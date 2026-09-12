from finevidence.contracts.benchmark import MiniCase, RequiredEvidenceRef
from finevidence.evidence.coverage import coverage_for_case
from finevidence.eval.metrics import evaluate_retrieval, hard_negative_error_rate


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
    result = coverage_for_case(_case(), {"e-1"})

    assert result.covered_count == 1
    assert result.complete is False
    assert result.missing_evidence_ids == ["e-2"]


def test_all_required_evidence_is_complete():
    result = coverage_for_case(_case(), {"e-1", "e-2", "extra"})

    assert result.complete is True
    assert result.covered_count == 2


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
