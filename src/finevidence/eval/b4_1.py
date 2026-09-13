from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import time
from pathlib import Path

from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.contracts.requirements import Requirement, RequirementGraph
from finevidence.evidence.alignment import align_requirement_to_evidence, evaluate_independent_coverage
from finevidence.evidence.pdf_table import extract_pdf_tables, pdf_structure_summary
from finevidence.retrieval.failure_router import predict_failure_route
from finevidence.retrieval.fusion import rrf_fusion
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.visual import ClipImageEncoder, VisualRetriever
from finevidence.eval.b3 import _load_evidence, _ranking_pages


K = (1, 5, 10)
TABLE_FAILURES = {"TABLE_ROW_MIXING", "TABLE_COLUMN_MIXING", "MULTI_LEVEL_HEADER", "UNIT_HEADER_LOSS"}
SYSTEMS = ("T0 Text Only", "T1 Parsed Page Text", "T2 Real Structured Table IR", "V0 Visual Only", "T2 + Text", "Oracle Table Executor")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile(values: list[float], p: int) -> float | str:
    if not values:
        return "N/A"
    return float(values[0]) if len(values) == 1 else float(statistics.quantiles(values, n=100, method="inclusive")[p - 1])


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def table_cell_evidence(table: object, cell: object, *, source_uri: str) -> Evidence:
    """Create qualified evidence whose text includes row/column context."""
    cells = getattr(table, "cells", ())
    row_label = next((item.value for item in cells if item.row_index == cell.row_index and item.column_index == 0 and item.value), "")
    column_headers = [item.value for item in cells if item.column_index == cell.column_index and item.is_header and item.value]
    headers = " | ".join(dict.fromkeys((*cell.header_path, *column_headers)))
    parts = [f"table {cell.table_id}", f"row {cell.row_index}", f"column {cell.column_index}"]
    if row_label and row_label != cell.value:
        parts.append(f"row label {row_label}")
    if headers:
        parts.append(f"headers {headers}")
    parts.append(f"value {cell.value or '[blank]'}")
    if cell.unit:
        parts.append(f"unit {cell.unit}")
    if cell.period:
        parts.append(f"period {cell.period}")
    return Evidence.from_content(
        document_id=table.source_document_id, source_uri=source_uri, page=table.source_page,
        block_id=cell.cell_id, modality="table", text="; ".join(parts), evidence_id=cell.cell_id,
        table_id=cell.table_id, row_id=cell.row_id, column_id=cell.column_id,
        bbox=cell.bbox, region_bbox=cell.bbox, region_type="table_cell",
            entity=getattr(cell, "entity", None), metric=getattr(cell, "metric", None), period=getattr(cell, "period", None),
    )


class StructuredTableRetriever:
    """Small deterministic executor over TableIR cells, rows and header paths."""

    backend_name = "deterministic_table_ir_executor"

    def __init__(self) -> None:
        self._evidence: list[Evidence] = []

    def fit(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)

    def search(self, query: str, top_k: int) -> list[RetrievedEvidence]:
        query_tokens = _tokens(query)
        scored = []
        for item in self._evidence:
            tokens = _tokens(item.text)
            overlap = len(query_tokens & tokens) / max(len(query_tokens), 1)
            exact_period = any(token.isdigit() and len(token) == 4 and token in item.text for token in query_tokens)
            score = overlap + (0.05 if exact_period else 0.0)
            scored.append((score, item))
        scored.sort(key=lambda pair: (-pair[0], pair[1].evidence_id))
        return [RetrievedEvidence(evidence_id=item.evidence_id, rank=rank, retrieval_score=float(score)) for rank, (score, item) in enumerate(scored[:top_k], 1)]


def structure_metrics(tables: list[object]) -> dict:
    if not tables:
        return {"table_count": 0, "page_count": 0, "table_parse_success": 0.0, "structure_recoverable_rate": 0.0, "cell_identity_preservation": "N/A", "row_column_relation": "N/A", "header_recovery": "N/A", "unit_association": "N/A", "human_verified_cell_accuracy": "N/A"}
    summary = pdf_structure_summary(tables)
    return {"table_count": summary["table_count"], "page_count": summary["page_count"], "table_parse_success": 1.0, "structure_recoverable_rate": summary["cells_with_bbox_rate"], "cell_identity_preservation": 1.0, "row_column_relation": 1.0, "header_recovery": summary["header_path_rate"], "unit_association": "N/A", "human_verified_cell_accuracy": "N/A", "note": "Identity and row/column relations are TableIR invariants; semantic cell correctness has no verified human gold."}


