from __future__ import annotations

import hashlib
from pathlib import Path

from finevidence.contracts.b5 import ModelManifest
from finevidence.contracts.evidence import Evidence, RetrievedEvidence


class QwenEmbeddingRetriever:
    """Optional real Qwen3 text embedding adapter; no heuristic fallback."""

    def __init__(self, model_id: str = "Qwen/Qwen3-Embedding-0.6B", revision: str | None = None, device: str = "cpu", cache_dir: str | None = None, local_files_only: bool = True) -> None:
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.cache_dir = cache_dir
        self.local_files_only = local_files_only
        self.model = None
        self.tokenizer = None
        self._torch = None
        self._evidence: list[Evidence] = []
        self._vectors = None
        self.error: str | None = None
        self._load()

    def _load(self) -> None:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            kwargs = {"revision": self.revision, "cache_dir": self.cache_dir, "local_files_only": self.local_files_only}
            kwargs = {key: value for key, value in kwargs.items() if value is not None}
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, **kwargs)
            self.model = AutoModel.from_pretrained(self.model_id, **kwargs).to(self.device).eval()
            self._torch = torch
        except Exception as exc:  # optional adapter boundary: caller receives auditable N/A
            self.error = f"{type(exc).__name__}: {exc}"

    @property
    def available(self) -> bool:
        return self.model is not None and self.tokenizer is not None and self._torch is not None

    def manifest(self) -> ModelManifest:
        weights_hash = None
        if self.available:
            digest = hashlib.sha256()
            for key, value in sorted(self.model.state_dict().items()):
                digest.update(key.encode())
                digest.update(value.detach().cpu().numpy().tobytes())
            weights_hash = digest.hexdigest()
        return ModelManifest(
            model_name=self.model_id,
            model_revision=self.revision,
            runtime="transformers",
            device=self.device,
            status="READY" if self.available else "N/A",
            weights_sha256=weights_hash,
            error=None if self.available else self.error,
        )

    def _encode(self, texts: list[str]):
        assert self.available
        inputs = self.tokenizer(texts, padding=True, truncation=True, max_length=8192, return_tensors="pt").to(self.device)
        with self._torch.no_grad():
            output = self.model(**inputs).last_hidden_state
        mask = inputs["attention_mask"].bool()
        positions = mask.sum(dim=1) - 1
        vectors = output[self._torch.arange(output.shape[0], device=output.device), positions]
        return vectors / vectors.norm(dim=-1, keepdim=True).clamp_min(1e-12)

    def fit(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)
        if self.available and self._evidence:
            self._vectors = self._encode([item.text for item in self._evidence])

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        if not self.available or self._vectors is None:
            return []
        query_vector = self._encode([query])[0]
        scores = (self._vectors @ query_vector).detach().cpu().tolist()
        order = sorted(range(len(self._evidence)), key=lambda index: (-float(scores[index]), self._evidence[index].evidence_id))
        return [RetrievedEvidence(evidence_id=self._evidence[index].evidence_id, rank=rank, retrieval_score=float(scores[index])) for rank, index in enumerate(order[:top_k], start=1)]


def local_model_artifact(model_id: str) -> Path | None:
    """Return a cache hint only; existence does not imply runnable weights."""
    safe = model_id.replace("/", "--")
    candidates = [Path.home() / ".cache" / "huggingface" / "hub" / f"models--{safe}", Path("artifacts/models") / safe]
    return next((path for path in candidates if path.exists()), None)
