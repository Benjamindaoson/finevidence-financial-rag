from __future__ import annotations

from finevidence.contracts.benchmark import MiniCase
from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.ranking.facets import facet_features


def _ranked(candidates, scores, top_k):
    ordered = sorted(zip(candidates, scores), key=lambda pair: (-pair[1], pair[0].evidence_id))[:top_k]
    return [
        item.model_copy(update={"rank": rank, "rerank_score": float(score)})
        for rank, (item, score) in enumerate(ordered, start=1)
    ]


class FacetAwareReranker:
    backend_name = "deterministic_financial_facet_reranker"

    def rank(self, query: str, candidates: list[RetrievedEvidence], evidence_by_id: dict[str, Evidence], top_k: int = 5):
        scores = [
            max(item.retrieval_score, 0.0) * 0.1 + sum(facet_features(query, evidence_by_id[item.evidence_id]))
            for item in candidates
        ]
        return _ranked(candidates, scores, top_k)


class HardNegativeAwareReranker:
    backend_name = "deterministic_hard_negative_financial_reranker"

    def __init__(self) -> None:
        self.weights: list[float] = [0.1] + [1.0] * 8

    def fit(self, cases: list[MiniCase], evidence_by_id: dict[str, Evidence]):
        # ponytail: deterministic pairwise updates; replace with learned ranking only if the
        # controlled hard-negative suite shows this ceiling is insufficient.
        for case in cases:
            positive_id = case.positive_evidence_id
            if not positive_id or positive_id not in evidence_by_id:
                continue
            positive = (max(0.0, 1.0), *facet_features(case.question, evidence_by_id[positive_id]))
            for negative_id in case.hard_negative_ids:
                if negative_id not in evidence_by_id:
                    continue
                negative = (0.0, *facet_features(case.question, evidence_by_id[negative_id]))
                difference = [left - right for left, right in zip(positive, negative)]
                if sum(weight * value for weight, value in zip(self.weights, difference)) <= 0:
                    self.weights = [weight + value for weight, value in zip(self.weights, difference)]
        return self

    def rank(self, query: str, candidates: list[RetrievedEvidence], evidence_by_id: dict[str, Evidence], top_k: int = 5):
        scores = [
            self.weights[0] * max(item.retrieval_score, 0.0)
            + sum(weight * value for weight, value in zip(self.weights[1:], facet_features(query, evidence_by_id[item.evidence_id])))
            for item in candidates
        ]
        return _ranked(candidates, scores, top_k)
