from __future__ import annotations

from typing import Protocol

from finevidence.contracts.benchmark import MiniCase
from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.ranking.facets import evidence_facets, facet_features


def _ranked(candidates, scores, top_k):
    ordered = sorted(
        zip(candidates, scores),
        key=lambda pair: (-pair[1], pair[0].evidence_id),
    )[:top_k]
    return [
        item.model_copy(update={"rank": rank, "rerank_score": float(score)})
        for rank, (item, score) in enumerate(ordered, start=1)
    ]


class FacetAwareReranker:
    backend_name = "deterministic_financial_facet_reranker"

    def rank(
        self,
        query: str,
        candidates: list[RetrievedEvidence],
        evidence_by_id: dict[str, Evidence],
        top_k: int = 5,
    ):
        scores = [
            max(item.retrieval_score, 0.0) * 0.1
            + sum(facet_features(query, evidence_by_id[item.evidence_id]))
            for item in candidates
        ]
        return _ranked(candidates, scores, top_k)


class HardNegativeAwareReranker:
    backend_name = "deterministic_hard_negative_financial_reranker"

    def __init__(self) -> None:
        self.weights: list[float] = [0.1] + [1.0] * 8

    def fit(self, cases: list[MiniCase], evidence_by_id: dict[str, Evidence]):
        # Deterministic pairwise updates; replace with learned ranking only if the
        # controlled hard-negative suite shows this ceiling is insufficient.
        for case in cases:
            positive_id = case.positive_evidence_id
            if not positive_id or positive_id not in evidence_by_id:
                continue
            positive = (
                max(0.0, 1.0),
                *facet_features(case.question, evidence_by_id[positive_id]),
            )
            for negative_id in case.hard_negative_ids:
                if negative_id not in evidence_by_id:
                    continue
                negative = (
                    0.0,
                    *facet_features(case.question, evidence_by_id[negative_id]),
                )
                difference = [
                    left - right for left, right in zip(positive, negative)
                ]
                if sum(
                    weight * value
                    for weight, value in zip(self.weights, difference)
                ) <= 0:
                    self.weights = [
                        weight + value
                        for weight, value in zip(self.weights, difference)
                    ]
        return self

    def rank(
        self,
        query: str,
        candidates: list[RetrievedEvidence],
        evidence_by_id: dict[str, Evidence],
        top_k: int = 5,
    ):
        scores = [
            self.weights[0] * max(item.retrieval_score, 0.0)
            + sum(
                weight * value
                for weight, value in zip(
                    self.weights[1:],
                    facet_features(query, evidence_by_id[item.evidence_id]),
                )
            )
            for item in candidates
        ]
        return _ranked(candidates, scores, top_k)


class PairScorer(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        ...


class SentenceTransformerCrossEncoder:
    """Lazy optional adapter for a real Cross-Encoder reranker.

    The dependency and model weights are intentionally optional so the core
    repository and CI remain deterministic and offline-friendly.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        *,
        device: str | None = None,
    ) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError(
                "Install FinEvidence with the 'neural-rerank' extra to use "
                "SentenceTransformerCrossEncoder."
            ) from exc
        kwargs = {}
        if device is not None:
            kwargs["device"] = device
        self.model = CrossEncoder(model_name, **kwargs)
        self.model_name = model_name

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        scores = self.model.predict(pairs)
        return [float(value) for value in scores]


class CrossEncoderReranker:
    backend_name = "cross_encoder"

    def __init__(self, scorer: PairScorer) -> None:
        self.scorer = scorer

    def rank(
        self,
        query: str,
        candidates: list[RetrievedEvidence],
        evidence_by_id: dict[str, Evidence],
        top_k: int = 5,
    ) -> list[RetrievedEvidence]:
        pairs = [
            (query, evidence_by_id[item.evidence_id].text)
            for item in candidates
        ]
        return _ranked(candidates, self.scorer.predict(pairs), top_k)


class FinanceAwareMultiObjectiveReranker:
    """Cross-Encoder relevance + financial scope + provenance + coverage novelty."""

    backend_name = "finance_aware_multi_objective"

    _SOURCE_AUTHORITY = {
        "regulatory_filing": 1.00,
        "annual_report": 0.95,
        "official_disclosure": 0.90,
        "investor_presentation": 0.80,
        "approved_internal": 0.80,
        "third_party": 0.50,
    }

    def __init__(
        self,
        scorer: PairScorer | None = None,
        *,
        relevance_weight: float = 0.55,
        facet_weight: float = 0.25,
        provenance_weight: float = 0.10,
        coverage_weight: float = 0.10,
    ) -> None:
        self.scorer = scorer
        self.relevance_weight = relevance_weight
        self.facet_weight = facet_weight
        self.provenance_weight = provenance_weight
        self.coverage_weight = coverage_weight

    @staticmethod
    def _coverage_key(evidence: Evidence) -> tuple[str | None, ...]:
        facets = evidence_facets(evidence)
        return (
            facets.metric,
            facets.period,
            facets.basis,
            facets.segment,
            facets.geography,
        )

    def _base_scores(
        self,
        query: str,
        candidates: list[RetrievedEvidence],
        evidence_by_id: dict[str, Evidence],
    ) -> list[float]:
        if self.scorer is not None:
            relevance = self.scorer.predict(
                [
                    (query, evidence_by_id[item.evidence_id].text)
                    for item in candidates
                ]
            )
        else:
            relevance = [max(item.retrieval_score, 0.0) for item in candidates]

        scores: list[float] = []
        for item, neural_score in zip(candidates, relevance):
            evidence = evidence_by_id[item.evidence_id]
            facet_values = facet_features(query, evidence)
            facet_score = sum(facet_values) / len(facet_values)
            source_score = self._SOURCE_AUTHORITY.get(
                (evidence.source_type or "").lower(),
                0.60,
            )
            scores.append(
                self.relevance_weight * float(neural_score)
                + self.facet_weight * facet_score
                + self.provenance_weight * source_score
            )
        return scores

    def rank(
        self,
        query: str,
        candidates: list[RetrievedEvidence],
        evidence_by_id: dict[str, Evidence],
        top_k: int = 5,
    ) -> list[RetrievedEvidence]:
        if not candidates or top_k <= 0:
            return []

        base_scores = self._base_scores(query, candidates, evidence_by_id)
        remaining = list(zip(candidates, base_scores))
        selected: list[tuple[RetrievedEvidence, float]] = []
        seen_keys: set[tuple[str | None, ...]] = set()

        while remaining and len(selected) < top_k:
            rescored: list[tuple[float, RetrievedEvidence, float]] = []
            for item, base in remaining:
                key = self._coverage_key(evidence_by_id[item.evidence_id])
                informative = any(value is not None for value in key)
                coverage_gain = 1.0 if informative and key not in seen_keys else 0.0
                total = base + self.coverage_weight * coverage_gain
                rescored.append((total, item, base))
            total, winner, base = max(
                rescored,
                key=lambda row: (row[0], row[1].evidence_id),
            )
            selected.append((winner, total))
            seen_keys.add(self._coverage_key(evidence_by_id[winner.evidence_id]))
            remaining = [
                pair for pair in remaining if pair[0].evidence_id != winner.evidence_id
            ]

        return [
            item.model_copy(update={"rank": rank, "rerank_score": float(score)})
            for rank, (item, score) in enumerate(selected, start=1)
        ]
