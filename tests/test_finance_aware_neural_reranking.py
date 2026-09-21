from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.ranking import (
    CrossEncoderReranker,
    FinanceAwareMultiObjectiveReranker,
)


class FakeCrossEncoder:
    def predict(self, pairs):
        return [1.0 if "42.1" in passage else 0.2 for _, passage in pairs]


def _evidence():
    return {
        "reported": Evidence.from_content(
            "d",
            "fixture://d",
            1,
            "reported",
            "table",
            "HSBC Group FY2025 reported revenue was USD 42.1 billion.",
            evidence_id="reported",
            entity="HSBC Group",
            metric="revenue",
            period="2025",
            currency="USD",
            unit="billion",
            accounting_basis="reported",
            scope="Group",
            source_type="annual_report",
        ),
        "adjusted": Evidence.from_content(
            "d",
            "fixture://d",
            2,
            "adjusted",
            "table",
            "HSBC Group FY2025 adjusted revenue was USD 45.0 billion.",
            evidence_id="adjusted",
            entity="HSBC Group",
            metric="revenue",
            period="2025",
            currency="USD",
            unit="billion",
            accounting_basis="adjusted",
            scope="Group",
            source_type="investor_presentation",
        ),
    }


def test_cross_encoder_backend_is_adapter_driven():
    evidence = _evidence()
    candidates = [
        RetrievedEvidence(evidence_id="adjusted", rank=1, retrieval_score=0.9),
        RetrievedEvidence(evidence_id="reported", rank=2, retrieval_score=0.8),
    ]

    ranked = CrossEncoderReranker(FakeCrossEncoder()).rank(
        "HSBC Group 2025 reported revenue",
        candidates,
        evidence,
        top_k=2,
    )

    assert ranked[0].evidence_id == "reported"


def test_finance_aware_reranker_prefers_correct_basis_and_authoritative_source():
    evidence = _evidence()
    candidates = [
        RetrievedEvidence(evidence_id="adjusted", rank=1, retrieval_score=0.95),
        RetrievedEvidence(evidence_id="reported", rank=2, retrieval_score=0.80),
    ]

    ranked = FinanceAwareMultiObjectiveReranker(FakeCrossEncoder()).rank(
        "HSBC Group 2025 reported revenue",
        candidates,
        evidence,
        top_k=2,
    )

    assert ranked[0].evidence_id == "reported"
    assert ranked[0].rerank_score is not None
