import json

from finevidence.eval.p0_h import run_p0_h


def test_p0_h_runner_emits_required_artifacts(tmp_path):
    run_dir = run_p0_h({"artifact_root": str(tmp_path / "runs"), "requirement_case_count": 6, "hsbc_target_count": 0, "run_d1": False, "download_hsbc": False})
    names = {item.name for item in run_dir.iterdir()}
    required = {"config.json", "dataset_manifest.json", "annotation_manifest.json", "requirement_annotations.jsonl", "requirement_predictions.jsonl", "requirement_metrics.json", "requirement_failure_cases.jsonl", "hsbc_corpus_manifest.json", "hsbc_hard_cases.jsonl", "facet_predictions.jsonl", "ranking_predictions.jsonl", "ranking_metrics.json", "ranking_failure_cases.jsonl", "per_query_trace.jsonl", "b3_gate.json"}
    assert required <= names
    assert json.loads((run_dir / "b3_gate.json").read_text(encoding="utf-8"))["status"] == "BLOCKED"
