import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_visualstress_audit_selection_is_fixed_and_performance_blind():
    selection = json.loads((ROOT / "benchmarks/hsbc_visual_stress_v1/audit_selection.json").read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in (ROOT / "benchmarks/hsbc_visual_stress_v1/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert selection["case_count"] == 20
    assert selection["performance_blind"] is True
    assert not any("Recall" in key or "ranking" in key.lower() for key in selection)
    assert selection["source_cases_sha256"] == _sha256(ROOT / "benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    assert len(selection["case_ids"]) == len(set(selection["case_ids"])) == 20
    assert set(selection["case_ids"]).issubset({row["case_id"] for row in cases})


def test_natural_control_is_frozen_and_separate_from_stress_pages():
    manifest = json.loads((ROOT / "benchmarks/hsbc_natural_multimodal_v1/manifest.json").read_text(encoding="utf-8"))
    natural = [json.loads(line) for line in (ROOT / "benchmarks/hsbc_natural_multimodal_v1/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    stress = [json.loads(line) for line in (ROOT / "benchmarks/hsbc_visual_stress_v1/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    stress_pages = {item.replace(":image", ":page") for row in stress for item in row["candidate_evidence_ids"]}
    natural_pages = {row["positive_evidence_id"].replace(":image", ":page") for row in natural}
    assert manifest["dataset_name"] == "HSBCNaturalMultimodal-v1"
    assert 60 <= len(natural) <= 100
    assert manifest["selection_frozen_before_retrieval"] is True
    assert manifest["performance_blind"] is True
    assert natural_pages.isdisjoint(stress_pages)
    assert all(row["dataset_name"] == "HSBCNaturalMultimodal-v1" for row in natural)
    assert all(row["candidate_evidence_ids"] and row["positive_evidence_id"] in row["candidate_evidence_ids"] for row in natural)


def test_public_slice_revision_and_source_files_remain_frozen():
    manifest = json.loads((ROOT / "benchmarks/finragbench_v_slice_v1/manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_revision"] == "d0d65255c94e687caa81ac9da7758ed25ff046a5"
    assert manifest["query_count"] == 100
    assert manifest["source_files"]["queries_en.json"] == _sha256(ROOT / "data/finragbench_v_source/queries_en.json")
    assert manifest["source_files"]["qrels_en.tsv"] == _sha256(ROOT / "data/finragbench_v_source/qrels_en.tsv")


def test_public_blocker_does_not_claim_page_metrics():
    blocker = json.loads((ROOT / "data/finragbench_v_source/b3_2_download_blocker.json").read_text(encoding="utf-8"))
    assert blocker["status"] == "BLOCKED"
    assert blocker["revision"] == "d0d65255c94e687caa81ac9da7758ed25ff046a5"
    assert blocker["official_response_evidence"]["x_repo_commit"] == blocker["revision"]
    assert blocker["public_metrics"] == "N/A"
