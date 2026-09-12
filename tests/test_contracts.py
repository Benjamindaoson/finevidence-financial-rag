import pytest

from finevidence.contracts.evidence import Evidence
from finevidence.contracts.benchmark import MiniCase, RequiredEvidenceRef


def test_evidence_from_content_is_traceable_and_hash_stable():
    evidence = Evidence.from_content(
        document_id="doc-1",
        source_uri="fixture://doc-1",
        page=3,
        block_id="b-7",
        modality="table",
        text="CET1 ratio: 14.2%",
        table_id="t-1",
        row_id="hsbc",
        column_id="2024",
    )

    assert evidence.evidence_id == "doc-1:p3:b-7"
    assert evidence.content_hash == Evidence.from_content(
        document_id="doc-1",
        source_uri="fixture://doc-1",
        page=3,
        block_id="b-7",
        modality="table",
        text="CET1 ratio: 14.2%",
        table_id="t-1",
        row_id="hsbc",
        column_id="2024",
    ).content_hash
    assert evidence.model_dump()["table_id"] == "t-1"


def test_evidence_rejects_a_supplied_hash_that_does_not_match():
    with pytest.raises(ValueError, match="content_hash"):
        Evidence.from_content(
            document_id="doc-1",
            source_uri="fixture://doc-1",
            page=1,
            block_id="b-1",
            modality="text",
            text="grounded fact",
            content_hash="not-the-content-hash",
        )


def test_answerable_case_requires_required_evidence():
    with pytest.raises(ValueError, match="required_evidence"):
        MiniCase(
            question_id="q-1",
            question="What is the answer?",
            gold_answer="42",
            failure_type="TEXT_FACTUAL",
            answerable=True,
            required_evidence=[],
        )


def test_unanswerable_case_can_have_no_required_evidence():
    case = MiniCase(
        question_id="q-unknown",
        question="Which unpublished number is in the corpus?",
        gold_answer=None,
        failure_type="INSUFFICIENT_EVIDENCE",
        answerable=False,
        required_evidence=[],
    )

    assert case.answerable is False
    assert RequiredEvidenceRef(evidence_id="e-1").evidence_id == "e-1"
