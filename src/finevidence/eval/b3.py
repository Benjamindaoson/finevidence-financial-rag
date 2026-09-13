from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import subprocess
import time
from pathlib import Path

from finevidence.contracts.b3 import CitationResult
from finevidence.contracts.evidence import Evidence
from finevidence.contracts.requirements import Requirement, RequirementGraph
from finevidence.evidence.alignment import align_requirement_to_evidence, evaluate_independent_coverage
from finevidence.retrieval.fusion import rrf_fusion, weighted_fusion
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.routing import route_query
from finevidence.retrieval.visual import ClipImageEncoder, VisualRetriever


SYSTEMS = ("T0 Text Only", "T1 Parsed Page Text", "V0 Visual Only", "M0 Fusion RRF", "M0 Fusion Weighted", "M1 Conditional Multimodal")
RECOVERY_K = (1, 5, 10)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile(values: list[float], percentile: float) -> float | str:
    if not values:
        return "N/A"
    return float(statistics.quantiles(values, n=100, method="inclusive")[max(0, min(99, int(percentile) - 1))]) if len(values) > 1 else float(values[0])


def _page_for(evidence_id: str, by_id: dict[str, Evidence]) -> str | None:
    return f"{by_id[evidence_id].document_id}:p{by_id[evidence_id].page}" if evidence_id in by_id else None


def _ranking_pages(ranking: list[str], by_id: dict[str, Evidence]) -> list[str]:
    pages = []
    for evidence_id in ranking:
        page = _page_for(evidence_id, by_id)
        if page and page not in pages:
            pages.append(page)
    return pages


def _rank_metrics(rows: list[dict], rankings: dict[str, list[str]], by_id: dict[str, Evidence]) -> dict:
    if not rows:
        return {"page_recall_at_1": "N/A", "page_recall_at_5": "N/A", "page_recall_at_10": "N/A", "mrr": "N/A", "ndcg_at_10": "N/A"}
    recalls = {k: [] for k in RECOVERY_K}
    mrr, ndcg = [], []
    for row in rows:
        gold = f"{row['document_id']}:p{row['gold_page']}"
        pages = _ranking_pages(rankings[row["case_id"]], by_id)
        for k in recalls:
            recalls[k].append(float(gold in pages[:k]))
        ranks = [index + 1 for index, page in enumerate(pages) if page == gold]
        mrr.append(1.0 / ranks[0] if ranks else 0.0)
        gains = [1.0 if page == gold else 0.0 for page in pages[:10]]
        ndcg.append(sum(gain / math.log2(index + 2) for index, gain in enumerate(gains)))
    return {"page_recall_at_1": sum(recalls[1]) / len(rows), "page_recall_at_5": sum(recalls[5]) / len(rows), "page_recall_at_10": sum(recalls[10]) / len(rows), "mrr": sum(mrr) / len(rows), "ndcg_at_10": sum(ndcg) / len(rows)}


def _citation(row: dict, ranking: list[str], by_id: dict[str, Evidence]) -> CitationResult:
    gold = {f"{row['document_id']}:p{row['gold_page']}"}
    predicted = set(_ranking_pages(ranking[:5], by_id))
    precision = len(predicted & gold) / len(predicted) if predicted else 0.0
    recall = len(predicted & gold) / len(gold)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return CitationResult(predicted_page_ids=sorted(predicted), gold_page_ids=sorted(gold), page_precision=precision, page_recall=recall, page_f1=f1)


def _qualified(row: dict, ranking: list[str], by_id: dict[str, Evidence]) -> tuple[float, bool, list[str]]:
    target = row["positive_evidence_id"]
    acceptable = [target, target.replace(":image", ":page")]
    requirement = Requirement(requirement_id="R1", description=row["question"], fact_type="RETRIEVED_FACT", role="visual_target", criticality="CRITICAL", acceptable_evidence_ids=acceptable, evidence_role="VALUE_SUPPORT")
    graph = RequirementGraph(requirements=[requirement])
    alignments = [align_requirement_to_evidence(requirement, by_id[item]) for item in ranking if item in by_id]
    result = evaluate_independent_coverage(graph, alignments, set(ranking))
    return result.critical_coverage, result.answer_eligible, result.warnings


