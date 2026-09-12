from __future__ import annotations

import json
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from finevidence.benchmarks.loader import load_benchmark
from finevidence.evidence.coverage import fact_coverage_for_case
from finevidence.eval.metrics import complete_evidence_rates, evaluate_retrieval, false_answer_eligibility_rate
from finevidence.eval.run import _git_commit
from finevidence.ranking.rerankers import FacetAwareReranker, HardNegativeAwareReranker
from finevidence.retrieval.dense import DenseRetriever
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.targeted import TargetedRetriever


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _json_default(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)


def _resolve(root: Path, value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else root / path


def _rankings(retriever, cases, top_k: int) -> tuple[dict[str, list[str]], list[dict]]:
    rankings: dict[str, list[str]] = {}
    predictions = []
    for case in cases:
        results = retriever.search(case.question, top_k)
        rankings[case.question_id] = [item.evidence_id for item in results]
        predictions.append({"question_id": case.question_id, "retrieved": [item.model_dump() for item in results]})
    return rankings, predictions


def run_p0_bc(config: dict) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    completeness_root = _resolve(project_root, config.get("completeness_root"), project_root / "benchmarks/evidence_completeness_v1")
    hardset_root = _resolve(project_root, config.get("finance_hardset_root"), project_root / "benchmarks/finance_hardset_v1")
    artifact_root = _resolve(project_root, config.get("artifact_root"), project_root / "artifacts/p0_bc_runs")
    completeness = load_benchmark(completeness_root)
    hardset = load_benchmark(hardset_root)
    top_k = int(config.get("top_k", 5))
    initial_top_k = int(config.get("initial_top_k", 1))
    targeted_top_k = int(config.get("targeted_top_k", top_k))
    max_rounds = min(int(config.get("max_rounds", 2)), 2)
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}"
    run_dir = artifact_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    dense = DenseRetriever()
    dense.fit(hardset.evidence)
    hybrid = HybridRetriever()
    hybrid.fit(hardset.evidence)
    completeness_hybrid = HybridRetriever()
    completeness_hybrid.fit(completeness.evidence)
    evidence_by_id = {item.evidence_id: item for item in hardset.evidence}
    hard_ranker = HardNegativeAwareReranker().fit(hardset.cases, evidence_by_id)
    facet_ranker = FacetAwareReranker()

    dense_rankings, dense_predictions = _rankings(dense, hardset.cases, top_k)
    hybrid_rankings, hybrid_predictions = _rankings(hybrid, hardset.cases, top_k)
    facet_rankings: dict[str, list[str]] = {}
    hard_rankings: dict[str, list[str]] = {}
    for case in hardset.cases:
        candidates = hybrid.search(case.question, top_k)
        facet_results = facet_ranker.rank(case.question, candidates, evidence_by_id, top_k)
        hard_results = hard_ranker.rank(case.question, facet_results, evidence_by_id, top_k)
        facet_rankings[case.question_id] = [item.evidence_id for item in facet_results]
        hard_rankings[case.question_id] = [item.evidence_id for item in hard_results]

    ranking_table = []
    for name, rankings in (
        ("Dense", dense_rankings),
        ("Hybrid + Generic Reranker", hybrid_rankings),
        ("+ Financial Facets", facet_rankings),
        ("+ Financial-aware Reranker", hard_rankings),
    ):
        ranking_table.append({"variant": name, **evaluate_retrieval(hardset.cases, rankings, top_k)})

    base_selected: dict[str, set[str]] = {}
    targeted_selected: dict[str, set[str]] = {}
    eligibility_top_k: dict[str, bool] = {}
    eligibility_complete: dict[str, bool] = {}
    trace_lines = []
    targeted = TargetedRetriever(completeness_hybrid)
    for case in completeness.cases:
        base_results = completeness_hybrid.search(case.question, initial_top_k)
        base_ids = {item.evidence_id for item in base_results}
        base_selected[case.question_id] = base_ids
        base_coverage = fact_coverage_for_case(case, base_ids)
        eligibility_top_k[case.question_id] = bool(base_coverage.covered_fact_count)
        eligibility_complete[case.question_id] = base_coverage.complete
        result = targeted.retrieve(
            case,
            case.question,
            top_k=targeted_top_k,
            initial_top_k=initial_top_k,
            max_rounds=max_rounds,
        )
        targeted_selected[case.question_id] = result.selected_ids
        trace_lines.append(
            {
                "question_id": case.question_id,
                "initial": asdict(result.initial),
                "final": asdict(result.final),
                "selected_ids": sorted(result.selected_ids),
                "rounds": [asdict(item) for item in result.rounds],
            }
        )

    top_k_rates = complete_evidence_rates(completeness.cases, base_selected, base_selected)
    gate_rates = complete_evidence_rates(completeness.cases, base_selected, base_selected)
    targeted_rates = complete_evidence_rates(completeness.cases, base_selected, targeted_selected)
    sufficiency_table = [
        {
            "strategy": "Top-K RAG",
            **top_k_rates,
            "false_answer_eligibility_rate": false_answer_eligibility_rate(completeness.cases, base_selected, eligibility_top_k),
        },
        {
            "strategy": "Coverage Gate",
            **gate_rates,
            "false_answer_eligibility_rate": false_answer_eligibility_rate(completeness.cases, base_selected, eligibility_complete),
        },
        {
            "strategy": "Targeted Retrieval (max 2 rounds)",
            **targeted_rates,
            "false_answer_eligibility_rate": false_answer_eligibility_rate(completeness.cases, targeted_selected, {
                case.question_id: fact_coverage_for_case(case, targeted_selected.get(case.question_id, set())).complete
                for case in completeness.cases
            }),
        },
    ]

    all_predictions = []
    for name, rows in (("Dense", dense_predictions), ("Hybrid + Generic Reranker", hybrid_predictions)):
        all_predictions.extend({"variant": name, **row} for row in rows)
    _write_json(run_dir / "config.json", {
        **config,
        "resolved": {"completeness_root": str(completeness_root), "finance_hardset_root": str(hardset_root)},
        "git_commit": _git_commit(project_root),
        "runtime": {"python": sys.version, "platform": platform.platform()},
    })
    _write_json(run_dir / "dataset_manifest.json", {"completeness": completeness.manifest, "finance_hardset": hardset.manifest})
    _write_json(run_dir / "ranking_table.json", ranking_table)
    _write_json(run_dir / "sufficiency_table.json", sufficiency_table)
    _write_json(run_dir / "metrics.json", {"ranking": ranking_table, "sufficiency": sufficiency_table})
    (run_dir / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in all_predictions), encoding="utf-8")
    (run_dir / "per_query_trace.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, default=_json_default) + "\n" for row in trace_lines), encoding="utf-8")
    failures = [row for row in trace_lines if not row["final"]["complete"]]
    (run_dir / "failure_cases.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, default=_json_default) + "\n" for row in failures), encoding="utf-8")
    return run_dir


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    import argparse

    parser = argparse.ArgumentParser(description="Run the bounded P0-B/P0-C experiment sprint.")
    parser.add_argument("--config", default="configs/p0_bc_cpu.json")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    config = json.loads(config_path.read_text(encoding="utf-8"))
    print(run_p0_bc(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
