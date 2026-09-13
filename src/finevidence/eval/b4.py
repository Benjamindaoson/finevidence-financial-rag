from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import time
from pathlib import Path

from finevidence.contracts.evidence import Evidence
from finevidence.evidence.table_ir import parse_table, table_structure_invariants
from finevidence.eval.b3 import _load_evidence, _page_for, _qualified, _ranking_pages
from finevidence.retrieval.failure_router import FailureRoute, oracle_failure_route, predict_failure_route
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.visual import ClipImageEncoder, VisualRetriever


POLICIES = ("Always Text", "Coverage -> Vision", "Always Vision", "Oracle Failure Router", "Predicted Failure Router")
K = (1, 5, 10, 50)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile(values: list[float], percentile: int) -> float | str:
    if not values:
        return "N/A"
    if len(values) == 1:
        return float(values[0])
    return float(statistics.quantiles(values, n=100, method="inclusive")[max(0, min(99, percentile - 1))])


def _route_action(route: FailureRoute, query: str, text: HybridRetriever, by_id: dict[str, Evidence], visual: VisualRetriever | None) -> list[str]:
    if route.action == "TEXT_RETRY":
        return [item.evidence_id for item in text.search(query, 50)]
    if route.action == "VISUAL_RETRIEVAL" and visual and visual.available:
        return [item.evidence_id for item in visual.search(query, 50)]
    if route.action == "ADJACENT_PAGE_RETRIEVAL":
        # ponytail: local +/-1 page expansion; replace with document-aware page graph if cross-document continuity matters.
        seen: set[str] = set()
        result: list[str] = []
        for item in text.search(query, 10):
            evidence = by_id.get(item.evidence_id)
            if not evidence:
                continue
            for page in (evidence.page - 1, evidence.page, evidence.page + 1):
                for candidate in by_id.values():
                    if candidate.modality == "text" and candidate.document_id == evidence.document_id and candidate.page == page and candidate.evidence_id not in seen:
                        seen.add(candidate.evidence_id)
                        result.append(candidate.evidence_id)
        return result[:50]
    return []


def _table_ir_eval(project_root: Path, config: dict) -> dict:
    source = project_root / config.get("tatqa_source", "../research/repos/tat-qa/dataset_raw/tatqa_dataset_dev.json")
    if not source.exists():
        return {"status": "N/A", "reason": f"missing source: {source}"}
    questions = project_root / config.get("real_finance_questions", "benchmarks/real_finance_v1/questions.jsonl")
    if not questions.exists():
        return {"status": "N/A", "reason": f"missing benchmark: {questions}"}
    records = json.loads(source.read_text(encoding="utf-8"))
    wanted = []
    for line in questions.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if item.get("source_dataset") == "TAT-QA":
                wanted.append(str(item["source_record_id"]))
    tables = []
    seen: set[str] = set()
    for record_id in wanted:
        if record_id in seen or not record_id.isdigit() or int(record_id) >= len(records):
            continue
        seen.add(record_id)
        raw = records[int(record_id)]
        try:
            table = parse_table(raw["table"], document_id=f"tatqa:{record_id}", source_record_id=record_id)
            tables.append({"table": table.model_dump(), "invariants": table_structure_invariants(table, raw["table"])})
        except (KeyError, TypeError, ValueError) as exc:
            tables.append({"source_record_id": record_id, "error": f"{type(exc).__name__}: {exc}"})
    valid = [item for item in tables if "invariants" in item]
    def rate(key: str) -> float | str:
        return sum(bool(item["invariants"][key]) for item in valid) / len(valid) if valid else "N/A"
    return {
        "status": "READY" if valid else "N/A", "source": str(source), "source_sha256": _sha256(source),
        "source_table_count": len(valid), "parse_success_rate": len(valid) / len(tables) if tables else "N/A",
        "raw_value_roundtrip_rate": rate("raw_value_roundtrip"), "cell_identity_rate": rate("cell_identity_unique"),
        "row_column_relation_rate": rate("row_column_relations_present"),
        "header_path_population_rate": sum(bool(cell["header_path"]) for item in valid for cell in item["table"]["cells"]) / sum(len(item["table"]["cells"]) for item in valid) if valid else "N/A",
        "caption_relation": "N/A", "footnote_relation": "N/A", "bbox": "N/A",
        "records": tables,
    }


