from finevidence.eval.p0_d import run_p0_d
import json


def test_p0_d_runner_emits_public_tables_and_hsbc_readiness_gate(tmp_path):
    result = run_p0_d({"artifact_root": str(tmp_path / "runs"), "slice_root": str(tmp_path / "slice")})

    assert {"metrics.json", "dataset_manifest.json", "per_query_trace.jsonl", "hsbc_readiness.json"} <= {
        path.name for path in result.iterdir()
    }
    metrics = json.loads((result / "metrics.json").read_text(encoding="utf-8"))
    assert set(metrics["evidence_eligibility"]) == {"Top-K RAG", "Coverage Gate", "Targeted Retrieval"}
