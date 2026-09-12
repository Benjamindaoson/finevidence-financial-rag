from finevidence.contracts.benchmark import MiniCase
from finevidence.contracts.evidence import RetrievedEvidence
from finevidence.retrieval.targeted import TargetedRetriever


class ScriptedRetriever:
    def __init__(self):
        self.queries = []

    def search(self, query, top_k):
        self.queries.append(query)
        if "management explanation" in query:
            return [RetrievedEvidence(evidence_id="e-management", rank=1, retrieval_score=0.9)]
        return [RetrievedEvidence(evidence_id="e-revenue", rank=1, retrieval_score=0.9)]


class NeverCompleteRetriever:
    def __init__(self):
        self.queries = []

    def search(self, query, top_k):
        self.queries.append(query)
        return [RetrievedEvidence(evidence_id="e-revenue", rank=1, retrieval_score=0.9)]


def _case():
    return MiniCase(
        question_id="q-targeted",
        question="What is revenue and why did it change?",
        gold_answer="answer",
        required_evidence=[
            {"evidence_id": "e-revenue"},
            {"evidence_id": "e-management"},
        ],
        required_facts=[
            {"fact_id": "F1", "description": "revenue", "acceptable_evidence_ids": ["e-revenue"]},
            {
                "fact_id": "F2",
                "description": "management explanation",
                "acceptable_evidence_ids": ["e-management"],
            },
        ],
        failure_type="CROSS_PAGE_EVIDENCE_SET",
        answerable=True,
    )


def test_targeted_retrieval_queries_the_missing_fact_and_recovers_in_one_round():
    retriever = ScriptedRetriever()
    result = TargetedRetriever(retriever).retrieve(_case(), "What is revenue and why did it change?", top_k=2)

    assert result.initial.complete is False
    assert result.final.complete is True
    assert len(result.rounds) == 2
    assert "management explanation" in retriever.queries[1]
    assert result.selected_ids == {"e-revenue", "e-management"}


def test_targeted_retrieval_stops_after_two_targeted_rounds():
    retriever = NeverCompleteRetriever()
    result = TargetedRetriever(retriever).retrieve(_case(), "What is revenue and why did it change?", top_k=2, max_rounds=2)

    assert len(retriever.queries) == 3
    assert len(result.rounds) == 3
    assert result.final.complete is False
