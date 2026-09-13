import json
from pathlib import Path

from finevidence.eval.b3 import RECOVERY_K, SYSTEMS, _percentile


def test_b3_1_uses_explicit_recovery_cutoffs_and_honest_t1_name():
    assert RECOVERY_K == (1, 5, 10)
    assert "T1 Parsed Page Text" in SYSTEMS
    assert "T1 Structured Text/Table" not in SYSTEMS


def test_hsbc_routing_set_is_balanced_and_real_page_provenanced():
    root = Path(__file__).parents[1]
    manifest = json.loads((root / "benchmarks/hsbc_multimodal_routing_v1/manifest.json").read_text(encoding="utf-8"))
    assert manifest["class_counts"] == {"TEXT_SUFFICIENT": 10, "TABLE_PARSED_SUFFICIENT": 10, "VISUAL_NEEDED": 10}
    rows = [json.loads(line) for line in (root / "benchmarks/hsbc_multimodal_routing_v1/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 30
    assert all(row["source_hashes"] and row["positive_evidence_id"].endswith(":image") for row in rows)


def test_latency_percentile_is_empty_safe():
    assert _percentile([], 95) == "N/A"
