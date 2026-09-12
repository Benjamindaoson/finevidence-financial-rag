from finevidence.contracts.evidence import Evidence
from finevidence.retrieval.dense import DenseRetriever
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.visual import VisualRetriever


def _evidence():
    return [
        Evidence.from_content("d1", "fixture://d1", 1, "b1", "text", "CET1 ratio in 2024 was 14.2 percent."),
        Evidence.from_content("d2", "fixture://d2", 1, "b1", "text", "Revenue increased to 100 million."),
        Evidence.from_content("d3", "fixture://d3", 1, "b1", "text", "The chart shows a declining cost of risk."),
    ]


def test_dense_results_are_traceable_and_deterministically_ranked():
    retriever = DenseRetriever()
    retriever.fit(_evidence())

    first = retriever.search("2024 CET1 ratio", top_k=2)
    second = retriever.search("2024 CET1 ratio", top_k=2)

    assert [item.evidence_id for item in first] == [item.evidence_id for item in second]
    assert first[0].evidence_id == "d1:p1:b1"
    assert first[0].rank == 1


def test_hybrid_results_keep_rerank_scores_and_evidence_identity():
    retriever = HybridRetriever()
    retriever.fit(_evidence())

    results = retriever.search("CET1 ratio 2024", top_k=2)

    assert results
    assert all(item.evidence_id for item in results)
    assert all(item.rerank_score is not None for item in results)


def test_visual_retriever_is_explicitly_unavailable_without_visual_adapter():
    retriever = VisualRetriever()
    retriever.fit(_evidence())

    assert retriever.available is False
    assert retriever.search("chart", top_k=3) == []
    assert retriever.reason == "visual adapter or visual evidence unavailable"