def _qualified(row: dict, ranking: list[str], by_id: dict[str, Evidence], table_ids_by_page: dict[str, set[str]]) -> tuple[float, bool, list[str]]:
    target = row["positive_evidence_id"]
    acceptable = [target, target.replace(":image", ":page")]
    gold_page = f"{row['document_id']}:p{row['gold_page']}"
    acceptable.extend(table_ids_by_page.get(gold_page, set()))
    requirement = Requirement(requirement_id="R1", description=row["question"], fact_type="RETRIEVED_FACT", role="table_target", criticality="CRITICAL", acceptable_evidence_ids=acceptable, evidence_role="VALUE_SUPPORT")
    result = evaluate_independent_coverage(RequirementGraph(requirements=[requirement]), [align_requirement_to_evidence(requirement, by_id[item]) for item in ranking if item in by_id], set(ranking))
    return result.critical_coverage, result.answer_eligible, result.warnings


def _rank_metrics(rows: list[dict], rankings: dict[str, list[str]], by_id: dict[str, Evidence]) -> dict:
    result = {}
    for k in K:
        result[str(k)] = sum(f"{row['document_id']}:p{row['gold_page']}" in _ranking_pages(rankings[row["case_id"]], by_id)[:k] for row in rows) / len(rows) if rows else "N/A"
    reciprocal = []
    ndcg = []
    for row in rows:
        pages = _ranking_pages(rankings[row["case_id"]], by_id)
        gold = f"{row['document_id']}:p{row['gold_page']}"
        reciprocal.append(1 / (pages.index(gold) + 1) if gold in pages else 0.0)
        ndcg.append(sum((1.0 if page == gold else 0.0) / math.log2(index + 2) for index, page in enumerate(pages[:10])))
    return {"page_recall_at_1": result["1"], "page_recall_at_5": result["5"], "page_recall_at_10": result["10"], "mrr": sum(reciprocal) / len(reciprocal) if reciprocal else "N/A", "ndcg_at_10": sum(ndcg) / len(ndcg) if ndcg else "N/A"}


def _recovery(rows: list[dict], base: dict[str, list[str]], candidate: dict[str, list[str]], by_id: dict[str, Evidence], table_ids_by_page: dict[str, set[str]]) -> dict:
    output = {}
    for k in K:
        base_fail = recovered = regression = critical_fail = critical_recovered = 0
        for row in rows:
            gold = f"{row['document_id']}:p{row['gold_page']}"
            base_hit = gold in _ranking_pages(base[row["case_id"]], by_id)[:k]
            candidate_hit = gold in _ranking_pages(candidate[row["case_id"]], by_id)[:k]
            base_ok = _qualified(row, base[row["case_id"]][:k], by_id, table_ids_by_page)[1]
            candidate_ok = _qualified(row, candidate[row["case_id"]][:k], by_id, table_ids_by_page)[1]
            base_fail += not base_hit
            recovered += not base_hit and candidate_hit
            regression += base_hit and not candidate_hit
            critical_fail += not base_ok
            critical_recovered += not base_ok and candidate_ok
        output[str(k)] = {"base_failure_count": base_fail, "recovered_cases": recovered, "recovery_rate": recovered / base_fail if base_fail else "N/A", "regression_cases": regression, "regression_rate": regression / len(rows) if rows else "N/A", "critical_failure_count": critical_fail, "critical_recovered_cases": critical_recovered, "critical_recovery_rate": critical_recovered / critical_fail if critical_fail else "N/A", "net_recovery": recovered - regression}
    return output


def _qualification_average(rows: list[dict], rankings: dict[str, list[str]], by_id: dict[str, Evidence], table_ids_by_page: dict[str, set[str]]) -> dict:
    values = [_qualified(row, rankings[row["case_id"]][:10], by_id, table_ids_by_page) for row in rows]
    return {"independent_critical_coverage": sum(value[0] for value in values) / len(values) if values else "N/A", "answer_eligible_rate": sum(value[1] for value in values) / len(values) if values else "N/A"}