def _policy_metrics(rows: list[dict], rankings: dict[str, list[str]], base: dict[str, list[str]], by_id: dict[str, Evidence]) -> dict:
    output = {}
    for policy, ranking_map in rankings.items():
        hits = {k: [] for k in K}
        recovered = {k: 0 for k in K}
        regressions = {k: 0 for k in K}
        for row in rows:
            gold = f"{row['document_id']}:p{row['gold_page']}"
            pages = _ranking_pages(ranking_map[row["case_id"]], by_id)
            base_pages = _ranking_pages(base[row["case_id"]], by_id)
            for k in K:
                hit = gold in pages[:k]
                base_hit = gold in base_pages[:k]
                hits[k].append(float(hit))
                recovered[k] += int(not base_hit and hit)
                regressions[k] += int(base_hit and not hit)
        output[policy] = {
            "page_recall_at_1": sum(hits[1]) / len(rows) if rows else "N/A", "page_recall_at_5": sum(hits[5]) / len(rows) if rows else "N/A",
            "page_recall_at_10": sum(hits[10]) / len(rows) if rows else "N/A", "page_recall_at_50": sum(hits[50]) / len(rows) if rows else "N/A",
            "recovery_at_k": {str(k): {"recovered_cases": recovered[k], "regression_cases": regressions[k], "net_recovery": recovered[k] - regressions[k]} for k in K},
        }
    return output


def _route_quality(rows: list[dict], routes: dict[str, FailureRoute], oracle: dict[str, FailureRoute]) -> dict:
    non_unknown = [row for row in rows if oracle[row["case_id"]].action != "ABSTAIN_ESCALATE"]
    correct = sum(routes[row["case_id"]].action == oracle[row["case_id"]].action for row in non_unknown)
    return {"case_count": len(rows), "evaluated_case_count": len(non_unknown), "route_accuracy": correct / len(non_unknown) if non_unknown else "N/A", "route_confusion": {action: sum(routes[row["case_id"]].action == action and oracle[row["case_id"]].action != action for row in non_unknown) for action in {route.action for route in oracle.values()}}}


def _qualification_metrics(traces: list[dict], policy: str) -> dict:
    values = [trace["qualification"][policy] for trace in traces]
    return {"critical_coverage": sum(item["critical_coverage"] for item in values) / len(values) if values else "N/A", "eligible_rate": sum(item["answer_eligible"] for item in values) / len(values) if values else "N/A"}


def _category_metrics(category: str, policy: str, rows: list[dict], traces: list[dict], rankings: dict[str, dict[str, list[str]]], by_id: dict[str, Evidence]) -> dict:
    subset = [row for row in rows if row.get("category") == category]
    subset_ids = {row["case_id"] for row in subset}
    page = _policy_metrics(subset, {policy: {case_id: rankings[policy][case_id] for case_id in subset_ids}}, {case_id: rankings["Always Text"][case_id] for case_id in subset_ids}, by_id)[policy]["page_recall_at_10"]
    subset_traces = [trace for trace in traces if trace["category"] == category]
    return {"page_recall_at_10": page, "eligible_rate": sum(trace["qualification"][policy]["answer_eligible"] for trace in subset_traces) / len(subset_traces) if subset_traces else "N/A"}


