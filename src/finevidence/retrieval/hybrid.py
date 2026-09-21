from __future__ import annotations

import math

from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.retrieval.dense import DenseRetriever
from finevidence.retrieval.fusion import reciprocal_rank_fusion
from finevidence.retrieval.lexical import BM25Retriever


def _normalise(items: list[RetrievedEvidence]) -> dict[str, float]:
    if not items:
        return {}
    values = [float(item.retrieval_score) for item in items]
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return {item.evidence_id: 1.0 for item in items}
    return {
        item.evidence_id: (float(item.retrieval_score) - lo) / (hi - lo)
        for item in items
    }


class HybridRetriever:
    """Dense + BM25 retrieval.

    New callers use reciprocal-rank fusion by default. The historical alpha
    argument remains supported for reproducibility of older FinEvidence
    experiments and switches to normalized weighted fusion.
    """

    backend_name = "dense_bm25_rrf"

    def __init__(
        self,
        alpha: float | None = None,
        *,
        rrf_k: int = 60,
        candidate_multiplier: int = 4,
    ) -> None:
        if alpha is not None and not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        if rrf_k <= 0:
            raise ValueError("rrf_k must be positive")
        if candidate_multiplier <= 0:
            raise ValueError("candidate_multiplier must be positive")
        self.alpha = alpha
        self.rrf_k = rrf_k
        self.candidate_multiplier = candidate_multiplier
        self._dense = DenseRetriever()
        self._bm25 = BM25Retriever()
        self._evidence: list[Evidence] = []

    def fit(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)
        self._dense.fit(self._evidence)
        self._bm25.fit(self._evidence)

    def _weighted(
        self,
        dense: list[RetrievedEvidence],
        lexical: list[RetrievedEvidence],
        top_k: int,
    ) -> list[RetrievedEvidence]:
        dense_scores = _normalise(dense)
        lexical_scores = _normalise(lexical)
        ids = set(dense_scores) | set(lexical_scores)
        alpha = 0.7 if self.alpha is None else self.alpha
        scored = {
            evidence_id: alpha * dense_scores.get(evidence_id, 0.0)
            + (1.0 - alpha) * lexical_scores.get(evidence_id, 0.0)
            for evidence_id in ids
        }
        return [
            RetrievedEvidence(
                evidence_id=evidence_id,
                rank=rank,
                retrieval_score=float(score),
                rerank_score=float(score),
            )
            for rank, (evidence_id, score) in enumerate(
                sorted(scored.items(), key=lambda item: (-item[1], item[0]))[:top_k],
                start=1,
            )
        ]

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        if top_k <= 0 or not self._evidence:
            return []
        candidate_k = min(
            len(self._evidence),
            max(top_k, top_k * self.candidate_multiplier),
        )
        dense = self._dense.search(query, candidate_k)
        lexical = self._bm25.search(query, candidate_k)
        if self.alpha is not None:
            return self._weighted(dense, lexical, top_k)
        return reciprocal_rank_fusion(
            [dense, lexical],
            k=self.rrf_k,
            top_k=top_k,
            expose_as_rerank_score=True,
        )
