from __future__ import annotations

import math

from finevidence.contracts.benchmark import MiniCase
from finevidence.evidence.coverage import coverage_for_case


def _eligible_rankings(cases: list[MiniCase], rankings: dict[str, list[str]]) -> list[tuple[MiniCase, list[str]]]:
    return [
        (case, rankings[case.question_id])
        for case in cases
        if case.question_id in rankings and case.answerable and case.required_evidence
    ]


def hard_negative_error_rate(cases: list[MiniCase], rankings: dict[str, list[str]]) -> float | str:
    eligible = [
        (case, rankings[case.question_id])
        for case in cases
        if case.question_id in rankings and case.positive_evidence_id and case.hard_negative_ids
    ]
    if not eligible:
        return "N/A"
    errors = 0
    for case, ranking in eligible:
        positive_rank = ranking.index(case.positive_evidence_id) if case.positive_evidence_id in ranking else math.inf
        negative_rank = min((ranking.index(item) for item in case.hard_negative_ids if item in ranking), default=math.inf)
        if negative_rank < positive_rank:
            errors += 1
    return errors / len(eligible)


def evaluate_retrieval(cases: list[MiniCase], rankings: dict[str, list[str]], top_k: int = 5) -> dict[str, float | str]:
    eligible = _eligible_rankings(cases, rankings)
    if not eligible:
        return {"recall_at_5": "N/A", "mrr": "N/A", "ndcg_at_10": "N/A", "complete_evidence_rate": "N/A"}

    recall_values = []
    reciprocal_ranks = []
    ndcg_values = []
    complete_values = []
    for case, ranking in eligible:
        required = {ref.evidence_id for ref in case.required_evidence}
        top = ranking[:top_k]
        recall_values.append(len(required & set(top)) / len(required) if required else 0.0)
        ranks = [index + 1 for index, evidence_id in enumerate(ranking) if evidence_id in required]
        reciprocal_ranks.append(1.0 / min(ranks) if ranks else 0.0)
        gains = [1.0 if evidence_id in required else 0.0 for evidence_id in ranking[:10]]
        dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))
        ideal = sum(1.0 / math.log2(index + 2) for index in range(min(len(required), 10)))
        ndcg_values.append(dcg / ideal if ideal else 0.0)
        complete_values.append(coverage_for_case(case, set(top)).complete)

    return {
        "recall_at_5": sum(recall_values) / len(recall_values),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "ndcg_at_10": sum(ndcg_values) / len(ndcg_values),
        "complete_evidence_rate": sum(complete_values) / len(complete_values),
        "hard_negative_error_rate": hard_negative_error_rate(cases, rankings),
    }
