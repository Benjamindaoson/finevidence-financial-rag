from finevidence.contracts.benchmark import MiniCase
from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.ranking.facets import extract_facets
from finevidence.ranking.rerankers import FacetAwareReranker, HardNegativeAwareReranker


def _evidence():
    return {
        "positive": Evidence.from_content(
            "d", "fixture://d", 1, "positive", "table", "HSBC Group 2024 CET1 ratio was 14.2%.",
            evidence_id="positive", entity="HSBC Group", metric="CET1 ratio", period="2024",
        ),
        "negative": Evidence.from_content(
            "d", "fixture://d", 1, "negative", "table", "HSBC Group 2023 CET1 ratio was 13.7%.",
            evidence_id="negative", entity="HSBC Group", metric="CET1 ratio", period="2023",
        ),
    }


def test_extract_facets_from_financial_query():
    facets = extract_facets("What was HSBC Group 2024 CET1 ratio?")

    assert facets.entity == "HSBC Group"
    assert facets.metric == "CET1 ratio"
    assert facets.period == "2024"


def test_facet_aware_ranker_prefers_matching_period_and_metric():
    evidence = _evidence()
    candidates = [
        RetrievedEvidence(evidence_id="negative", rank=1, retrieval_score=0.99),
        RetrievedEvidence(evidence_id="positive", rank=2, retrieval_score=0.80),
    ]

    results = FacetAwareReranker().rank("What was HSBC Group 2024 CET1 ratio?", candidates, evidence, top_k=2)

    assert results[0].evidence_id == "positive"
    assert results[0].rerank_score is not None


def test_hard_negative_ranker_is_reproducible_and_prefers_declared_positive():
    evidence = _evidence()
    case = MiniCase(
        question_id="q-hn",
        question="What was HSBC Group 2024 CET1 ratio?",
        gold_answer="14.2%",
        required_evidence=[{"evidence_id": "positive"}],
        required_facts=["2024 CET1 ratio"],
        failure_type="HARD_NEGATIVE_TEMPORAL",
        answerable=True,
        positive_evidence_id="positive",
        hard_negative_ids=["negative"],
    )
    candidates = [
        RetrievedEvidence(evidence_id="negative", rank=1, retrieval_score=0.99),
        RetrievedEvidence(evidence_id="positive", rank=2, retrieval_score=0.80),
    ]

    first = HardNegativeAwareReranker().fit([case], evidence)
    second = HardNegativeAwareReranker().fit([case], evidence)
    first_results = first.rank(case.question, candidates, evidence, top_k=2)
    second_results = second.rank(case.question, candidates, evidence, top_k=2)

    assert first.weights == second.weights
    assert [item.evidence_id for item in first_results] == ["positive", "negative"]
