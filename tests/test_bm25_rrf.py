from finevidence.contracts.evidence import Evidence
from finevidence.retrieval import BM25Retriever, HybridRetriever


def _items():
    return [
        Evidence.from_content(
            "d1", "fixture://d1", 1, "b1", "text",
            "CET1 ratio was 14.2 percent in FY2025."
        ),
        Evidence.from_content(
            "d2", "fixture://d2", 1, "b1", "text",
            "Management discussed capital strength and profitability."
        ),
        Evidence.from_content(
            "d3", "fixture://d3", 1, "b1", "text",
            "Revenue increased during the period."
        ),
    ]


def test_bm25_prefers_exact_financial_term_match():
    retriever = BM25Retriever()
    retriever.fit(_items())

    result = retriever.search("CET1 FY2025", top_k=2)

    assert result[0].evidence_id == "d1:p1:b1"


def test_hybrid_exposes_rrf_score_and_identity():
    retriever = HybridRetriever()
    retriever.fit(_items())

    result = retriever.search("CET1 FY2025", top_k=2)

    assert result[0].evidence_id == "d1:p1:b1"
    assert all(item.rerank_score is not None for item in result)
