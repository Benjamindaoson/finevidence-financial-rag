from __future__ import annotations

import re

from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.retrieval.dense import DenseRetriever


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", text)}


class HybridRetriever:
    backend_name = "dense_plus_lexical_generic_reranker"

    def __init__(self, alpha: float = 0.7) -> None:
        self.alpha = alpha
        self._dense = DenseRetriever()
        self._evidence: list[Evidence] = []

    def fit(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)
        self._dense.fit(self._evidence)

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        dense = {item.evidence_id: item for item in self._dense.search(query, len(self._evidence))}
        query_tokens = _tokens(query)
        scored: list[tuple[float, float, Evidence]] = []
        for item in self._evidence:
            lexical = len(query_tokens & _tokens(item.text)) / max(len(query_tokens), 1)
            dense_score = max(float(dense[item.evidence_id].retrieval_score), 0.0)
            fused = self.alpha * dense_score + (1 - self.alpha) * lexical
            rerank = 0.75 * fused + 0.25 * lexical
            scored.append((rerank, fused, item))
        scored.sort(key=lambda row: (-row[0], -row[1], row[2].evidence_id))
        return [
            RetrievedEvidence(
                evidence_id=item.evidence_id,
                rank=rank,
                retrieval_score=float(fused),
                rerank_score=float(rerank),
            )
            for rank, (rerank, fused, item) in enumerate(scored[:top_k], start=1)
        ]
