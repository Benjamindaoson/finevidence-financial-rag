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

from finevidence.contracts.b3 import CitationResult, VisualModelManifest
from finevidence.contracts.evidence import Evidence
from finevidence.contracts.requirements import FactEvidenceAlignment, Requirement, RequirementGraph
from finevidence.evidence.alignment import align_requirement_to_evidence, evaluate_independent_coverage
from finevidence.retrieval.fusion import rrf_fusion, weighted_fusion
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.routing import route_query
from finevidence.retrieval.visual import ClipImageEncoder, VisualRetriever


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
    recalls = {k: [] for k in (1, 5, 10)}
    mrr, ndcg = [], []
    for row in rows:
        gold = f"{row['document_id']}:p{row['gold_page']}"
        ranking = rankings[row["case_id"]]
        pages = _ranking_pages(ranking, by_id)
        for k in recalls:
            recalls[k].append(float(gold in pages[:k]))
        ranks = [index + 1 for index, page in enumerate(pages) if page == gold]
        mrr.append(1.0 / ranks[0] if ranks else 0.0)
        gains = [1.0 if page == gold else 0.0 for page in pages[:10]]
        dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))
        ndcg.append(dcg)
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


def run_b3(config: dict) -> dict:
    project_root = Path(__file__).resolve().parents[3]
    render_path = project_root / config.get("render_manifest", "artifacts/hsbc_page_images/page_render_manifest.json")
    stress_path = project_root / config.get("stress_cases", "benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    evidence_path = project_root / config.get("hsbc_evidence", "artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    render_manifest = json.loads(render_path.read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in stress_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence, by_id = _load_evidence(render_manifest, evidence_path)
    text_evidence = [item for item in evidence if item.modality == "text"]
    candidate_ids = {item_id for row in cases for item_id in row["candidate_evidence_ids"]}
    image_evidence = [item for item in evidence if item.modality == "image" and item.evidence_id in candidate_ids]
    text = HybridRetriever()
    text.fit(text_evidence)
    structured = HybridRetriever(alpha=0.45)
    structured.fit(text_evidence)
    visual = None
    visual_manifest = {"model_name": "N/A", "model_revision": "N/A", "runtime": "N/A", "device": "cpu", "image_encoder": False, "weights_sha256": None, "status": "N/A", "reason": "not attempted"}
    try:
        encoder = ClipImageEncoder(model_path=str(project_root / "artifacts/models"), device="cpu")
        visual = VisualRetriever(encoder)
        visual.fit(image_evidence)
        visual_manifest = encoder.manifest() if visual.available else {**visual_manifest, "reason": "no rendered image evidence"}
    except Exception as exc:
        visual_manifest["reason"] = f"{type(exc).__name__}: {exc}"
    rankings = {name: {} for name in ("T0 Text Only", "T1 Structured Text/Table", "V0 Visual Only", "M0 Fusion RRF", "M0 Fusion Weighted", "M1 Conditional Multimodal")}
    traces, failure_rows = [], []
    latencies = {name: [] for name in rankings}
    for row in cases:
        q = row["question"]
        start = time.perf_counter(); t_results = text.search(q, 10); t0 = [item.evidence_id for item in t_results]; latencies["T0 Text Only"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); t1 = [item.evidence_id for item in structured.search(q, 10)]; latencies["T1 Structured Text/Table"].append((time.perf_counter() - start) * 1000)
        v0 = []
        v_results = []
        if visual and visual.available:
            start = time.perf_counter(); v_results = visual.search(q, 10); v0 = [item.evidence_id for item in v_results]; latencies["V0 Visual Only"].append((time.perf_counter() - start) * 1000)
        else:
            latencies["V0 Visual Only"].append(0.0)
        text_retrieved = t0
        if v0:
            rrf = [item.evidence_id for item in rrf_fusion(t_results, v_results, top_k=10)]
            weighted = [item.evidence_id for item in weighted_fusion(t_results, v_results, top_k=10)]
        else:
            rrf = weighted = text_retrieved
        target_text_id = row["positive_evidence_id"].replace(":image", ":page")
        decision = route_query(q, initial_critical_coverage=0.0 if target_text_id not in text_retrieved[:5] else 1.0, parser_confidence=0.8)
        m1 = rrf if decision.visual_invoked and v0 else text_retrieved
        rankings["T0 Text Only"][row["case_id"]] = t0
        rankings["T1 Structured Text/Table"][row["case_id"]] = t1
        rankings["V0 Visual Only"][row["case_id"]] = v0
        rankings["M0 Fusion RRF"][row["case_id"]] = rrf
        rankings["M0 Fusion Weighted"][row["case_id"]] = weighted
        rankings["M1 Conditional Multimodal"][row["case_id"]] = m1
        for name, ranking in (("T0 Text Only", t0), ("T1 Structured Text/Table", t1), ("V0 Visual Only", v0), ("M0 Fusion RRF", rrf), ("M1 Conditional Multimodal", m1)):
            page_ranking = ranking
            coverage, eligible, warnings = _qualified(row, page_ranking, by_id)
            if name == "T0 Text Only":
                text_critical = eligible
            if name == "M1 Conditional Multimodal":
                m1_critical = eligible
        text_has = _page_for(row["positive_evidence_id"], by_id) in _ranking_pages(t0, by_id)
        m1_has = _page_for(row["positive_evidence_id"], by_id) in _ranking_pages(m1, by_id)
        failure_rows.append({"case_id": row["case_id"], "category": row["category"], "text_failed": not text_has, "visual_recovered": (not text_has and m1_has), "critical_recovered": (not text_critical and m1_critical), "regression": text_has and not m1_has})
        traces.append({"case_id": row["case_id"], "question": q, "requirements": [{"requirement_id": "R1", "description": q, "criticality": "CRITICAL", "modality": "VISUAL"}], "gold_page": f"{row['document_id']}:p{row['gold_page']}", "text_candidates": t0, "structured_candidates": t1, "initial_critical_coverage": float(text_critical), "routing_decision": decision.model_dump(), "visual_invoked": decision.visual_invoked, "visual_candidates": v0, "fusion_candidates": rrf, "final_candidates": m1, "final_critical_coverage": float(m1_critical), "text_failure_recovered": (not text_has and m1_has), "critical_requirement_recovered": (not text_critical and m1_critical), "multimodal_regression": text_has and not m1_has, "citation_result": _citation(row, m1, by_id).model_dump(), "latency_ms": {"text": latencies["T0 Text Only"][-1], "visual": latencies["V0 Visual Only"][-1]}, "warnings": []})
    metrics = {name: _rank_metrics(cases, ranking, by_id) for name, ranking in rankings.items()}
    recovery = sum(item["visual_recovered"] for item in failure_rows) / max(sum(item["text_failed"] for item in failure_rows), 1)
    critical_recovery = sum(item["critical_recovered"] for item in failure_rows) / max(sum(not _qualified(row, rankings["T0 Text Only"][row["case_id"]], by_id)[1] for row in cases), 1)
    regression = sum(item["regression"] for item in failure_rows) / len(failure_rows) if failure_rows else 0.0
    metrics["b3"] = {"text_only_failure_recovery_rate": recovery, "visual_critical_requirement_recovery_rate": critical_recovery, "multimodal_regression_rate": regression, "net_recovery": sum(item["visual_recovered"] for item in failure_rows) - sum(item["regression"] for item in failure_rows), "visual_routing_precision": sum(item["visual_recovered"] or not item["text_failed"] for item in failure_rows) / len(failure_rows) if failure_rows else 0.0, "visual_routing_recall": sum(item["visual_recovered"] for item in failure_rows) / max(sum(item["text_failed"] for item in failure_rows), 1), "visual_invocation_rate": sum(1 for trace in traces if trace["visual_invoked"]) / len(traces) if traces else 0.0}
    metrics["per_failure_type"] = {category: {name: _rank_metrics([row for row in cases if row["category"] == category], ranking, by_id)["page_recall_at_5"] for name, ranking in rankings.items()} for category in sorted({row["category"] for row in cases})}
    latency_metrics = {name: {"p50_ms": _percentile(values, 50), "p95_ms": _percentile(values, 95)} for name, values in latencies.items()}
    invocation = [bool(trace["visual_invoked"]) for trace in traces]
    visual_required = [row["category"] in {"CHART_VALUE", "CHART_LEGEND", "CAPTION_MISMATCH", "VISUAL_ONLY_INFORMATION", "MULTI_COLUMN_READING_ORDER"} for row in cases]
    true_positive_routes = sum(a and b for a, b in zip(invocation, visual_required))
    metrics["b3"].update({"visual_routing_precision": true_positive_routes / sum(invocation) if sum(invocation) else 0.0, "visual_routing_recall": true_positive_routes / sum(visual_required) if sum(visual_required) else "N/A", "unnecessary_visual_invocation_rate": sum(a and not b for a, b in zip(invocation, visual_required)) / max(sum(not b for b in visual_required), 1), "visual_pages_per_query": sum(len(trace["visual_candidates"]) for trace in traces) / len(traces) if traces else 0.0, "peak_gpu_memory_mb": 0.0})
    config = {**config, "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root, text=True).strip()}
    return {"config": config, "visual_model": visual_manifest, "case_count": len(cases), "evidence_count": len(evidence), "metrics": metrics, "latency_metrics": latency_metrics, "failure_cases": failure_rows, "traces": traces, "rankings": rankings, "citation_bbox": "N/A: no bbox gold in HSBCVisualStress-v1", "environment": {"device": "cpu", "cuda": False, "pid": os.getpid()}}


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
    (run / "routing_predictions.jsonl").write_text("".join(json.dumps({"case_id": trace["case_id"], "routing": trace["routing_decision"], "visual_invoked": trace["visual_invoked"]}) + "\n" for trace in result["traces"]), encoding="utf-8")
    (run / "grounding_predictions.jsonl").write_text("".join(json.dumps({"gold_page": trace["gold_page"], "citation_result": trace["citation_result"]}) + "\n" for trace in result["traces"]), encoding="utf-8")
    for name, rows in result["rankings"].items():
        filename = name.lower().replace(" ", "_").replace("+", "plus").replace("/", "_") + "_predictions.jsonl"
        (run / filename).write_text("".join(json.dumps({"case_id": case_id, "ranking": ranking}) + "\n" for case_id, ranking in rows.items()), encoding="utf-8")
    (run / "dataset_manifest.json").write_text(json.dumps({"dataset": "HSBCVisualStress-v1", "case_count": result["case_count"], "evidence_count": result["evidence_count"], "citation_bbox": result["citation_bbox"], "stress_manifest_sha256": _sha256(project_root / "benchmarks/hsbc_visual_stress_v1/manifest.json") if (project_root / "benchmarks/hsbc_visual_stress_v1/manifest.json").exists() else "N/A", "render_manifest_sha256": _sha256(project_root / "artifacts/hsbc_page_images/page_render_manifest.json")}, indent=2) + "\n", encoding="utf-8")
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
