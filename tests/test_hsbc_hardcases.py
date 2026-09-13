import pytest

from finevidence.contracts.evidence import Evidence
from finevidence.eval.p0_h_hsbc import build_hsbc_hard_case


def _evidence(evidence_id, text, *, period=None, entity=None, metric=None):
    return Evidence.from_content(document_id="D1", source_uri="https://www.hsbc.com/x.pdf", page=1, block_id=evidence_id, modality="text", text=text, evidence_id=evidence_id, period=period, entity=entity, metric=metric)


def test_hard_case_requires_positive_negative_and_facet_conflict():
    positive = _evidence("E1", "HSBC Holdings CET1 ratio FY2025 was 14.9%", period="2025", entity="HSBC Holdings", metric="CET1 ratio")
    negative = _evidence("E2", "HSBC Holdings CET1 ratio FY2024 was 14.8%", period="2024", entity="HSBC Holdings", metric="CET1 ratio")
    case = build_hsbc_hard_case("HSBC Holdings FY2025 CET1 ratio", positive, [negative], category="TEMPORAL")
    assert case.positive_evidence_id == "E1"
    assert case.hard_negative_ids == ["E2"]
    assert case.verification_pass_a == "PASS"
    assert case.verification_pass_b == "PASS"
    assert case.adjudication_status == "KEEP"


def test_hard_case_rejects_candidate_without_facet_conflict():
    positive = _evidence("E1", "HSBC Holdings CET1 ratio FY2025 was 14.9%", period="2025", entity="HSBC Holdings", metric="CET1 ratio")
    with pytest.raises(ValueError, match="facet"):
        build_hsbc_hard_case("HSBC Holdings FY2025 CET1 ratio", positive, [_evidence("E2", "HSBC Holdings CET1 ratio FY2025 was 14.8%", period="2025", entity="HSBC Holdings", metric="CET1 ratio")], category="TEMPORAL")
