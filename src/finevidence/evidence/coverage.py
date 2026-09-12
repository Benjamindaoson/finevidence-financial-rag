from __future__ import annotations

from dataclasses import dataclass

from finevidence.contracts.benchmark import FactRequirement, MiniCase


@dataclass(frozen=True)
class CoverageResult:
    required_count: int
    covered_count: int
    complete: bool
    missing_evidence_ids: list[str]


@dataclass(frozen=True)
class FactCoverageResult:
    required_fact_count: int
    covered_fact_count: int
    fact_coverage: float
    complete: bool
    covered_facts: list[FactRequirement]
    missing_facts: list[FactRequirement]


def _fact_requirements(case: MiniCase) -> list[FactRequirement]:
    refs = [ref.evidence_id for ref in case.required_evidence]
    facts: list[FactRequirement] = []
    for index, fact in enumerate(case.required_facts):
        if isinstance(fact, FactRequirement):
            facts.append(fact)
            continue
        acceptable = [refs[index]] if index < len(refs) else refs
        if acceptable:
            facts.append(FactRequirement(fact_id=f"legacy-{index + 1}", description=fact, acceptable_evidence_ids=acceptable))
    return facts


def fact_coverage_for_case(case: MiniCase, selected_ids: set[str]) -> FactCoverageResult:
    facts = _fact_requirements(case)
    covered = [fact for fact in facts if set(fact.acceptable_evidence_ids) & selected_ids]
    missing = [fact for fact in facts if fact not in covered]
    total = len(facts)
    return FactCoverageResult(
        required_fact_count=total,
        covered_fact_count=len(covered),
        fact_coverage=(len(covered) / total if total else 0.0),
        complete=bool(total) and len(covered) == total,
        covered_facts=covered,
        missing_facts=missing,
    )


def coverage_for_case(case: MiniCase, selected_ids: set[str]) -> CoverageResult:
    required = [ref.evidence_id for ref in case.required_evidence]
    missing = [evidence_id for evidence_id in required if evidence_id not in selected_ids]
    return CoverageResult(
        required_count=len(required),
        covered_count=len(required) - len(missing),
        complete=bool(required) and not missing,
        missing_evidence_ids=missing,
    )
