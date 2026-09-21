from __future__ import annotations

from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.retrieval.dense import DenseRetriever
from finevidence.retrieval.fusion import reciprocal_rank_fusion
from finevidence.retrieval.lexical import BM25Retriever


class HybridRetriever:
    """Dense + BM25 retrieval fused with reciprocal-rank fusion."""

    backend_name = "dense_bm25_rrf"

    def __init__(self, *, rrf_k: int = 60, candidate_multiplier: int = 4) -> None:
        if rrf_k <= 0:
            raise ValueError("rrf_k must be positive")
        if candidate_multiplier <= 0:
            raise ValueError("candidate_multiplier must be positive")
        self.rrf_k = rrf_k
        self.candidate_multiplier = candidate_multiplier
        self._dense = DenseRetriever()
        self._bm25 = BM25Retriever()
        self._evidence: list[Evidence] = []

    def fit(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)
        self._dense.fit(self._evidence)
        self._bm25.fit(self._evidence)

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        if top_k <= 0 or not self._evidence:
            return []
        candidate_k = min(
            len(self._evidence),
            max(top_k, top_k * self.candidate_multiplier),
        )
        dense = self._dense.search(query, candidate_k)
        lexical = self._bm25.search(query, candidate_k)
        return reciprocal_rank_fusion(
            [dense, lexical],
            k=self.rrf_k,
            top_k=top_k,
            expose_as_rerank_score=True,
        )
