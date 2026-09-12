from __future__ import annotations

from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.retrieval.dense import DenseRetriever


class VisualRetriever:
    backend_name = "conditional_visual_adapter"

    def __init__(self, encoder: object | None = None) -> None:
        self.encoder = encoder
        self._visual: list[Evidence] = []
        self._dense = DenseRetriever()
        self.reason = "visual adapter or visual evidence unavailable"

    @property
    def available(self) -> bool:
        return self.encoder is not None and bool(self._visual)

    def fit(self, evidence: list[Evidence]) -> None:
        self._visual = [item for item in evidence if item.modality in {"image", "table"}]
        if self.available:
            self._dense.fit(self._visual)

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        if not self.available:
            return []
        return self._dense.search(query, top_k)
