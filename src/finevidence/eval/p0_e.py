from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from finevidence.benchmarks.loader import load_benchmark
from finevidence.benchmarks.real_finance import build_real_finance_slice
from finevidence.contracts.benchmark import FactRequirement, MiniCase
from finevidence.eval.metrics import complete_evidence_rates, false_answer_eligibility_rate, oracle_gap, structured_fact_metrics
from finevidence.eval.run import _git_commit
from finevidence.evidence.coverage import fact_coverage_for_case
from finevidence.evidence.fact_understanding import DecompositionResult, decompose_required_facts_by_variant
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.targeted import TargetedRetriever


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _predicted_faer(cases: list[MiniCase], predicted_cases: dict[str, MiniCase], selected: dict[str, set[str]], eligibility: dict[str, bool]) -> float | str:
    if not cases:
        return "N/A"
    false_eligible = sum(
        bool(eligibility.get(case.question_id, False))
        and not fact_coverage_for_case(predicted_cases[case.question_id], selected.get(case.question_id, set())).complete
        for case in cases
    )
    return false_eligible / len(cases)


def _variant_run(
    cases: list[MiniCase],
    evidence_by_id: dict,
    initial_selected: dict[str, set[str]],
    hybrid: HybridRetriever,
    variant: str,
    top_k: int,
    max_rounds: int,
) -> tuple[dict, list[dict]]:
    predicted_cases: dict[str, MiniCase] = {}
    initial, final = {}, {}
    rows, traces = [], []
    targeted = TargetedRetriever(hybrid)
    for case in cases:
        candidate = [(item.evidence_id, evidence_by_id[item.evidence_id].text) for item in hybrid.search(case.question, top_k)]
        result: DecompositionResult = decompose_required_facts_by_variant(case.question, variant, candidate if variant == "D3" else None)
        if result.status == "N/A":
            rows.append({"status": result.status, "reason": result.reason, "fact_precision": "N/A", "fact_recall": "N/A", "critical_fact_recall": "N/A", "slot_accuracy": "N/A", "initial_cer": "N/A", "final_cer": "N/A", "recovery": "N/A", "faer": "N/A", "oracle_gap": "N/A"})
            traces.append({"question_id": case.question_id, "variant": variant, "status": result.status, "reason": result.reason})
            continue
        predicted_case = case.model_copy(update={"required_facts": result.facts})
        predicted_cases[case.question_id] = predicted_case
        initial[case.question_id] = initial_selected[case.question_id]
        targeted_result = targeted.retrieve(predicted_case, case.question, top_k=top_k, max_rounds=max_rounds)
        final[case.question_id] = targeted_result.selected_ids
        initial_coverage = fact_coverage_for_case(predicted_case, initial[case.question_id])
        final_coverage = fact_coverage_for_case(predicted_case, final[case.question_id])
        metrics = structured_fact_metrics(case, result.facts)
        rows.append({
            "status": result.status,
            **metrics,
            "initial_cer": float(initial_coverage.complete),
            "final_cer": float(final_coverage.complete),
            "recovery": float(not initial_coverage.complete and final_coverage.complete),
        })
        traces.append({
            "question_id": case.question_id,
            "variant": variant,
            "status": result.status,
            "question_type": result.question_type,
            "facts": [fact.model_dump() for fact in result.facts],
            "initial_ids": sorted(initial[case.question_id]),
            "final_ids": sorted(final[case.question_id]),
            "initial_coverage": asdict(initial_coverage),
            "final_coverage": asdict(final_coverage),
            "rounds": [asdict(item) for item in targeted_result.rounds],
        })
    if not predicted_cases:
        return rows[0], traces
    initial_complete = [fact_coverage_for_case(predicted_cases[case.question_id], initial[case.question_id]).complete for case in cases]
    final_complete = [fact_coverage_for_case(predicted_cases[case.question_id], final[case.question_id]).complete for case in cases]
    partial = sum(not value for value in initial_complete)
    recovered = sum(not before and after for before, after in zip(initial_complete, final_complete))
    aggregate = {
        "status": "READY",
        "fact_precision": sum(row["fact_precision"] for row in rows) / len(rows),
        "fact_recall": sum(row["fact_recall"] for row in rows) / len(rows),
        "critical_fact_recall": _mean_or_na(rows, "critical_fact_recall"),
        "slot_accuracy": _mean_or_na(rows, "slot_accuracy"),
        "initial_cer": sum(initial_complete) / len(initial_complete),
        "final_cer": sum(final_complete) / len(final_complete),
        "recovery": recovered / partial if partial else "N/A",
    }
    eligibility = {case.question_id: bool(fact_coverage_for_case(predicted_cases[case.question_id], final[case.question_id]).complete) for case in cases}
    aggregate["faer"] = _predicted_faer(cases, predicted_cases, final, eligibility)
    aggregate["oracle_gap"] = oracle_gap(None, aggregate["final_cer"])
    return aggregate, traces


