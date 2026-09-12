from finevidence.ranking.facets import extract_facets
from finevidence.eval.metrics import facet_extraction_metrics


def test_facet_metrics_distinguish_paraphrase_miss_from_exact_match():
    gold = {"entity": "HSBC Holdings", "metric": "CET1 ratio", "period": "2024"}
    predicted = extract_facets("How did the Group's common equity tier 1 position change during the year?")

    metrics = facet_extraction_metrics(gold, predicted)

    assert metrics["entity_accuracy"] == 0.0
    assert metrics["metric_accuracy"] == 0.0
    assert metrics["period_accuracy"] == 0.0
