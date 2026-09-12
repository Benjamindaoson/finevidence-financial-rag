from __future__ import annotations

from dataclasses import dataclass

from finevidence.contracts.benchmark import MiniCase


@dataclass(frozen=True)
class CoverageResult:
    required_count: int
    covered_count: int
    complete: bool
    missing_evidence_ids: list[str]


def coverage_for_case(case: MiniCase, selected_ids: set[str]) -> CoverageResult:
    required = [ref.evidence_id for ref in case.required_evidence]
    missing = [evidence_id for evidence_id in required if evidence_id not in selected_ids]
    return CoverageResult(
        required_count=len(required),
        covered_count=len(required) - len(missing),
        complete=bool(required) and not missing,
        missing_evidence_ids=missing,
    )