def _mean_or_na(rows: list[dict], key: str) -> float | str:
    values = [row[key] for row in rows if isinstance(row.get(key), (int, float))]
    return sum(values) / len(values) if values else "N/A"


def run_p0_e(config: dict) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    slice_root = Path(config.get("slice_root", project_root / "benchmarks/real_finance_v1"))
    if not slice_root.is_absolute():
        slice_root = project_root / slice_root
    if not (slice_root / "manifest.json").exists():
        build_real_finance_slice(
            project_root.parent / "research/repos/tat-qa/dataset_raw/tatqa_dataset_dev.json",
            project_root.parent / "research/repos/FinQA/dataset/dev.json",
            slice_root,
            50,
            50,
        )
    benchmark = load_benchmark(slice_root)
    artifact_root = Path(config.get("artifact_root", project_root / "artifacts/p0_e_runs"))
    if not artifact_root.is_absolute():
        artifact_root = project_root / artifact_root
    run_dir = artifact_root / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=False)
    top_k = int(config.get("top_k", 5))
    max_rounds = min(int(config.get("max_rounds", 2)), 2)
    hybrid = HybridRetriever()
    hybrid.fit(benchmark.evidence)
    evidence_by_id = {item.evidence_id: item for item in benchmark.evidence}
    initial_selected = {case.question_id: {item.evidence_id for item in hybrid.search(case.question, top_k)} for case in benchmark.cases}
    gold_final = TargetedRetriever(hybrid)
    gold_selected = {}
    for case in benchmark.cases:
        gold_selected[case.question_id] = gold_final.retrieve(case, case.question, top_k=top_k, max_rounds=max_rounds).selected_ids
    gold_rates = complete_evidence_rates(benchmark.cases, initial_selected, gold_selected)
    variants = {}
    traces = []
    for variant, label in (("D0", "D0 Heuristic"), ("D1", "D1 LLM Direct"), ("D2", "D2 Schema-constrained"), ("D3", "D3 Evidence-aware")):
        aggregate, variant_traces = _variant_run(benchmark.cases, evidence_by_id, initial_selected, hybrid, variant, top_k, max_rounds)
        if aggregate.get("status") == "N/A":
            aggregate["oracle_gap"] = "N/A"
        elif label != "D1 LLM Direct":
            aggregate["oracle_gap"] = oracle_gap(gold_rates["final_complete_evidence_rate"], aggregate["final_cer"])
            if isinstance(aggregate["oracle_gap"], (int, float)) and aggregate["oracle_gap"] < 0:
                aggregate["oracle_gap_warning"] = "NEGATIVE_GAP_PREDICTED_FACTS_NOT_CALIBRATED_TO_GOLD_FACTS"
        variants[label] = aggregate
        traces.extend(variant_traces)
    metrics = {
        "dataset_type": "public_benchmark_slice",
        "source_splits": {dataset: sum(case.source_dataset == dataset for case in benchmark.cases) for dataset in ("TAT-QA", "FinQA")},
        "gold_evidence_completion": {**gold_rates, "faer": false_answer_eligibility_rate(benchmark.cases, gold_selected, {case.question_id: fact_coverage_for_case(case, gold_selected[case.question_id]).complete for case in benchmark.cases})},
        "fact_understanding": variants,
        "evidence_completion": {
            "gold_final_cer": gold_rates["final_complete_evidence_rate"],
            "oracle_gap_definition": "gold_final_cer - predicted_final_cer",
            "oracle_gap": {label: row.get("oracle_gap", "N/A") for label, row in variants.items()},
        },
    }
    _write_json(run_dir / "config.json", {**config, "git_commit": _git_commit(project_root), "runtime": {"python": sys.version, "platform": platform.platform()}})
    _write_json(run_dir / "dataset_manifest.json", benchmark.manifest)
    _write_json(run_dir / "metrics.json", metrics)
    (run_dir / "per_query_trace.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in traces), encoding="utf-8")
    (run_dir / "failure_cases.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in traces if row.get("status") == "READY" and not row.get("final_coverage", {}).get("complete", True)), encoding="utf-8")
    return run_dir


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Run P0-E evidence requirement understanding evaluation.")
    parser.add_argument("--config", default="configs/p0_e_cpu.json")
    args = parser.parse_args()
    path = Path(args.config)
    if not path.is_absolute():
        path = project_root / path
    print(run_p0_e(json.loads(path.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
