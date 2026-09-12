from __future__ import annotations

from dataclasses import dataclass

from finevidence.contracts.benchmark import MiniCase
from finevidence.contracts.evidence import RetrievedEvidence
from finevidence.evidence.coverage import FactCoverageResult, fact_coverage_for_case


@dataclass(frozen=True)
class RetrievalRound:
    round_number: int
    query: str
    retrieved_ids: list[str]
    covered_facts: list[str]
    missing_facts: list[str]


@dataclass(frozen=True)
class TargetedRetrievalResult:
    initial: FactCoverageResult
    final: FactCoverageResult
    selected_ids: set[str]
    rounds: list[RetrievalRound]


class TargetedRetriever:
    """Bounded missing-fact retrieval; it deliberately has no agent loop."""

    def __init__(self, retriever) -> None:
        self.retriever = retriever

    def retrieve(
        self,
        case: MiniCase,
        original_query: str,
        top_k: int,
        max_rounds: int = 2,
        initial_top_k: int | None = None,
    ) -> TargetedRetrievalResult:
        selected: set[str] = set()
        rounds: list[RetrievalRound] = []
        query = original_query
        initial: FactCoverageResult | None = None
        current: FactCoverageResult | None = None
        for round_number in range(max_rounds + 1):
            search_k = initial_top_k if round_number == 0 and initial_top_k is not None else top_k
            results: list[RetrievedEvidence] = self.retriever.search(query, search_k)
            selected.update(item.evidence_id for item in results)
            current = fact_coverage_for_case(case, selected)
            if initial is None:
                initial = current
            rounds.append(
                RetrievalRound(
                    round_number=round_number,
                    query=query,
                    retrieved_ids=[item.evidence_id for item in results],
                    covered_facts=[fact.fact_id for fact in current.covered_facts],
                    missing_facts=[fact.fact_id for fact in current.missing_facts],
                )
            )
            if current.complete or round_number >= max_rounds:
                break
            missing = current.missing_facts[0]
            query = f"{original_query} Evidence needed: {missing.description}"
        assert initial is not None and current is not None
        return TargetedRetrievalResult(initial=initial, final=current, selected_ids=selected, rounds=rounds)
