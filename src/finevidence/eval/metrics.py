from __future__ import annotations

import math
import re

from finevidence.contracts.benchmark import FactRequirement, MiniCase
from finevidence.ranking.facets import FinancialFacets
from finevidence.evidence.coverage import coverage_for_case, fact_coverage_for_case


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


def hard_negative_error_rate_by_category(
    cases: list[MiniCase], rankings: dict[str, list[str]]
) -> dict[str, float | str]:
    categories: dict[str, list[MiniCase]] = {}
    for case in cases:
        if case.positive_evidence_id and case.hard_negative_ids:
            category = case.failure_type.removeprefix("HARD_NEGATIVE_")
            categories.setdefault(category, []).append(case)
    return {
        category: hard_negative_error_rate(category_cases, rankings)
        for category, category_cases in sorted(categories.items())
    }


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


def complete_evidence_rates(
    cases: list[MiniCase],
    initial_selected: dict[str, set[str]],
    final_selected: dict[str, set[str]],
) -> dict[str, float | str]:
    eligible = [case for case in cases if case.answerable and case.required_facts]
    if not eligible:
        return {
            "initial_complete_evidence_rate": "N/A",
            "final_complete_evidence_rate": "N/A",
            "partial_to_complete_recovery_rate": "N/A",
        }
    initial_complete = [
        fact_coverage_for_case(case, initial_selected.get(case.question_id, set())).complete
        for case in eligible
    ]
    final_complete = [
        fact_coverage_for_case(case, final_selected.get(case.question_id, set())).complete
        for case in eligible
    ]
    partial_count = sum(not item for item in initial_complete)
    recovered = sum(
        not initial and final
        for initial, final in zip(initial_complete, final_complete)
    )
    return {
        "initial_complete_evidence_rate": sum(initial_complete) / len(eligible),
        "final_complete_evidence_rate": sum(final_complete) / len(eligible),
        "partial_to_complete_recovery_rate": recovered / partial_count if partial_count else "N/A",
    }


def false_answer_eligibility_rate(
    cases: list[MiniCase],
    selected_ids_by_case: dict[str, set[str]],
    eligibility_by_case: dict[str, bool],
) -> float | str:
    eligible_cases = [case for case in cases if case.answerable and case.required_facts]
    if not eligible_cases:
        return "N/A"
    false_eligible = sum(
        bool(eligibility_by_case.get(case.question_id, False))
        and not fact_coverage_for_case(case, selected_ids_by_case.get(case.question_id, set())).complete
        for case in eligible_cases
    )
    return false_eligible / len(eligible_cases)


def fact_decomposition_metrics(case: MiniCase, predicted_facts: list[FactRequirement]) -> dict[str, float]:
    gold_descriptions = [
        fact.description if isinstance(fact, FactRequirement) else fact
        for fact in case.required_facts
    ]
    gold_tokens = [set(re.findall(r"[a-z0-9]+", description.lower())) for description in gold_descriptions]
    predicted_tokens = [set(re.findall(r"[a-z0-9]+", fact.description.lower())) for fact in predicted_facts]
    matched = 0
    unused = set(range(len(gold_tokens)))
    for candidate in predicted_tokens:
        best = max(
            ((len(candidate & gold_tokens[index]) / max(len(candidate | gold_tokens[index]), 1), index) for index in unused),
            default=(0.0, -1),
        )
        if best[0] >= 0.5:
            matched += 1
            unused.remove(best[1])
    return {
        "required_fact_precision": matched / len(predicted_tokens) if predicted_tokens else 0.0,
        "required_fact_recall": matched / len(gold_tokens) if gold_tokens else 0.0,
    }


def facet_extraction_metrics(gold: dict[str, str | None], predicted: FinancialFacets) -> dict[str, float | str]:
    fields = ("entity", "metric", "period", "segment", "basis", "geography", "currency")
    result = {}
    for field in fields:
        expected = gold.get(field)
        if expected is None:
            result[f"{field}_accuracy"] = "N/A"
            continue
        actual = getattr(predicted, field)
        result[f"{field}_accuracy"] = float(bool(actual) and actual.lower() == expected.lower())
    return result
