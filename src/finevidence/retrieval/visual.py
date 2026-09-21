from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from finevidence.contracts.evidence import Evidence, RetrievedEvidence


class ClipImageEncoder:
    """Real image/text encoder adapter; imports OpenAI CLIP only when selected."""

    model_name = "openai-clip-RN50"

    def __init__(self, model_path: str | None = None, device: str = "cpu") -> None:
        import clip
        import torch

        self.device = device
        self.model, self.preprocess = clip.load(
            "RN50",
            device=device,
            download_root=model_path or "artifacts/models",
        )
        self.model.eval()
        self._clip = clip
        self._torch = torch

    def encode_images(self, paths: list[str]) -> object:
        from PIL import Image

        with self._torch.no_grad():
            batch = self._torch.stack(
                [self.preprocess(Image.open(path).convert("RGB")) for path in paths]
            ).to(self.device)
            vectors = self.model.encode_image(batch).float()
            return vectors / vectors.norm(dim=-1, keepdim=True).clamp_min(1e-12)

    def encode_text(self, texts: list[str]) -> object:
        with self._torch.no_grad():
            vectors = self.model.encode_text(
                self._clip.tokenize(texts).to(self.device)
            ).float()
            return vectors / vectors.norm(dim=-1, keepdim=True).clamp_min(1e-12)

    def manifest(self) -> dict:
        state = self.model.state_dict()
        digest = hashlib.sha256()
        for key in sorted(state):
            digest.update(key.encode())
            digest.update(state[key].detach().cpu().numpy().tobytes())
        return {
            "model_name": self.model_name,
            "model_revision": "openai-public-RN50",
            "runtime": "openai-clip",
            "device": self.device,
            "image_encoder": True,
            "weights_sha256": digest.hexdigest(),
            "status": "READY",
        }


class VisualRetriever:
    backend_name = "real_image_encoder_visual_retriever"

    def __init__(self, encoder: object | None = None) -> None:
        self.encoder = encoder
        self._visual: list[Evidence] = []
        self._vectors = None
        self.reason = "visual adapter or visual evidence unavailable"

    @property
    def available(self) -> bool:
        return (
            self.encoder is not None
            and bool(self._visual)
            and self._vectors is not None
        )

    def fit(self, evidence: list[Evidence]) -> None:
        self._visual = [
            item for item in evidence if item.image_path and Path(item.image_path).exists()
        ]
        if not self._visual or self.encoder is None:
            return
        self._vectors = self.encoder.encode_images(
            [item.image_path for item in self._visual]
        )

    @staticmethod
    def _scores_to_list(scores: object) -> list[float]:
        # Accept torch tensors for the real CLIP adapter and NumPy arrays for
        # lightweight deterministic tests/adapters.
        if hasattr(scores, "detach"):
            return [float(value) for value in scores.detach().cpu().tolist()]
        return [float(value) for value in np.asarray(scores).tolist()]

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        if not self.available:
            return []
        query_vector = self.encoder.encode_text([query])[0]
        scores = self._vectors @ query_vector
        values = self._scores_to_list(scores)
        order = sorted(
            range(len(self._visual)),
            key=lambda i: (-values[i], self._visual[i].evidence_id),
        )
        return [
            RetrievedEvidence(
                evidence_id=self._visual[index].evidence_id,
                rank=rank,
                retrieval_score=values[index],
            )
            for rank, index in enumerate(order[:top_k], start=1)
        ]
