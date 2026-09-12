from finevidence.contracts.benchmark import MiniCase, RequiredEvidenceRef
from finevidence.evidence.coverage import fact_coverage_for_case
from finevidence.eval.metrics import (
    complete_evidence_rates,
    evaluate_retrieval,
    false_answer_eligibility_rate,
    hard_negative_error_rate,
    hard_negative_error_rate_by_category,
)


def _case(**kwargs):
    values = dict(
        question_id="q-1",
        question="Which evidence is required?",
        gold_answer="answer",
        required_evidence=[RequiredEvidenceRef(evidence_id="e-1"), RequiredEvidenceRef(evidence_id="e-2")],
        required_facts=["f1", "f2"],
        failure_type="MULTI_EVIDENCE",
        answerable=True,
    )
    values.update(kwargs)
    return MiniCase(**values)


def test_partial_evidence_is_not_complete():
    result = fact_coverage_for_case(
        _case(
            required_facts=[
                {"fact_id": "F1", "description": "first", "acceptable_evidence_ids": ["e-1"]},
                {"fact_id": "F2", "description": "second", "acceptable_evidence_ids": ["e-2"]},
            ]
        ),
        {"e-1"},
    )

    assert result.covered_fact_count == 1
    assert result.fact_coverage == 0.5
    assert result.complete is False
    assert result.missing_facts[0].fact_id == "F2"


def test_all_required_evidence_is_complete():
    result = fact_coverage_for_case(
        _case(
            required_facts=[
                {"fact_id": "F1", "description": "first", "acceptable_evidence_ids": ["e-1"]},
                {"fact_id": "F2", "description": "second", "acceptable_evidence_ids": ["e-2"]},
            ]
        ),
        {"e-1", "e-2", "extra"},
    )

    assert result.complete is True
    assert result.covered_fact_count == 2


def test_hard_negative_error_rate_counts_negative_above_positive():
    cases = [
        _case(
            question_id="q-hn",
            required_evidence=[RequiredEvidenceRef(evidence_id="positive")],
            positive_evidence_id="positive",
            hard_negative_ids=["negative-2023"],
            failure_type="HARD_NEGATIVE",
        )
    ]

    assert hard_negative_error_rate(cases, {"q-hn": ["negative-2023", "positive"]}) == 1.0


def test_hard_negative_metric_is_na_without_annotated_cases():
    assert hard_negative_error_rate([_case()], {"q-1": ["e-1"]}) == "N/A"


def test_hard_negative_error_rate_is_available_per_category():
    temporal = _case(
        question_id="q-temporal",
        required_evidence=[RequiredEvidenceRef(evidence_id="positive")],
        positive_evidence_id="positive",
        hard_negative_ids=["negative"],
        failure_type="HARD_NEGATIVE_TEMPORAL",
    )
    metric = _case(
        question_id="q-metric",
        required_evidence=[RequiredEvidenceRef(evidence_id="positive")],
        positive_evidence_id="positive",
        hard_negative_ids=["negative"],
        failure_type="HARD_NEGATIVE_METRIC",
    )

    assert hard_negative_error_rate_by_category(
        [temporal, metric],
        {"q-temporal": ["negative", "positive"], "q-metric": ["positive", "negative"]},
    ) == {"TEMPORAL": 1.0, "METRIC": 0.0}


def test_retrieval_metrics_exclude_unanswerable_cases_without_gold_evidence():
    unknown = MiniCase(
        question_id="q-unknown",
        question="Unknown?",
        gold_answer=None,
        required_evidence=[],
        failure_type="INSUFFICIENT_EVIDENCE",
        answerable=False,
    )

    metrics = evaluate_retrieval(
        [_case(), unknown],
        {"q-1": ["e-1", "e-2"], "q-unknown": []},
    )

    assert metrics["recall_at_5"] == 1.0
    assert metrics["complete_evidence_rate"] == 1.0


def test_complete_evidence_rates_distinguish_initial_and_recovered_facts():
    case = _case(
        required_facts=[
            {"fact_id": "F1", "description": "first", "acceptable_evidence_ids": ["e-1"]},
            {"fact_id": "F2", "description": "second", "acceptable_evidence_ids": ["e-2"]},
        ]
    )

    metrics = complete_evidence_rates(
        [case],
        {"q-1": {"e-1"}},
        {"q-1": {"e-1", "e-2"}},
    )

    assert metrics == {
        "initial_complete_evidence_rate": 0.0,
        "final_complete_evidence_rate": 1.0,
        "partial_to_complete_recovery_rate": 1.0,
    }


def test_false_answer_eligibility_rate_counts_partial_case_allowed_to_generate():
    case = _case(
        required_facts=[
            {"fact_id": "F1", "description": "first", "acceptable_evidence_ids": ["e-1"]},
            {"fact_id": "F2", "description": "second", "acceptable_evidence_ids": ["e-2"]},
        ]
    )

    assert false_answer_eligibility_rate([case], {"q-1": {"e-1"}}, {"q-1": True}) == 1.0
    assert false_answer_eligibility_rate([case], {"q-1": {"e-1"}}, {"q-1": False}) == 0.0