def _load_evidence(render_manifest: dict, hsbc_evidence_path: Path) -> tuple[list[Evidence], dict[str, Evidence]]:
    page_rows = {(item["document_id"], item["page"]): item for item in render_manifest["pages"]}
    text_rows = [json.loads(line) for line in hsbc_evidence_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence = []
    for raw in text_rows:
        page = page_rows.get((raw["document_id"], raw["page"]))
        if not page:
            continue
        image = Evidence.from_content(document_id=raw["document_id"], source_uri=raw["source_uri"], page=raw["page"], block_id=f"image-{raw['page']}", modality="image", text=raw["text"], evidence_id=raw["evidence_id"].replace(":page", ":image"), image_path=page["image_path"], page_image_id=page["page_image_id"], render_hash=page["image_sha256"], bbox=None, region_bbox=None, region_type="page")
        text = Evidence.from_content(document_id=raw["document_id"], source_uri=raw["source_uri"], page=raw["page"], block_id=raw["block_id"], modality="text", text=raw["text"], evidence_id=raw["evidence_id"])
        evidence.extend((text, image))
    return evidence, {item.evidence_id: item for item in evidence}


def _recovery_metrics(rows: list[dict], t0: dict[str, list[str]], m1: dict[str, list[str]], by_id: dict[str, Evidence]) -> dict:
    result = {}
    for k in RECOVERY_K:
        text_failed = recovered = critical_failed = critical_recovered = regressions = 0
        for row in rows:
            gold_page = f"{row['document_id']}:p{row['gold_page']}"
            text_hit = gold_page in _ranking_pages(t0[row["case_id"]][:k], by_id)
            final_hit = gold_page in _ranking_pages(m1[row["case_id"]][:k], by_id)
            text_eligible = _qualified(row, t0[row["case_id"]][:k], by_id)[1]
            final_eligible = _qualified(row, m1[row["case_id"]][:k], by_id)[1]
            text_failed += not text_hit
            recovered += not text_hit and final_hit
            critical_failed += not text_eligible
            critical_recovered += not text_eligible and final_eligible
            regressions += text_hit and not final_hit
        result[str(k)] = {"text_failure_count": text_failed, "text_failure_recovery_rate": recovered / text_failed if text_failed else "N/A", "visual_critical_requirement_recovery_rate": critical_recovered / critical_failed if critical_failed else "N/A", "multimodal_regression_rate": regressions / len(rows) if rows else "N/A", "net_recovery": recovered - regressions, "recovered_cases": recovered, "regression_cases": regressions}
    return result


def _routing_metrics(rows: list[dict], traces: list[dict], failure_rows: list[dict]) -> dict:
    if not rows:
        return {"case_count": 0}
    gold_visual = [row["gold_route"] in {"VISUAL", "MIXED"} for row in rows]
    invoked = [bool(item["visual_invoked"]) for item in traces]
    tp = sum(a and b for a, b in zip(invoked, gold_visual))
    fp = sum(a and not b for a, b in zip(invoked, gold_visual))
    fn = sum((not a) and b for a, b in zip(invoked, gold_visual))
    ids = {row["case_id"] for row in rows}
    routing_failures = [item for item in failure_rows if item["case_id"] in ids]
    return {"case_count": len(rows), "class_counts": {label: sum(row["routing_class"] == label for row in rows) for label in {row["routing_class"] for row in rows}}, "routing_precision": tp / (tp + fp) if tp + fp else "N/A", "routing_recall": tp / (tp + fn) if tp + fn else "N/A", "visual_invocation_rate": sum(invoked) / len(invoked), "unnecessary_visual_invocation_rate": fp / sum(not item for item in gold_visual) if sum(not item for item in gold_visual) else "N/A", "critical_requirement_recovery_rate": sum(item["critical_recovered"] for item in routing_failures) / sum(not item["text_critical"] for item in routing_failures) if sum(not item["text_critical"] for item in routing_failures) else "N/A", "multimodal_regression_rate": sum(item["regression"] for item in routing_failures) / len(routing_failures) if routing_failures else "N/A", "net_recovery": sum(item["visual_recovered"] for item in routing_failures) - sum(item["regression"] for item in routing_failures)}


def run_b3(config: dict) -> dict:
    project_root = Path(__file__).resolve().parents[3]
    render_path = project_root / config.get("render_manifest", "artifacts/hsbc_page_images/page_render_manifest.json")
    stress_path = project_root / config.get("stress_cases", "benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    routing_path = project_root / config.get("routing_cases", "benchmarks/hsbc_multimodal_routing_v1/questions.jsonl")
    evidence_path = project_root / config.get("hsbc_evidence", "artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    render_manifest = json.loads(render_path.read_text(encoding="utf-8"))
    stress_cases = [json.loads(line) for line in stress_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    routing_cases = [json.loads(line) for line in routing_path.read_text(encoding="utf-8").splitlines() if line.strip()] if routing_path.exists() else []
    cases = stress_cases + routing_cases
    evidence, by_id = _load_evidence(render_manifest, evidence_path)
    text_evidence = [item for item in evidence if item.modality == "text"]
    candidate_ids = {item_id for row in cases for item_id in row["candidate_evidence_ids"]}
    image_evidence = [item for item in evidence if item.modality == "image" and item.evidence_id in candidate_ids]
    text = HybridRetriever()
    start = time.perf_counter(); text.fit(text_evidence); text_index_ms = (time.perf_counter() - start) * 1000
    structured = HybridRetriever(alpha=0.45)
    start = time.perf_counter(); structured.fit(text_evidence); structured_index_ms = (time.perf_counter() - start) * 1000
    visual = None
    visual_manifest = {"model_name": "N/A", "model_revision": "N/A", "runtime": "N/A", "device": "cpu", "image_encoder": False, "weights_sha256": None, "status": "N/A", "reason": "not attempted"}
    visual_index_ms = 0.0
    try:
        encoder = ClipImageEncoder(model_path=str(project_root / "artifacts/models"), device="cpu")
        visual = VisualRetriever(encoder)
        start = time.perf_counter(); visual.fit(image_evidence); visual_index_ms = (time.perf_counter() - start) * 1000
        visual_manifest = encoder.manifest() if visual.available else {**visual_manifest, "reason": "no rendered image evidence"}
    except Exception as exc:
        visual_manifest["reason"] = f"{type(exc).__name__}: {exc}"
    rankings = {name: {} for name in SYSTEMS}
    traces, failure_rows = [], []
    component_latencies = {name: [] for name in ("text_retrieval", "parsed_page_retrieval", "visual_query_encoding_retrieval", "fusion", "routing", "evidence_qualification", "end_to_end")}
    for row in cases:
        q, case_start = row["question"], time.perf_counter()
        start = time.perf_counter(); t_results = text.search(q, 10); component_latencies["text_retrieval"].append((time.perf_counter() - start) * 1000); t0_ids = [item.evidence_id for item in t_results]
        start = time.perf_counter(); t1_results = structured.search(q, 10); component_latencies["parsed_page_retrieval"].append((time.perf_counter() - start) * 1000); t1_ids = [item.evidence_id for item in t1_results]
        initial_coverage, text_critical, _ = _qualified(row, t0_ids[:10], by_id)
        start = time.perf_counter(); decision = route_query(q, initial_critical_coverage=initial_coverage, parser_confidence=0.8); component_latencies["routing"].append((time.perf_counter() - start) * 1000)
        v_results, v0_ids = [], []
        if visual and visual.available:
            start = time.perf_counter(); v_results = visual.search(q, 10); component_latencies["visual_query_encoding_retrieval"].append((time.perf_counter() - start) * 1000); v0_ids = [item.evidence_id for item in v_results]
        else:
            component_latencies["visual_query_encoding_retrieval"].append(0.0)
        start = time.perf_counter()
        if v0_ids:
            rrf = [item.evidence_id for item in rrf_fusion(t_results, v_results, top_k=10)]
            weighted = [item.evidence_id for item in weighted_fusion(t_results, v_results, top_k=10)]
        else:
            rrf = weighted = t0_ids
        component_latencies["fusion"].append((time.perf_counter() - start) * 1000)
        m1 = rrf if decision.visual_invoked and v0_ids else t0_ids
        start = time.perf_counter(); m1_coverage, m1_critical, qualification_warnings = _qualified(row, m1[:10], by_id); component_latencies["evidence_qualification"].append((time.perf_counter() - start) * 1000)
        for name, ranking in ((SYSTEMS[0], t0_ids), (SYSTEMS[1], t1_ids), (SYSTEMS[2], v0_ids), (SYSTEMS[3], rrf), (SYSTEMS[4], weighted), (SYSTEMS[5], m1)):
            rankings[name][row["case_id"]] = ranking
        gold_page = f"{row['document_id']}:p{row['gold_page']}"
        text_has = gold_page in _ranking_pages(t0_ids[:10], by_id)
        m1_has = gold_page in _ranking_pages(m1[:10], by_id)
        failure_rows.append({"case_id": row["case_id"], "category": row.get("category", row.get("routing_class", "UNKNOWN")), "text_failed": not text_has, "visual_recovered": (not text_has and m1_has), "text_critical": text_critical, "critical_recovered": (not text_critical and m1_critical), "regression": text_has and not m1_has})
        component_snapshot = {name: component_latencies[name][-1] for name in component_latencies if component_latencies[name]}
        component_latencies["end_to_end"].append((time.perf_counter() - case_start) * 1000)
        component_snapshot["end_to_end"] = component_latencies["end_to_end"][-1]
        traces.append({"case_id": row["case_id"], "question": q, "routing_class": row.get("routing_class"), "gold_route": row.get("gold_route"), "requirements": [{"requirement_id": "R1", "description": q, "criticality": "CRITICAL", "modality": "VISUAL"}], "gold_page": gold_page, "text_candidates": t0_ids, "structured_candidates": t1_ids, "initial_critical_coverage": float(initial_coverage), "routing_decision": decision.model_dump(), "visual_invoked": decision.visual_invoked, "visual_candidates": v0_ids, "fusion_candidates": rrf, "final_candidates": m1, "final_critical_coverage": float(m1_coverage), "text_failure_recovered": (not text_has and m1_has), "critical_requirement_recovered": (not text_critical and m1_critical), "multimodal_regression": text_has and not m1_has, "citation_result": _citation(row, m1, by_id).model_dump(), "latency_ms": component_snapshot, "warnings": qualification_warnings})
    metrics = {name: _rank_metrics(stress_cases, ranking, by_id) for name, ranking in rankings.items()}
    metrics["all_cases"] = {name: _rank_metrics(cases, ranking, by_id) for name, ranking in rankings.items()}
    metrics["routing_retrieval"] = {name: _rank_metrics(routing_cases, ranking, by_id) for name, ranking in rankings.items()}
    metrics["b3_recovery"] = _recovery_metrics(stress_cases, rankings[SYSTEMS[0]], rankings[SYSTEMS[5]], by_id)
    metrics["routing_recovery"] = _recovery_metrics(routing_cases, rankings[SYSTEMS[0]], rankings[SYSTEMS[5]], by_id)
    metrics["b3"] = {"case_count": len(stress_cases), "text_only_failure_recovery_rate_at_10": metrics["b3_recovery"]["10"]["text_failure_recovery_rate"], "visual_critical_requirement_recovery_rate_at_10": metrics["b3_recovery"]["10"]["visual_critical_requirement_recovery_rate"], "multimodal_regression_rate_at_10": metrics["b3_recovery"]["10"]["multimodal_regression_rate"], "net_recovery_at_10": metrics["b3_recovery"]["10"]["net_recovery"], "visual_pages_per_query": sum(len(trace["visual_candidates"]) for trace in traces) / len(traces) if traces else 0.0, "peak_gpu_memory_mb": 0.0}
    metrics["routing"] = _routing_metrics(routing_cases, [trace for trace in traces if trace["case_id"].startswith("hsbc-r-")], failure_rows)
    metrics["per_failure_type"] = {category: {name: _rank_metrics([row for row in stress_cases if row.get("category") == category], ranking, by_id)["page_recall_at_5"] for name, ranking in rankings.items()} for category in sorted({row.get("category", "UNKNOWN") for row in stress_cases})}
    latency_metrics = {name: {"p50_ms": _percentile(values, 50), "p95_ms": _percentile(values, 95)} for name, values in component_latencies.items()}
    latency_metrics["offline_indexing"] = {"text_indexing_ms": text_index_ms, "parsed_page_indexing_ms": structured_index_ms, "visual_image_indexing_ms": visual_index_ms, "visual_pages_indexed": len(image_evidence)}
    config = {**config, "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root, text=True).strip(), "recovery_cutoffs": list(RECOVERY_K), "t1_name": "T1 Parsed Page Text", "verified_structured_table_ir": "N/A"}
    return {"config": config, "visual_model": visual_manifest, "case_count": len(cases), "stress_case_count": len(stress_cases), "routing_case_count": len(routing_cases), "evidence_count": len(evidence), "metrics": metrics, "latency_metrics": latency_metrics, "failure_cases": failure_rows, "traces": traces, "rankings": rankings, "citation_bbox": "N/A: no bbox gold in HSBCVisualStress-v1 or HSBCMultimodalRouting-v1", "environment": {"device": "cpu", "cuda": False, "pid": os.getpid()}}


def write_run(result: dict, artifact_root: Path) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    artifact_root.mkdir(parents=True, exist_ok=True)
    run = artifact_root / time.strftime("%Y%m%dT%H%M%S")
    suffix = 0
    while run.exists():
        suffix += 1
        run = artifact_root / f"{time.strftime('%Y%m%dT%H%M%S')}-{suffix}"
    run.mkdir()
    (run / "config.json").write_text(json.dumps(result["config"], indent=2) + "\n", encoding="utf-8")
    (run / "model_manifest.json").write_text(json.dumps(result["visual_model"], indent=2) + "\n", encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(result["metrics"], indent=2) + "\n", encoding="utf-8")
    (run / "latency_metrics.json").write_text(json.dumps(result["latency_metrics"], indent=2) + "\n", encoding="utf-8")
    (run / "failure_cases.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in result["failure_cases"]), encoding="utf-8")
    (run / "per_query_trace.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in result["traces"]), encoding="utf-8")
    (run / "per_failure_type_metrics.json").write_text(json.dumps(result["metrics"].get("per_failure_type", {}), indent=2) + "\n", encoding="utf-8")
    (run / "routing_predictions.jsonl").write_text("".join(json.dumps({"case_id": trace["case_id"], "routing": trace["routing_decision"], "visual_invoked": trace["visual_invoked"], "gold_route": trace.get("gold_route")}) + "\n" for trace in result["traces"]), encoding="utf-8")
    (run / "grounding_predictions.jsonl").write_text("".join(json.dumps({"case_id": trace["case_id"], "gold_page": trace["gold_page"], "citation_result": trace["citation_result"]}) + "\n" for trace in result["traces"]), encoding="utf-8")
    for name, rows in result["rankings"].items():
        filename = name.lower().replace(" ", "_").replace("+", "plus").replace("/", "_") + "_predictions.jsonl"
        (run / filename).write_text("".join(json.dumps({"case_id": case_id, "ranking": ranking}) + "\n" for case_id, ranking in rows.items()), encoding="utf-8")
    (run / "dataset_manifest.json").write_text(json.dumps({"datasets": {"stress": "HSBCVisualStress-v1", "routing": "HSBCMultimodalRouting-v1"}, "case_count": result["case_count"], "stress_case_count": result["stress_case_count"], "routing_case_count": result["routing_case_count"], "evidence_count": result["evidence_count"], "citation_bbox": result["citation_bbox"], "stress_manifest_sha256": _sha256(project_root / "benchmarks/hsbc_visual_stress_v1/manifest.json"), "routing_manifest_sha256": _sha256(project_root / "benchmarks/hsbc_multimodal_routing_v1/manifest.json") if (project_root / "benchmarks/hsbc_multimodal_routing_v1/manifest.json").exists() else "N/A", "render_manifest_sha256": _sha256(project_root / "artifacts/hsbc_page_images/page_render_manifest.json")}, indent=2) + "\n", encoding="utf-8")
    return run


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/b3_cpu.json")
    args = parser.parse_args()
    config_path = project_root / args.config if not Path(args.config).is_absolute() else Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = run_b3(config)
    run = write_run(result, project_root / config.get("artifact_root", "artifacts/b3_runs"))
    print(json.dumps({"run": str(run.resolve()), "metrics": result["metrics"], "visual_model": result["visual_model"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
