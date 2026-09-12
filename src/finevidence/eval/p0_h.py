from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from finevidence.benchmarks.hsbc import build_hsbc_evidence, download_hsbc_corpus
from finevidence.benchmarks.loader import load_benchmark
from finevidence.contracts.p0_h import LocalLLMConfig
from finevidence.contracts.requirements import RequirementGraph
from finevidence.eval.p0_h_annotation import build_requirement_adjudicated_subset
from finevidence.eval.p0_h_hsbc import evaluate_hsbc_ranking, mine_hsbc_natural_hard_cases
from finevidence.eval.p0_h_requirements import evaluate_requirement_methods
from finevidence.eval.run import _git_commit
from finevidence.evidence.fact_understanding import classify_question
from finevidence.evidence.llm_direct import LocalLLMRunner, run_direct_decomposition
from finevidence.ranking.facets import evidence_facets, extract_facets


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows), encoding="utf-8")


def _select_cases(benchmark, count: int) -> list:
    by_type = {}
    for case in benchmark.cases:
        by_type.setdefault(classify_question(case.question), []).append(case)
    if count != 36:
        return sorted(benchmark.cases, key=lambda item: item.question_id)[:count]
    quotas = {"factual": 10, "comparison": 4, "numerical": 18, "trend": 3, "explanation": 1, "multi-document synthesis": 0}
    selected = []
    for kind, quota in quotas.items():
        selected.extend(sorted(by_type.get(kind, []), key=lambda item: item.question_id)[:quota])
    if len(selected) < count:
        used = {item.question_id for item in selected}
        selected.extend(item for item in sorted(benchmark.cases, key=lambda item: item.question_id) if item.question_id not in used)
    return sorted(selected[:count], key=lambda item: item.question_id)


def _model_sha256(path: str | None) -> str | None:
    if not path or not Path(path).exists():
        return None
    digest = hashlib.sha256()
    for item in sorted(Path(path).rglob("*")):
        if item.is_file():
            digest.update(str(item.relative_to(path)).encode())
            digest.update(hashlib.sha256(item.read_bytes()).digest())
    return digest.hexdigest()


def _hsbc_manifest_or_na(config: dict, run_dir: Path) -> tuple[dict, list]:
    local_root = Path(config.get("hsbc_artifact_root", "artifacts/hsbc_local_sources"))
    if not local_root.is_absolute():
        local_root = Path(__file__).resolve().parents[3] / local_root
    manifest_path = local_root / "hsbc_corpus_manifest.json"
    try:
        if not manifest_path.exists() and config.get("download_hsbc", True):
            download_hsbc_corpus(config.get("hsbc_source_manifest", "data/hsbc_public_sources.json"), local_root)
        if not manifest_path.exists():
            manifest = {"status": "N/A", "reason": "HSBC_CORPUS_NOT_DOWNLOADED"}
            _write_json(run_dir / "hsbc_corpus_manifest.json", manifest)
            return manifest, []
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        evidence = build_hsbc_evidence(manifest)
        _write_json(run_dir / "hsbc_corpus_manifest.json", manifest)
        return {"status": "READY", **manifest, "evidence_count": len(evidence)}, evidence
    except Exception as exc:
        manifest = {"status": "N/A", "reason": f"HSBC_CORPUS_ERROR: {type(exc).__name__}: {exc}"}
        _write_json(run_dir / "hsbc_corpus_manifest.json", manifest)
        return manifest, []