def run_b4(config: dict) -> dict:
    project_root = Path(__file__).resolve().parents[3]
    render_path = project_root / config.get("render_manifest", "artifacts/hsbc_page_images/page_render_manifest.json")
    stress_path = project_root / config.get("stress_cases", "benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    evidence_path = project_root / config.get("hsbc_evidence", "artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    render_manifest = json.loads(render_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in stress_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence, by_id = _load_evidence(render_manifest, evidence_path)
    text_evidence = [item for item in evidence if item.modality == "text"]
    text = HybridRetriever(); text.fit(text_evidence)
    legacy_ids = {item_id for row in rows for item_id in row["candidate_evidence_ids"]}
    images = [item for item in evidence if item.modality == "image" and item.evidence_id in legacy_ids]
    visual: VisualRetriever | None = None
    visual_manifest: dict = {"status": "N/A", "reason": "not attempted"}
    visual_index_ms = 0.0
    try:
        encoder = ClipImageEncoder(model_path=str(project_root / "artifacts/models"), device="cpu")
        visual_manifest = encoder.manifest()
        visual = VisualRetriever(encoder)
        start = time.perf_counter(); visual.fit(images); visual_index_ms = (time.perf_counter() - start) * 1000
    except Exception as exc:
        visual_manifest["reason"] = f"{type(exc).__name__}: {exc}"
    rankings = {policy: {} for policy in POLICIES}
    traces, failures = [], []
    oracle_routes, predicted_routes = {}, {}
    latencies = {name: [] for name in ("text_retrieval", "structured_table_retrieval", "adjacent_page_retrieval", "visual_retrieval", "routing", "evidence_qualification", "end_to_end")}
    parser_has_table_ir = False
    for row in rows:
        start_case = time.perf_counter(); q = row["question"]
        start = time.perf_counter(); t_ids = [item.evidence_id for item in text.search(q, 50)]; latencies["text_retrieval"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); initial_coverage, text_critical, initial_warnings = _qualified(row, t_ids[:10], by_id); latencies["evidence_qualification"].append((time.perf_counter() - start) * 1000)
        oracle = oracle_failure_route(row.get("category", "UNKNOWN")); predicted = predict_failure_route(q, initial_coverage=initial_coverage, parser_has_table_ir=parser_has_table_ir)
        oracle_routes[row["case_id"]] = oracle; predicted_routes[row["case_id"]] = predicted
        start = time.perf_counter(); route = predicted; latencies["routing"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter(); visual_ids = [item.evidence_id for item in visual.search(q, 50)] if visual and visual.available else []; latencies["visual_retrieval"].append((time.perf_counter() - start) * 1000)
        route_ids: dict[str, list[str]] = {"Always Text": t_ids, "Coverage -> Vision": visual_ids if initial_coverage < 1.0 else t_ids, "Always Vision": visual_ids}
        for name, selected_route in (("Oracle Failure Router", oracle), ("Predicted Failure Router", predicted)):
            start = time.perf_counter(); route_ids[name] = _route_action(selected_route, q, text, by_id, visual)
            action_latency = {"TEXT_RETRY": "text_retrieval", "ADJACENT_PAGE_RETRIEVAL": "adjacent_page_retrieval", "VISUAL_RETRIEVAL": "visual_retrieval"}.get(selected_route.action)
            if action_latency:
                latencies[action_latency].append((time.perf_counter() - start) * 1000)
        for policy in POLICIES: rankings[policy][row["case_id"]] = route_ids[policy]
        qualification = {}
        for policy in POLICIES:
            start = time.perf_counter(); coverage, eligible, warnings = _qualified(row, route_ids[policy][:10], by_id); qualification[policy] = {"critical_coverage": float(coverage), "answer_eligible": eligible, "warnings": warnings}; latencies["evidence_qualification"].append((time.perf_counter() - start) * 1000)
        gold_page = f"{row['document_id']}:p{row['gold_page']}"
        text_hit = gold_page in _ranking_pages(t_ids[:10], by_id)
        final = qualification["Predicted Failure Router"]
        final_hit = gold_page in _ranking_pages(route_ids["Predicted Failure Router"][:10], by_id)
        failure = {"case_id": row["case_id"], "category": row.get("category", "UNKNOWN"), "text_failed": not text_hit, "predicted_route": predicted.action, "oracle_route": oracle.action, "visual_recovered": not text_hit and final_hit, "text_critical": text_critical, "critical_recovered": not text_critical and final["critical_coverage"] >= 1.0, "regression": text_hit and not final_hit}
        failures.append(failure)
        traces.append({"case_id": row["case_id"], "question": q, "category": row.get("category"), "gold_page": gold_page, "text_candidates": t_ids[:50], "initial_critical_coverage": float(initial_coverage), "initial_warnings": initial_warnings, "oracle_route": oracle.model_dump(), "predicted_route": predicted.model_dump(), "visual_candidates": visual_ids[:50], "policy_rankings": {policy: rankings[policy][row["case_id"]][:50] for policy in POLICIES}, "policy_actions": {"Always Text": "TEXT_RETRY", "Coverage -> Vision": "VISUAL_RETRIEVAL" if initial_coverage < 1.0 else "TEXT_RETRY", "Always Vision": "VISUAL_RETRIEVAL", "Oracle Failure Router": oracle.action, "Predicted Failure Router": predicted.action}, "qualification": qualification, "visual_invoked": {"Coverage -> Vision": initial_coverage < 1.0, "Always Vision": True, "Oracle Failure Router": oracle.action == "VISUAL_RETRIEVAL", "Predicted Failure Router": predicted.action == "VISUAL_RETRIEVAL"}, "latency_ms": {"end_to_end": (time.perf_counter() - start_case) * 1000}})
        latencies["end_to_end"].append((time.perf_counter() - start_case) * 1000)
    oracle_quality = _route_quality(rows, oracle_routes, oracle_routes)
    predicted_quality = _route_quality(rows, predicted_routes, oracle_routes)
    policy_metrics = _policy_metrics(rows, rankings, rankings["Always Text"], by_id)
    for policy in POLICIES:
        policy_metrics[policy].update(_qualification_metrics(traces, policy))
    action_rates = {}
    for policy in POLICIES:
        actions = [trace["policy_actions"][policy] for trace in traces]
        action_rates[policy] = {"visual_invocation_rate": sum(action == "VISUAL_RETRIEVAL" for action in actions) / len(actions) if actions else 0.0, "structured_table_invocation_rate": sum(action == "STRUCTURED_TABLE_RETRIEVAL" for action in actions) / len(actions) if actions else 0.0, "adjacent_page_invocation_rate": sum(action == "ADJACENT_PAGE_RETRIEVAL" for action in actions) / len(actions) if actions else 0.0, "text_retry_rate": sum(action == "TEXT_RETRY" for action in actions) / len(actions) if actions else 0.0, "abstain_rate": sum(action == "ABSTAIN_ESCALATE" for action in actions) / len(actions) if actions else 0.0, "structured_table_available": False}
    categories = sorted({item["category"] for item in failures})
    per_failure_type = {category: {policy: _category_metrics(category, policy, rows, traces, rankings, by_id) for policy in POLICIES} for category in categories}
    metrics = {"table_ir": _table_ir_eval(project_root, config), "policies": policy_metrics, "oracle_route_quality": oracle_quality, "predicted_route_quality": predicted_quality, "failure_counts": {category: sum(item["category"] == category for item in failures) for category in categories}, "route_invocation": action_rates, "predicted_router": {"critical_recovery_rate": sum(item["critical_recovered"] for item in failures) / sum(not item["text_critical"] for item in failures) if sum(not item["text_critical"] for item in failures) else "N/A", "regression_rate": sum(item["regression"] for item in failures) / len(failures) if failures else "N/A", "net_recovery": sum(item["visual_recovered"] for item in failures) - sum(item["regression"] for item in failures)}, "structured_table_ir": "N/A on HSBC: current parser exposes page text only", "per_failure_type": per_failure_type}
    latency_metrics = {name: {"p50_ms": _percentile(values, 50), "p95_ms": _percentile(values, 95)} for name, values in latencies.items()}
    latency_metrics["offline_indexing"] = {"text_indexing_ms": "N/A", "structured_table_indexing_ms": "N/A", "visual_indexing_ms": visual_index_ms, "visual_pages_indexed": len(images)}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root, text=True).strip()
    result = {"config": {**config, "code_commit": commit, "policies": POLICIES, "retrieval_cutoffs": K, "parser_has_table_ir_hsbc": False}, "visual_model": visual_manifest, "dataset": {"name": "HSBCVisualStress-v1", "case_count": len(rows), "cases_sha256": _sha256(stress_path), "render_manifest_sha256": _sha256(render_path), "evidence_sha256": _sha256(evidence_path)}, "metrics": metrics, "latency_metrics": latency_metrics, "failures": failures, "traces": traces, "rankings": rankings, "public_corpus": {"status": "separate investigation required", "frozen": True}}
    return result


def write_run(result: dict, artifact_root: Path) -> Path:
    artifact_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S"); run = artifact_root / stamp; suffix = 0
    while run.exists():
        suffix += 1; run = artifact_root / f"{stamp}-{suffix}"
    run.mkdir()
    for name, value in (("config.json", result["config"]), ("model_manifest.json", result["visual_model"]), ("dataset_manifest.json", result["dataset"]), ("metrics.json", result["metrics"]), ("latency_metrics.json", result["latency_metrics"]), ("per_failure_type_metrics.json", result["metrics"]["failure_counts"]), ("public_corpus.json", result["public_corpus"])):
        (run / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    table_records = result["metrics"]["table_ir"].get("records", [])
    (run / "table_ir.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in table_records), encoding="utf-8")
    for name, items in (("failure_cases.jsonl", result["failures"]), ("per_query_trace.jsonl", result["traces"])):
        (run / name).write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf-8")
    for policy, items in result["rankings"].items():
        filename = policy.lower().replace(" ", "_").replace("-", "_").replace(">", "to") + "_predictions.jsonl"
        (run / filename).write_text("".join(json.dumps({"case_id": case_id, "ranking": ranking}) + "\n" for case_id, ranking in items.items()), encoding="utf-8")
    return run


def main() -> int:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(); parser.add_argument("--config", default="configs/b4_cpu.json"); args = parser.parse_args()
    config_path = project_root / args.config if not Path(args.config).is_absolute() else Path(args.config)
    result = run_b4(json.loads(config_path.read_text(encoding="utf-8")))
    run = write_run(result, project_root / result["config"].get("artifact_root", "artifacts/b4_runs"))
    print(json.dumps({"run": str(run.resolve()), "table_ir": result["metrics"]["table_ir"].get("status"), "predicted_route_accuracy": result["metrics"]["predicted_route_quality"].get("route_accuracy")}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
