from finevidence.benchmarks.real_finance import project_finqa_record
from finevidence.evidence.decomposition import decompose_required_facts
from finevidence.eval.metrics import fact_decomposition_metrics


def _case():
    _, case = project_finqa_record(
        {
            "id": "r-1",
            "pre_text": ["Revenue was 100."],
            "post_text": [],
            "table": [["Metric", "2024"], ["Revenue", "100"]],
            "qa": {
                "question": "What was revenue and what was the change?",
                "gold_inds": {"table_1": "revenue was 100 ;", "text_0": "revenue was 100 ."},
                "program": "subtract(100, 90)",
                "exe_ans": 10.0,
                "answer": "10",
            },
        },
        split="dev",
    )
    return case


def test_predicted_fact_recall_exposes_omitted_gold_fact():
    case = _case()
    predicted = decompose_required_facts(case.question)

    metrics = fact_decomposition_metrics(case, predicted)

    assert metrics["required_fact_recall"] < 1.0
    assert metrics["required_fact_precision"] <= 1.0