def run_b4_1(config: dict) -> dict:
    project_root = Path(__file__).resolve().parents[3]
    render_path = project_root / config.get("render_manifest", "artifacts/hsbc_page_images/page_render_manifest.json")
    stress_path = project_root / config.get("stress_cases", "benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    evidence_path = project_root / config.get("hsbc_evidence", "artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    rows = [json.loads(line) for line in stress_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence, by_id = _load_evidence(json.loads(render_path.read_text(encoding="utf-8")), evidence_path)
    text_items = [item for item in evidence if item.modality == "text"]
    text0 = HybridRetriever(alpha=0.7); text0.fit(text_items)
    text1 = HybridRetriever(alpha=0.45); text1.fit(text_items)

    table_pdf = project_root / config.get("table_pdf", "artifacts/hsbc_local_sources/01-hsbc-fy2025-annual-report.pdf")
    table_pages = range(1, int(config.get("table_page_limit", 26)) + 1)
    parse_start = time.perf_counter(); tables = extract_pdf_tables(table_pdf, pages=table_pages); parse_ms = (time.perf_counter() - parse_start) * 1000
    table_evidence: list[Evidence] = []
    table_ids_by_page: dict[str, set[str]] = {}
    table_records = []
    table_document_id = config.get("table_document_id", "hsbc-fy2025-annual-report")
    for table in tables:
        # The download filename has a numeric prefix, while the frozen HSBC
        # evidence manifest uses its stable document identifier.
        table = table.model_copy(update={"source_document_id": table_document_id, "cells": tuple(cell.model_copy(update={"source_document_id": table_document_id}) for cell in table.cells)})
        page_key = f"{table.source_document_id}:p{table.source_page}"
        table_ids_by_page.setdefault(page_key, set())
        table_records.append(table.model_dump())
        for cell in table.cells:
            item = table_cell_evidence(table, cell, source_uri=table_pdf.as_uri())
            table_evidence.append(item); by_id[item.evidence_id] = item; table_ids_by_page[page_key].add(item.evidence_id)
    structured = StructuredTableRetriever(); structured.fit(table_evidence)

    legacy_ids = {item_id for row in rows for item_id in row["candidate_evidence_ids"]}
    images = [item for item in evidence if item.modality == "image" and item.evidence_id in legacy_ids]
    visual = None; visual_manifest = {"status": "N/A", "reason": "not attempted"}; visual_index_ms = 0.0
    try:
        encoder = ClipImageEncoder(model_path=str(project_root / "artifacts/models"), device=config.get("device", "cpu"))
        visual_manifest = encoder.manifest(); visual = VisualRetriever(encoder)
        start = time.perf_counter(); visual.fit(images); visual_index_ms = (time.perf_counter() - start) * 1000
    except Exception as exc:
        visual_manifest["reason"] = f"{type(exc).__name__}: {exc}"

    rankings = {name: {} for name in SYSTEMS}; traces = []; failures = []
    latency = {name: [] for name in ("text_retrieval", "parsed_page_retrieval", "structured_table_retrieval", "visual_retrieval", "fusion", "routing", "evidence_qualification", "end_to_end")}
    for row in rows:
        case_start = time.perf_counter(); q = row["question"]; cid = row["case_id"]
        start = time.perf_counter(); t0 = [item.evidence_id for item in text0.search(q, 50)]; latency["text_retrieval"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); t1 = [item.evidence_id for item in text1.search(q, 50)]; latency["parsed_page_retrieval"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); t2_items = structured.search(q, 50); t2 = [item.evidence_id for item in t2_items]; latency["structured_table_retrieval"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); v0 = [item.evidence_id for item in (visual.search(q, 50) if visual and visual.available else [])]; latency["visual_retrieval"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); fused = [item.evidence_id for item in rrf_fusion(text1.search(q, 50), t2_items, top_k=50)]; latency["fusion"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); initial_coverage, initial_eligible, initial_warnings = _qualified(row, t1[:10], by_id, table_ids_by_page); latency["evidence_qualification"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); predicted_route = predict_failure_route(q, initial_coverage=initial_coverage, parser_has_table_ir=bool(tables)); latency["routing"].append((time.perf_counter() - start) * 1000)
        oracle = t2 if row.get("category") in TABLE_FAILURES else t0
        route_map = {"T0 Text Only": t0, "T1 Parsed Page Text": t1, "T2 Real Structured Table IR": t2, "V0 Visual Only": v0, "T2 + Text": fused, "Oracle Table Executor": oracle}
        for name, ranking in route_map.items(): rankings[name][cid] = ranking
        qualification = {}
        for name, ranking in route_map.items():
            start = time.perf_counter(); coverage, eligible, warnings = _qualified(row, ranking[:10], by_id, table_ids_by_page); qualification[name] = {"independent_critical_coverage": float(coverage), "answer_eligible": eligible, "warnings": warnings}; latency["evidence_qualification"].append((time.perf_counter() - start) * 1000)
        gold = f"{row['document_id']}:p{row['gold_page']}"
        t1_hit = gold in _ranking_pages(t1, by_id)[:10]; t2_hit = gold in _ranking_pages(t2, by_id)[:10]
        t1_ok = qualification["T1 Parsed Page Text"]["answer_eligible"]; t2_ok = qualification["T2 Real Structured Table IR"]["answer_eligible"]
        failure = {"case_id": cid, "category": row.get("category", "UNKNOWN"), "text_failed": not t1_hit, "structured_recovered": not t1_hit and t2_hit, "critical_recovered": not t1_ok and t2_ok, "regression": t1_hit and not t2_hit, "t2_table_available_on_gold_page": bool(table_ids_by_page.get(gold))}
        failures.append(failure)
        traces.append({"case_id": cid, "question": q, "category": row.get("category"), "gold_page": gold, "t0_candidates": t0, "t1_candidates": t1, "t2_candidates": t2, "v0_candidates": v0, "t2_text_candidates": fused, "oracle_candidates": oracle, "initial_critical_coverage": float(initial_coverage), "initial_answer_eligible": initial_eligible, "initial_warnings": initial_warnings, "predicted_route": predicted_route.model_dump(), "qualification": qualification, "latency_ms": {"end_to_end": (time.perf_counter() - case_start) * 1000}})
        latency["end_to_end"].append((time.perf_counter() - case_start) * 1000)

    metrics = {"systems": {name: {**_rank_metrics(rows, rankings[name], by_id), **_qualification_average(rows, rankings[name], by_id, table_ids_by_page), "table_failure_recovery": _recovery([row for row in rows if row.get("category") in TABLE_FAILURES], rankings["T1 Parsed Page Text"], rankings[name], by_id, table_ids_by_page)} for name in SYSTEMS}, "table_failure_categories": sorted(TABLE_FAILURES), "failure_counts": {category: sum(item["category"] == category for item in failures) for category in sorted({item["category"] for item in failures})}, "oracle_after_structured_executor": {"table_cases": sum(row.get("category") in TABLE_FAILURES for row in rows), "executor_used_for_table_categories": True}, "predicted_route": {"status": "observed_only", "reason": "Existing heuristic route was measured but not promoted as a causal improvement."}, "structure_fidelity": structure_metrics(tables)}
    latency_metrics = {name: {"p50_ms": _percentile(values, 50), "p95_ms": _percentile(values, 95)} for name, values in latency.items()}
    latency_metrics["offline_indexing"] = {"pdf_table_extraction_ms": parse_ms, "pdf_table_extraction_pages": int(config.get("table_page_limit", 26)), "visual_indexing_ms": visual_index_ms, "visual_pages_indexed": len(images)}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root, text=True).strip()
    return {"config": {**config, "code_commit": commit, "systems": SYSTEMS, "retrieval_cutoffs": K, "structured_backend": StructuredTableRetriever.backend_name}, "visual_model": visual_manifest, "dataset": {"name": "HSBCVisualStress-v1", "case_count": len(rows), "cases_sha256": _sha256(stress_path), "render_manifest_sha256": _sha256(render_path), "evidence_sha256": _sha256(evidence_path), "table_pdf_sha256": _sha256(table_pdf), "table_page_scope": [1, int(config.get("table_page_limit", 26))]}, "table_ir": table_records, "metrics": metrics, "latency_metrics": latency_metrics, "failures": failures, "traces": traces, "rankings": rankings, "claims": {"verified_structured_table_ir": "N/A", "semantic_cell_accuracy": "N/A", "bbox_grounding": "N/A", "table_ir_is_real_pdf_geometry_extraction": True}}


def write_run(result: dict, artifact_root: Path) -> Path:
    artifact_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S"); run = artifact_root / stamp; suffix = 0
    while run.exists():
        suffix += 1; run = artifact_root / f"{stamp}-{suffix}"
    run.mkdir()
    for name, value in (("config.json", result["config"]), ("model_manifest.json", result["visual_model"]), ("dataset_manifest.json", result["dataset"]), ("metrics.json", result["metrics"]), ("latency_metrics.json", result["latency_metrics"]), ("structure_fidelity.json", result["metrics"]["structure_fidelity"]), ("per_failure_type_metrics.json", result["metrics"]["failure_counts"]), ("claims.json", result["claims"])):
        (run / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, items in (("table_ir.jsonl", result["table_ir"]), ("failure_cases.jsonl", result["failures"]), ("per_query_trace.jsonl", result["traces"])):
        (run / name).write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf-8")
    for system, items in result["rankings"].items():
        filename = system.lower().replace(" ", "_").replace("+", "plus").replace("/", "_") + "_predictions.jsonl"
        (run / filename).write_text("".join(json.dumps({"case_id": case_id, "ranking": ranking}) + "\n" for case_id, ranking in items.items()), encoding="utf-8")
    return run


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(); parser.add_argument("--config", default="configs/b4_1_cpu.json"); args = parser.parse_args()
    config_path = project_root / args.config if not Path(args.config).is_absolute() else Path(args.config)
    result = run_b4_1(json.loads(config_path.read_text(encoding="utf-8")))
    run = write_run(result, project_root / result["config"].get("artifact_root", "artifacts/b4_1_runs"))
    print(json.dumps({"run": str(run.resolve()), "table_count": result["metrics"]["structure_fidelity"]["table_count"], "t2_page_recall_at_10": result["metrics"]["systems"]["T2 Real Structured Table IR"]["page_recall_at_10"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
