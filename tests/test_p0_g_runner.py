import json

from finevidence.eval.p0_g import run_p0_g


def test_p0_g_runner_emits_graph_alignment_and_coverage_artifacts(tmp_path):
    result = run_p0_g({"artifact_root": str(tmp_path / "runs")})

    names = {path.name for path in result.iterdir()}
    assert {"metrics.json", "dataset_manifest.json", "per_query_trace.jsonl", "requirement_graphs.jsonl", "alignment_results.jsonl", "failure_cases.jsonl"} <= names
    metrics = json.loads((result / "metrics.json").read_text(encoding="utf-8"))
    assert set(metrics["alignment"]) == {"Gold", "D0 Heuristic", "D1 LLM Direct", "D2 Schema-constrained", "D3 Evidence-aware", "D4 Requirement-Graph-Constrained"}
    assert "independent_cer" in metrics["alignment"]["D4 Requirement-Graph-Constrained"]
