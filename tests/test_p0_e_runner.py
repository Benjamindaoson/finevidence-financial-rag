import json
import pytest

from finevidence.eval.p0_e import run_p0_e
from finevidence.eval.metrics import oracle_gap


def test_oracle_gap_is_gold_minus_predicted_and_allows_calibration_warning():
    assert oracle_gap(0.89, 0.57) == pytest.approx(0.32)
    assert oracle_gap(0.89, 0.99) == pytest.approx(-0.1)


def test_p0_e_runner_emits_variant_metrics_and_oracle_gap(tmp_path):
    result = run_p0_e({"artifact_root": str(tmp_path / "runs")})

    metrics = json.loads((result / "metrics.json").read_text(encoding="utf-8"))
    assert set(metrics["fact_understanding"]) == {"D0 Heuristic", "D1 LLM Direct", "D2 Schema-constrained", "D3 Evidence-aware"}
    assert metrics["fact_understanding"]["D1 LLM Direct"]["status"] == "N/A"
    assert "oracle_gap" in metrics["evidence_completion"]
    assert (result / "failure_cases.jsonl").exists()
