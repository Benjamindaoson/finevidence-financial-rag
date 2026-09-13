from __future__ import annotations

import json
import math
import platform
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from finevidence.benchmarks.loader import load_benchmark
from finevidence.contracts.evidence import Evidence, RetrievedEvidence
from finevidence.eval.metrics import evaluate_retrieval
from finevidence.retrieval.dense import DenseRetriever
from finevidence.retrieval.fusion import weighted_fusion
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.neural import QwenEmbeddingRetriever


def _git_commit(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _percentile(values: list[float], percentile: float) -> float | str:
    if not values:
        return "N/A"
    if len(values) == 1:
        return float(values[0])
    return float(statistics.quantiles(values, n=100, method="inclusive")[int(percentile) - 1])


def _retrieval_metrics(cases, rankings: dict[str, list[str]] | None, top_k: int) -> dict[str, float | str]:
    if rankings is None:
        return {"recall_at_1": "N/A", "recall_at_5": "N/A", "recall_at_10": "N/A", "mrr": "N/A", "ndcg_at_10": "N/A", "complete_evidence_rate": "N/A"}
    eligible = [case for case in cases if case.answerable and case.required_evidence and case.question_id in rankings]
    if not eligible:
        return {"recall_at_1": "N/A", "recall_at_5": "N/A", "recall_at_10": "N/A", "mrr": "N/A", "ndcg_at_10": "N/A", "complete_evidence_rate": "N/A"}
    recall = {k: [] for k in (1, 5, 10)}
    reciprocal, ndcg, complete = [], [], []
    for case in eligible:
        required = {ref.evidence_id for ref in case.required_evidence}
        ranking = rankings[case.question_id]
        for k in recall:
            recall[k].append(len(required & set(ranking[:k])) / len(required))
        positions = [index + 1 for index, item in enumerate(ranking) if item in required]
        reciprocal.append(1 / min(positions) if positions else 0.0)
        gains = [1.0 if item in required else 0.0 for item in ranking[:10]]
        dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))
        ideal = sum(1 / math.log2(index + 2) for index in range(min(len(required), 10)))
        ndcg.append(dcg / ideal if ideal else 0.0)
        complete.append(required <= set(ranking[:top_k]))
    return {"recall_at_1": sum(recall[1]) / len(eligible), "recall_at_5": sum(recall[5]) / len(eligible), "recall_at_10": sum(recall[10]) / len(eligible), "mrr": sum(reciprocal) / len(eligible), "ndcg_at_10": sum(ndcg) / len(eligible), "complete_evidence_rate": sum(complete) / len(eligible)}


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_b5_1(config: dict) -> Path:
    root = Path(__file__).resolve().parents[3]
    benchmark = load_benchmark(root / config.get("benchmark_root", "benchmarks/real_finance_v1"))
    artifact_root = root / config.get("artifact_root", "artifacts/b5_1_runs")
    artifact_root.mkdir(parents=True, exist_ok=True)
    run = artifact_root / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}"
    run.mkdir()
    top_k = int(config.get("top_k", 10))
    evidence = benchmark.evidence
    current_dense = DenseRetriever()
    current_hybrid = HybridRetriever()
    timings: dict[str, list[float]] = {"current_dense_index": [], "current_hybrid_index": [], "qwen_index": [], "current_dense_query": [], "current_hybrid_query": [], "qwen_query": []}
    start = time.perf_counter(); current_dense.fit(evidence); timings["current_dense_index"].append((time.perf_counter() - start) * 1000)
    start = time.perf_counter(); current_hybrid.fit(evidence); timings["current_hybrid_index"].append((time.perf_counter() - start) * 1000)
    rankings: dict[str, dict[str, list[str]] | None] = {}
    predictions: list[dict] = []
    for name, retriever, timing_name in (("R1 Current Dense", current_dense, "current_dense_query"), ("R2 Current Hybrid", current_hybrid, "current_hybrid_query")):
        ranking = {}
        for case in benchmark.cases:
            start = time.perf_counter(); results = retriever.search(case.question, top_k); timings[timing_name].append((time.perf_counter() - start) * 1000)
            ranking[case.question_id] = [item.evidence_id for item in results]
            predictions.append({"system": name, "question_id": case.question_id, "retrieved": [item.model_dump() for item in results]})
        rankings[name] = ranking
    qwen = QwenEmbeddingRetriever(model_id=config.get("model_id", "Qwen/Qwen3-Embedding-0.6B"), revision=config.get("model_revision"), device=config.get("device", "cpu"), cache_dir=config.get("cache_dir"), local_files_only=bool(config.get("local_files_only", True)))
    qwen_manifest = qwen.manifest().model_dump()
    if qwen.available:
        start = time.perf_counter(); qwen.fit(evidence); timings["qwen_index"].append((time.perf_counter() - start) * 1000)
        qwen_ranking, hybrid_qwen_ranking = {}, {}
        for case in benchmark.cases:
            start = time.perf_counter(); q_results = qwen.search(case.question, top_k); timings["qwen_query"].append((time.perf_counter() - start) * 1000)
            h_results = current_hybrid.search(case.question, top_k)
            qwen_ranking[case.question_id] = [item.evidence_id for item in q_results]
            hybrid_qwen_ranking[case.question_id] = [item.evidence_id for item in weighted_fusion(h_results, q_results, text_weight=0.5, top_k=top_k)]
            predictions.extend(({"system": "R3 Qwen Dense", "question_id": case.question_id, "retrieved": [item.model_dump() for item in q_results]}, {"system": "R4 Current Hybrid + Qwen Dense", "question_id": case.question_id, "retrieved": hybrid_qwen_ranking[case.question_id]}))
        rankings["R3 Qwen Dense"] = qwen_ranking
        rankings["R4 Current Hybrid + Qwen Dense"] = hybrid_qwen_ranking
    else:
        rankings["R3 Qwen Dense"] = None
        rankings["R4 Current Hybrid + Qwen Dense"] = None
    metrics = {name: _retrieval_metrics(benchmark.cases, ranking, top_k) for name, ranking in rankings.items()}
    metrics["R0 BM25"] = {"status": "N/A", "reason": "explicit BM25 backend not present; current lexical component remains inside HybridRetriever"}
    metrics["hard_negative"] = {name: (evaluate_retrieval(benchmark.cases, ranking, top_k).get("hard_negative_error_rate", "N/A") if ranking is not None else "N/A") for name, ranking in rankings.items()}
    manifest = {**benchmark.manifest, "benchmark_root": str((root / config.get("benchmark_root", "benchmarks/real_finance_v1")).resolve())}
    run_config = {**config, "stage": "B5.1", "code_commit": _git_commit(root), "python": platform.python_version(), "device": config.get("device", "cpu"), "qwen_status": qwen_manifest["status"]}
    _write_json(run / "config.json", run_config)
    _write_json(run / "dataset_manifest.json", manifest)
    _write_json(run / "model_manifest.json", qwen_manifest)
    _write_json(run / "metrics.json", metrics)
    _write_json(run / "latency.json", {name: {"p50_ms": _percentile(values, 50), "p95_ms": _percentile(values, 95)} for name, values in timings.items()})
    (run / "predictions.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in predictions), encoding="utf-8")
    (run / "failures.json").write_text(json.dumps({"qwen": qwen_manifest, "historical_results_untouched": True}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run
