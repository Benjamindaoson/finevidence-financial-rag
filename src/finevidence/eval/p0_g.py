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
from finevidence.contracts.requirements import FactEvidenceAlignment, Requirement, RequirementGraph
from finevidence.eval.metrics import fact_decomposition_metrics, oracle_gap
from finevidence.eval.run import _git_commit
from finevidence.evidence.alignment import align_requirement_to_evidence, evaluate_independent_coverage
from finevidence.evidence.fact_understanding import classify_question, decompose_required_facts_by_variant
from finevidence.evidence.requirement_graph import decompose_requirement_graph
from finevidence.retrieval.hybrid import HybridRetriever


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _gold_graph(case: MiniCase) -> RequirementGraph:
    facts = [fact for fact in case.required_facts if isinstance(fact, FactRequirement)]
    return RequirementGraph(
        requirements=[
            Requirement(
                requirement_id=fact.fact_id,
                description=fact.description,
                fact_type="RETRIEVED_FACT",
                role=f"gold_fact_{index}",
                criticality="CRITICAL",
                acceptable_evidence_ids=fact.acceptable_evidence_ids,
            )
            for index, fact in enumerate(facts, start=1)
        ],
        edges=[],
    )


def _flat_graph(result) -> RequirementGraph:
    requirements = []
    for fact in result.facts:
        slots = fact.slots
        requirements.append(
            Requirement(
                requirement_id=fact.fact_id,
                description=fact.description,
                fact_type="RETRIEVED_FACT",
                role=slots.role if slots else "predicted_fact",
                entity=slots.entity if slots else None,
                metric=slots.metric if slots else None,
                period=slots.period if slots else None,
                segment=slots.segment if slots else None,
                basis=slots.basis if slots else None,
                criticality="CRITICAL" if not slots or slots.critical else "SUPPORTING",
                acceptable_evidence_ids=fact.acceptable_evidence_ids,
            )
        )
    return RequirementGraph(requirements=requirements, edges=[])


def _align_graph(graph: RequirementGraph, selected_ids: set[str], evidence_by_id: dict) -> list[FactEvidenceAlignment]:
    alignments = []
    for requirement in graph.requirements:
        if requirement.fact_type == "DERIVED_FACT":
            continue
        for evidence_id in sorted(selected_ids):
            if evidence_id not in evidence_by_id:
                continue
            alignments.append(align_requirement_to_evidence(requirement, evidence_by_id[evidence_id]))
    return alignments


def _retrieve(graph: RequirementGraph, question: str, hybrid: HybridRetriever, evidence_by_id: dict, top_k: int, max_rounds: int):
    selected: set[str] = set()
    initial_selected: set[str] = set()
    queries = []
    query = question
    final_coverage = None
    final_alignments: list[FactEvidenceAlignment] = []
    for round_number in range(max_rounds + 1):
        queries.append(query)
        round_ids = {item.evidence_id for item in hybrid.search(query, top_k)}
        selected.update(round_ids)
        if round_number == 0:
            initial_selected = set(round_ids)
        final_alignments = _align_graph(graph, selected, evidence_by_id)
        final_coverage = evaluate_independent_coverage(graph, final_alignments, selected)
        if final_coverage.answer_eligible or round_number >= max_rounds:
            break
        missing = next((graph.requirement(item) for item in final_coverage.missing_critical_requirements), None)
        if missing is None:
            break
        query = f"{question} Evidence needed: {missing.description}"
    assert final_coverage is not None
    return initial_selected, selected, final_alignments, final_coverage, queries


def _coverage_metrics(results: list) -> dict[str, float | str]:
    def mean(field: str) -> float:
        return sum(getattr(item, field) for item in results) / len(results) if results else 0.0

    return {
        "raw_self_coverage": mean("raw_self_coverage"),
        "independent_cer": mean("independent_coverage"),
        "critical_coverage": mean("critical_coverage"),
        "critical_missing_rate": mean("critical_missing_rate"),
        "evidence_reuse_rate": mean("evidence_reuse_rate"),
        "invalid_reuse_rate": mean("invalid_reuse_rate"),
        "answer_eligible_rate": mean("answer_eligible"),
        "faer": sum(item.raw_self_coverage == 1.0 and not item.answer_eligible for item in results) / len(results) if results else "N/A",
    }


def _failure_types(graph: RequirementGraph, coverage, gold_count: int) -> list[str]:
    failures = []
    if len(graph.requirements) < gold_count:
        failures.append("PREDICTED_REQUIREMENTS_UNDER_SPECIFIED")
    if "EVIDENCE_REUSE_INFLATION" in coverage.warnings:
        failures.append("EVIDENCE_REUSE_INFLATION")
    if coverage.missing_critical_requirements:
        failures.append("CRITICAL_FACT_MISSING")
    if not coverage.answer_eligible:
        failures.append("EVIDENCE_MAPPING_FAILURE")
    return failures


