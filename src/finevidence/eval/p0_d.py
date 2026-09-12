from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from finevidence.benchmarks.loader import load_benchmark
from finevidence.benchmarks.real_finance import build_real_finance_slice
from finevidence.eval.metrics import complete_evidence_rates, fact_decomposition_metrics, facet_extraction_metrics, evaluate_retrieval
from finevidence.eval.run import _git_commit
from finevidence.evidence.coverage import fact_coverage_for_case
from finevidence.evidence.decomposition import decompose_required_facts
from finevidence.ranking.rerankers import FacetAwareReranker
from finevidence.ranking.facets import extract_facets
from finevidence.retrieval.dense import DenseRetriever
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.targeted import TargetedRetriever


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _json_default(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _predicted_coverage(predicted_facts, selected_ids: set[str], evidence_by_id) -> tuple[int, int, bool]:
    covered = 0
    for fact in predicted_facts:
        fact_tokens = _tokens(fact.description)
        if any(len(fact_tokens & _tokens(evidence_by_id[item].text)) / max(len(fact_tokens), 1) >= 0.2 for item in selected_ids if item in evidence_by_id):
            covered += 1
    total = len(predicted_facts)
    return covered, total, bool(total) and covered == total


def _predicted_rates(cases, initial_selected, final_selected, evidence_by_id):
    initial_complete, final_complete, recoverable = [], [], []
    for case in cases:
        predicted = decompose_required_facts(case.question)
        initial = _predicted_coverage(predicted, initial_selected.get(case.question_id, set()), evidence_by_id)[2]
        final = _predicted_coverage(predicted, final_selected.get(case.question_id, set()), evidence_by_id)[2]
        initial_complete.append(initial)
        final_complete.append(final)
        if not initial:
            recoverable.append(final)
    return {
        "initial_complete_evidence_rate": sum(initial_complete) / len(cases) if cases else "N/A",
        "final_complete_evidence_rate": sum(final_complete) / len(cases) if cases else "N/A",
        "partial_to_complete_recovery_rate": sum(recoverable) / len(recoverable) if recoverable else "N/A",
    }


def run_p0_d(config: dict) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    raw_tatqa = Path(config.get("tatqa_path", project_root.parent / "research/repos/tat-qa/dataset_raw/tatqa_dataset_dev.json"))
    raw_finqa = Path(config.get("finqa_path", project_root.parent / "research/repos/FinQA/dataset/dev.json"))
    if not raw_tatqa.is_absolute():
        raw_tatqa = project_root / raw_tatqa
    if not raw_finqa.is_absolute():
        raw_finqa = project_root / raw_finqa
    slice_root = Path(config.get("slice_root", project_root / "benchmarks/real_finance_v1"))
    if not slice_root.is_absolute():
        slice_root = project_root / slice_root
    if not (slice_root / "manifest.json").exists():
        build_real_finance_slice(raw_tatqa, raw_finqa, slice_root, int(config.get("tatqa_limit", 50)), int(config.get("finqa_limit", 50)))
    benchmark = load_benchmark(slice_root)
    artifact_root = Path(config.get("artifact_root", project_root / "artifacts/p0_d_runs"))
    if not artifact_root.is_absolute():
        artifact_root = project_root / artifact_root
    run_dir = artifact_root / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=False)
    evidence_by_id = {item.evidence_id: item for item in benchmark.evidence}
    dense, hybrid = DenseRetriever(), HybridRetriever()
    dense.fit(benchmark.evidence)
    hybrid.fit(benchmark.evidence)
    top_k = int(config.get("top_k", 5))
    initial_selected, final_selected, traces = {}, {}, []
    facet_rows = []
    decomposition_rows = []
    targeted = TargetedRetriever(hybrid)
    for case in benchmark.cases:
        initial_results = dense.search(case.question, top_k)
        initial_selected[case.question_id] = {item.evidence_id for item in initial_results}
        result = targeted.retrieve(case, case.question, top_k=top_k, max_rounds=min(int(config.get("max_rounds", 2)), 2))
        final_selected[case.question_id] = result.selected_ids
        predicted = decompose_required_facts(case.question)
        decomposition_rows.append(fact_decomposition_metrics(case, predicted))
        traces.append({
            "question_id": case.question_id,
            "source_dataset": case.source_dataset,
            "source_record_id": case.source_record_id,
            "gold": {"initial": asdict(fact_coverage_for_case(case, initial_selected[case.question_id])), "final": asdict(result.final)},
            "predicted_fact_metrics": fact_decomposition_metrics(case, predicted),
            "predicted_facts": [fact.model_dump() for fact in predicted],
            "rounds": [asdict(item) for item in result.rounds],
            "initial_ids": sorted(initial_selected[case.question_id]),
            "final_ids": sorted(result.selected_ids),
        })
        facet_rows.append({"question_id": case.question_id, "predicted": asdict(extract_facets(case.question)), "gold": None, "metrics": facet_extraction_metrics({}, extract_facets(case.question))})

    generic_rankings, facet_rankings = {}, {}
    facet_ranker = FacetAwareReranker()
    for case in benchmark.cases:
        generic = hybrid.search(case.question, top_k)
        generic_rankings[case.question_id] = [item.evidence_id for item in generic]
        facet_rankings[case.question_id] = [item.evidence_id for item in facet_ranker.rank(case.question, generic, evidence_by_id, top_k)]
    metrics = {
        "dataset_type": "public_benchmark_slice",
        "source_splits": {dataset: sum(case.source_dataset == dataset for case in benchmark.cases) for dataset in ("TAT-QA", "FinQA")},
        "ranking": {
            "Dense": evaluate_retrieval(benchmark.cases, {case.question_id: [item.evidence_id for item in dense.search(case.question, top_k)] for case in benchmark.cases}, top_k),
            "Hybrid + Generic": evaluate_retrieval(benchmark.cases, generic_rankings, top_k),
            "Facet-aware / predicted facets": evaluate_retrieval(benchmark.cases, facet_rankings, top_k),
            "Facet-aware / gold facets": "N/A (source slice has no canonical facet labels)",
        },
        "gold_fact_condition": complete_evidence_rates(benchmark.cases, initial_selected, final_selected),
        "predicted_fact_condition": _predicted_rates(benchmark.cases, initial_selected, final_selected, evidence_by_id),
        "fact_decomposition": {
            key: sum(row[key] for row in decomposition_rows) / len(decomposition_rows)
            for key in ("required_fact_precision", "required_fact_recall")
        },
        "facet_extraction": {"status": "N/A", "reason": "TAT-QA and FinQA do not provide canonical entity/metric/period facet labels"},
    }
    _write_json(run_dir / "config.json", {**config, "git_commit": _git_commit(project_root), "runtime": {"python": sys.version, "platform": platform.platform()}})
    _write_json(run_dir / "dataset_manifest.json", benchmark.manifest)
    _write_json(run_dir / "metrics.json", metrics)
    _write_json(run_dir / "facet_metrics.json", facet_rows)
    _write_json(run_dir / "hsbc_readiness.json", {"status": "N/A", "reason": "LOCAL_PROVENANCE_SOURCE_MISSING", "required": "licensed HSBC source corpus"})
    (run_dir / "per_query_trace.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, default=_json_default) + "\n" for row in traces), encoding="utf-8")
    (run_dir / "failure_cases.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, default=_json_default) + "\n" for row in traces if not row["gold"]["final"]["complete"]), encoding="utf-8")
    return run_dir


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Run public real-finance validation on TAT-QA and FinQA.")
    parser.add_argument("--config", default="configs/p0_d_cpu.json")
    args = parser.parse_args()
    path = Path(args.config)
    if not path.is_absolute():
        path = project_root / path
    print(run_p0_d(json.loads(path.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
