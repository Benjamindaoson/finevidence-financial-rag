from pathlib import Path

from finevidence.eval.p0_bc import run_p0_bc


def test_p0_bc_runner_outputs_two_tables_and_round_trace(tmp_path):
    result = run_p0_bc({"project_root": str(tmp_path), "artifact_root": str(tmp_path / "runs")})

    assert {"ranking_table.json", "sufficiency_table.json", "per_query_trace.jsonl"} <= {
        path.name for path in result.iterdir()
    }