def run_p0_g(config: dict) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    slice_root = Path(config.get("slice_root", project_root / "benchmarks/real_finance_v1"))
    if not slice_root.is_absolute():
        slice_root = project_root / slice_root
    if not (slice_root / "manifest.json").exists():
        build_real_finance_slice(project_root.parent / "research/repos/tat-qa/dataset_raw/tatqa_dataset_dev.json", project_root.parent / "research/repos/FinQA/dataset/dev.json", slice_root, 50, 50)
    benchmark = load_benchmark(slice_root)
    artifact_root = Path(config.get("artifact_root", project_root / "artifacts/p0_g_runs"))
    if not artifact_root.is_absolute():
        artifact_root = project_root / artifact_root
    run_dir = artifact_root / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=False)
    top_k = int(config.get("top_k", 5))
    max_rounds = min(int(config.get("max_rounds", 2)), 2)
    hybrid = HybridRetriever()
    hybrid.fit(benchmark.evidence)
    evidence_by_id = {item.evidence_id: item for item in benchmark.evidence}
    methods = (("D0", "D0 Heuristic"), ("D1", "D1 LLM Direct"), ("D2", "D2 Schema-constrained"), ("D3", "D3 Evidence-aware"), ("D4", "D4 Requirement-Graph-Constrained"))
    alignment_rows: dict[str, list] = {label: [] for _, label in methods}
    understanding_rows: dict[str, list] = {label: [] for _, label in methods}
    traces, predictions, graph_rows, alignment_artifacts, failure_rows = [], [], [], [], []
    gold_coverage = []
    for case in benchmark.cases:
        gold_graph = _gold_graph(case)
        gold_initial, gold_selected, gold_alignments, gold_result, gold_queries = _retrieve(gold_graph, case.question, hybrid, evidence_by_id, top_k, max_rounds)
        gold_coverage.append(gold_result)
        graph_rows.append({"question_id": case.question_id, "method": "Gold", "graph": gold_graph.model_dump()})
        alignment_artifacts.append({"question_id": case.question_id, "method": "Gold", "initial_evidence": sorted(gold_initial), "final_evidence": sorted(gold_selected), "alignments": [item.model_dump() for item in gold_alignments], "coverage": gold_result.model_dump(), "targeted_queries": gold_queries})
        for variant, label in methods:
            if variant == "D4":
                graph = decompose_requirement_graph(case.question)
                result = None
            else:
                candidates = [(item.evidence_id, evidence_by_id[item.evidence_id].text) for item in hybrid.search(case.question, top_k)] if variant == "D3" else None
                result = decompose_required_facts_by_variant(case.question, variant, candidates)
                graph = _flat_graph(result) if result.status == "READY" else None
            if graph is None:
                understanding_rows[label].append({"status": "N/A", "reason": result.reason, "fact_precision": "N/A", "fact_recall": "N/A", "critical_fact_recall": "N/A", "requirement_count_error": "N/A", "requirement_type_accuracy": "N/A", "slot_accuracy": "N/A"})
                predictions.append({"question_id": case.question_id, "method": label, "status": "N/A", "reason": result.reason})
                traces.append({"question_id": case.question_id, "method": label, "status": "N/A", "reason": result.reason})
                continue
            if variant == "D4":
                predicted_facts = [FactRequirement(fact_id=item.requirement_id, description=item.description, acceptable_evidence_ids=item.acceptable_evidence_ids or ["__unresolved__"]) for item in graph.requirements]
            else:
                predicted_facts = result.facts
            initial_selected, selected, alignments, coverage, queries = _retrieve(graph, case.question, hybrid, evidence_by_id, top_k, max_rounds)
            lexical = fact_decomposition_metrics(case, predicted_facts)
            understanding_rows[label].append({
                "status": "READY",
                "fact_precision": lexical["required_fact_precision"],
                "fact_recall": lexical["required_fact_recall"],
                "critical_fact_recall": "N/A",
                "requirement_count_error": abs(len(graph.requirements) - len(gold_graph.requirements)),
                "requirement_type_accuracy": "N/A",
                "slot_accuracy": "N/A",
            })
            alignment_rows[label].append(coverage)
            warning_list = list(coverage.warnings)
            if len(graph.requirements) < len(gold_graph.requirements):
                warning_list.append("PREDICTED_REQUIREMENTS_UNDER_SPECIFIED")
            trace = {
                "question": case.question,
                "question_id": case.question_id,
                "question_type": classify_question(case.question),
                "method": label,
                "gold_requirements": [item.model_dump() for item in gold_graph.requirements],
                "predicted_requirements": [item.model_dump() for item in graph.requirements],
                "requirement_graph": graph.model_dump(),
                "initial_evidence": sorted(initial_selected),
                "fact_evidence_alignments": [item.model_dump() for item in alignments],
                "invalid_reuse_events": [item.model_dump() for item in coverage.invalid_reuse_events],
                "critical_missing_requirements": coverage.missing_critical_requirements,
                "targeted_queries": queries,
                "final_evidence": sorted(selected),
                "raw_self_coverage": coverage.raw_self_coverage,
                "independent_coverage": coverage.independent_coverage,
                "critical_coverage": coverage.critical_coverage,
                "answer_eligible": coverage.answer_eligible,
                "warnings": warning_list,
                "failure_types": _failure_types(graph, coverage, len(gold_graph.requirements)),
            }
            traces.append(trace)
            predictions.append({"question_id": case.question_id, "method": label, "status": "READY", "question_type": trace["question_type"], "requirements": [item.model_dump() for item in graph.requirements]})
            graph_rows.append({"question_id": case.question_id, "method": label, "graph": graph.model_dump()})
            alignment_artifacts.append({
                "question_id": case.question_id,
                "method": label,
                "alignments": [item.model_dump() for item in alignments],
                "invalid_reuse_events": [item.model_dump() for item in coverage.invalid_reuse_events],
                "warnings": coverage.warnings,
            })
            alignment_rows[label][-1] = coverage
            if trace["failure_types"]:
                failure_rows.append(trace)
    gold_final_cer = sum(item.independent_coverage for item in gold_coverage) / len(gold_coverage)
    gold_critical_coverage = sum(item.critical_coverage for item in gold_coverage) / len(gold_coverage)
    variants = {}
    for _, label in methods:
        if not alignment_rows[label]:
            variants[label] = {"status": "N/A", "reason": "LLM_PROVIDER_NOT_CONFIGURED", "oracle_gap": "N/A"}
            continue
        coverage = _coverage_metrics(alignment_rows[label])
        understanding = {key: _mean_or_na(understanding_rows[label], key) for key in ("fact_precision", "fact_recall", "critical_fact_recall", "requirement_count_error", "requirement_type_accuracy", "slot_accuracy")}
        variants[label] = {"status": "READY", **understanding, **coverage, "oracle_gap": oracle_gap(gold_final_cer, coverage["independent_cer"]), "critical_coverage_gap": gold_critical_coverage - coverage["critical_coverage"]}
        if isinstance(variants[label]["oracle_gap"], (int, float)) and variants[label]["oracle_gap"] < 0:
            variants[label]["warnings"] = ["PREDICTED_REQUIREMENTS_UNDER_SPECIFIED", "EVIDENCE_REUSE_INFLATION"]
    metrics = {
        "dataset_type": "public_benchmark_slice",
        "source_splits": {dataset: sum(case.source_dataset == dataset for case in benchmark.cases) for dataset in ("TAT-QA", "FinQA")},
        "gold_independent_cer": gold_final_cer,
        "alignment": {"Gold": {"status": "READY", "independent_cer": gold_final_cer, "critical_coverage": gold_critical_coverage, "faer": 0.0}, **variants},
        "oracle_gap_definition": "gold_independent_cer - predicted_independent_cer",
    }
    _write_json(run_dir / "config.json", {**config, "git_commit": _git_commit(project_root), "runtime": {"python": sys.version, "platform": platform.platform()}})
    _write_json(run_dir / "dataset_manifest.json", benchmark.manifest)
    _write_json(run_dir / "metrics.json", metrics)
    (run_dir / "predictions.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, default=str) + "\n" for item in predictions), encoding="utf-8")
    (run_dir / "per_query_trace.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, default=str) + "\n" for item in traces), encoding="utf-8")
    (run_dir / "requirement_graphs.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, default=str) + "\n" for item in graph_rows), encoding="utf-8")
    (run_dir / "alignment_results.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, default=str) + "\n" for item in alignment_artifacts), encoding="utf-8")
    (run_dir / "failure_cases.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, default=str) + "\n" for item in failure_rows), encoding="utf-8")
    return run_dir


def _mean_or_na(rows: list[dict], key: str) -> float | str:
    values = [row[key] for row in rows if isinstance(row.get(key), (int, float))]
    return sum(values) / len(values) if values else "N/A"


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Run P0-G requirement graph and independent evidence coverage evaluation.")
    parser.add_argument("--config", default="configs/p0_g_cpu.json")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    print(run_p0_g(json.loads(config_path.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