def run_p0_h(config: dict) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    benchmark = load_benchmark(project_root / "benchmarks/real_finance_v1")
    run_root = Path(config.get("artifact_root", project_root / "artifacts/p0_h_runs"))
    if not run_root.is_absolute():
        run_root = project_root / run_root
    run_dir = run_root / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir.mkdir(parents=True, exist_ok=False)
    selected = _select_cases(benchmark, int(config.get("requirement_case_count", 36)))
    llm_config = LocalLLMConfig(model_id=config.get("llm_model_id", "HuggingFaceTB/SmolLM2-135M-Instruct"), model_path=config.get("llm_model_path"), max_new_tokens=int(config.get("llm_max_new_tokens", 256)))
    d1_results = {}
    d1_graphs: dict[str, RequirementGraph] = {}
    d1_runner = None
    if config.get("run_d1", True):
        d1_runner = LocalLLMRunner(llm_config)
        for case in selected:
            result = run_direct_decomposition(case.question, llm_config, d1_runner)
            d1_results[case.question_id] = result
            if result.status == "READY":
                d1_graphs[case.question_id] = result.graph
    annotation_manifest = build_requirement_adjudicated_subset(benchmark, [case.question_id for case in selected], run_dir, d1_graphs, created_at_utc=config.get("annotation_timestamp_utc", "2026-09-13T00:00:00Z"))
    annotations = {}
    for line in (run_dir / "annotation_adjudicated.jsonl").read_text(encoding="utf-8").splitlines():
        from finevidence.contracts.p0_h import RequirementAdjudicatedCase

        row = RequirementAdjudicatedCase.model_validate_json(line)
        annotations[row.case_id] = row
    requirement_result = evaluate_requirement_methods(selected, annotations, d1_graphs, benchmark.evidence, int(config.get("top_k", 5)))
    d1_reason = next((result.reason for result in d1_results.values() if result.reason), "NO_VALID_LLM_REQUIREMENTS")
    requirement_result["summary"]["D1 LLM Direct"] = {"status": "N/A", "reason": d1_reason}
    for trace in requirement_result["traces"]:
        if trace["method"] == "D1 LLM Direct":
            result = d1_results.get(trace["question_id"])
            trace["reason"] = result.reason if result else "NO_VALID_LLM_REQUIREMENTS"
            trace["raw_output"] = result.raw_output if result else None
    prediction_rows = []
    for trace in requirement_result["traces"]:
        prediction_rows.append({
            "question_id": trace["question_id"],
            "method": trace["method"],
            "status": trace.get("status", "READY"),
            "reason": trace.get("reason"),
            "graph": {"requirements": trace.get("predicted_requirements", []), "edges": []},
            "matches": trace.get("matches", []),
            "coverage": trace.get("coverage"),
            "raw_output": d1_results.get(trace["question_id"]).raw_output if trace["method"] == "D1 LLM Direct" and trace["question_id"] in d1_results else None,
        })
    _write_jsonl(run_dir / "requirement_predictions.jsonl", prediction_rows)
    _write_json(run_dir / "requirement_metrics.json", {"dataset_type": "manually_subsetted_model_assisted_adjudication", "summary": requirement_result["summary"], "adjudicated_requirement_coverage": requirement_result["adjudicated_coverage"]})
    _write_jsonl(run_dir / "requirement_failure_cases.jsonl", requirement_result["failures"])
    hsbc_manifest, hsbc_evidence = _hsbc_manifest_or_na(config, run_dir)
    hsbc_cases = mine_hsbc_natural_hard_cases(hsbc_evidence, int(config.get("hsbc_target_count", 60))) if hsbc_evidence and int(config.get("hsbc_target_count", 60)) > 0 else []
    _write_jsonl(run_dir / "hsbc_hard_cases.jsonl", [item.model_dump() for item in hsbc_cases])
    if hsbc_cases:
        ranking_result = evaluate_hsbc_ranking(hsbc_cases, hsbc_evidence, int(config.get("top_k", 5)))
        rankings = ranking_result.pop("rankings")
        _write_jsonl(run_dir / "ranking_predictions.jsonl", [{"case_id": case_id, "method": method, "ranking": ranking} for method, values in rankings.items() for case_id, ranking in sorted(values.items())])
        _write_json(run_dir / "ranking_metrics.json", ranking_result)
        ranking_failures = [{"case_id": case.case_id, "category": case.category, "method": method, "positive_evidence_id": case.positive_evidence_id, "ranking": values[case.case_id]} for method, values in rankings.items() for case in hsbc_cases if not values[case.case_id] or values[case.case_id][0] != case.positive_evidence_id]
        _write_jsonl(run_dir / "ranking_failure_cases.jsonl", ranking_failures)
        facet_rows = []
        for case in hsbc_cases:
            predicted = extract_facets(case.question)
            facet_rows.append({"case_id": case.case_id, "predicted": {field: getattr(predicted, field) for field in case.adjudicated_facets}, "adjudicated": case.adjudicated_facets})
        _write_jsonl(run_dir / "facet_predictions.jsonl", facet_rows)
    else:
        _write_json(run_dir / "ranking_metrics.json", {"status": "N/A", "reason": hsbc_manifest.get("reason", "NO_HSBC_HARD_CASES")})
        _write_jsonl(run_dir / "ranking_predictions.jsonl", [])
        _write_jsonl(run_dir / "ranking_failure_cases.jsonl", [])
        _write_jsonl(run_dir / "facet_predictions.jsonl", [])
    _write_jsonl(run_dir / "per_query_trace.jsonl", requirement_result["traces"])
    requirement_summary = requirement_result["summary"]
    gate_values = {
        "requirement_adjudicated_v1": annotation_manifest.case_count >= 30,
        "d1_real_model_attempted": bool(d1_results),
        "d4_requirement_improvement": requirement_summary.get("D4 Requirement-Graph-Constrained", {}).get("requirement_recall", 0) > max(requirement_summary.get("D0 Heuristic", {}).get("requirement_recall", 0), requirement_summary.get("D2 Schema-constrained", {}).get("requirement_recall", 0)),
        "independent_coverage_validated": all(isinstance(requirement_result["adjudicated_coverage"].get(field), (int, float)) for field in ("independent_cer", "critical_coverage")),
        "requirement_failure_localization": bool(requirement_result["failures"] or requirement_result["traces"]),
        "hsbc_provenance_fixed": hsbc_manifest.get("status") == "READY",
        "hsbc_natural_hard_cases_at_least_50": len(hsbc_cases) >= 50,
        "facet_evaluation_available": bool(hsbc_cases),
    }
    gate = {
        "status": "READY" if all(gate_values[name] for name in ("requirement_adjudicated_v1", "independent_coverage_validated", "requirement_failure_localization", "hsbc_provenance_fixed", "hsbc_natural_hard_cases_at_least_50")) else "BLOCKED",
        "gates": gate_values,
        "reason": "B3 readiness requires adjudicated requirements, validated independent coverage, failure localization, fixed HSBC provenance and at least 50 valid HSBCNaturalHard-v1 cases. D4 improvement and D1 availability are reported but are not silently treated as success.",
    }
    _write_json(run_dir / "b3_gate.json", gate)
    resolved_model_path = d1_runner.resolved_model_path if d1_runner else llm_config.model_path
    _write_json(run_dir / "config.json", {**config, "git_commit": _git_commit(project_root), "llm": {**llm_config.model_dump(), "resolved_model_path": resolved_model_path, "model_sha256": _model_sha256(resolved_model_path)}, "runtime": {"python": sys.version, "platform": platform.platform()}})
    _write_json(run_dir / "dataset_manifest.json", benchmark.manifest)
    return run_dir


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Run P0-H requirement adjudication and HSBC natural hard-case evaluation.")
    parser.add_argument("--config", default="configs/p0_h_cpu.json")
    args = parser.parse_args()
    path = Path(args.config)
    if not path.is_absolute():
        path = project_root / path
    print(run_p0_h(json.loads(path.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
