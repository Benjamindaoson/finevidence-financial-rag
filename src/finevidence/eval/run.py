from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from finevidence.benchmarks.loader import load_benchmark
from finevidence.evidence.coverage import coverage_for_case
from finevidence.eval.metrics import evaluate_retrieval
from finevidence.retrieval.dense import DenseRetriever
from finevidence.retrieval.hybrid import HybridRetriever
from finevidence.retrieval.visual import VisualRetriever


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _git_commit(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "N/A"


def run_once(config: dict) -> Path:
    benchmark_root = Path(config["benchmark_root"]).resolve()
    benchmark = load_benchmark(benchmark_root)
    artifact_root = Path(config["artifact_root"]).resolve()
    manifest_hash = benchmark.manifest.get("files", {}).get(benchmark.manifest["evidence_file"], "")[:8]
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{manifest_hash}-{uuid4().hex[:8]}"
    run_dir = artifact_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    evidence = benchmark.evidence
    top_k = int(config.get("top_k", 5))
    dense = DenseRetriever()
    dense.fit(evidence)
    hybrid = HybridRetriever()
    hybrid.fit(evidence)
    visual = VisualRetriever()
    visual.fit(evidence)

    rankings: dict[str, dict[str, list[str]]] = {}
    predictions: list[dict] = []
    for baseline, retriever in (("B0", dense), ("B1", hybrid)):
        baseline_rankings: dict[str, list[str]] = {}
        for case in benchmark.cases:
            results = retriever.search(case.question, top_k)
            ids = [item.evidence_id for item in results]
            baseline_rankings[case.question_id] = ids
            predictions.append(
                {
                    "baseline": baseline,
                    "question_id": case.question_id,
                    "retrieved": [item.model_dump() for item in results],
                }
            )
        rankings[baseline] = baseline_rankings

    b2_rankings = rankings["B1"]
    for case in benchmark.cases:
        selected = set(b2_rankings[case.question_id][:top_k])
        coverage = coverage_for_case(case, selected)
        predictions.append(
            {
                "baseline": "B2",
                "question_id": case.question_id,
                "retrieved_evidence_ids": b2_rankings[case.question_id][:top_k],
                "coverage": coverage.__dict__,
                "answer_eligible": coverage.complete if case.answerable else False,
            }
        )

    metrics = {
        "B0": evaluate_retrieval(benchmark.cases, rankings["B0"], top_k),
        "B1": evaluate_retrieval(benchmark.cases, rankings["B1"], top_k),
        "B2": {
            **evaluate_retrieval(benchmark.cases, rankings["B1"], top_k),
            "unsupported_answer_rate": "N/A (generation not implemented)",
        },
        "B3": {
            "status": "N/A" if not visual.available else "available_not_scored",
            "reason": visual.reason if not visual.available else "visual scoring is not part of this runner yet",
        },
        "runtime": {"python": sys.version, "platform": platform.platform(), "top_k": top_k},
    }
    failures = []
    for case in benchmark.cases:
        selected = set(rankings["B1"][case.question_id][:top_k])
        coverage = coverage_for_case(case, selected)
        if case.answerable and not coverage.complete:
            failures.append(
                {
                    "question_id": case.question_id,
                    "failure_type": case.failure_type,
                    "missing_evidence_ids": coverage.missing_evidence_ids,
                }
            )

    project_root = Path(__file__).resolve().parents[3]
    _write_json(run_dir / "config.json", {**config, "git_commit": _git_commit(project_root)})
    _write_json(run_dir / "dataset_manifest.json", benchmark.manifest)
    _write_json(run_dir / "metrics.json", metrics)
    (run_dir / "predictions.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in predictions), encoding="utf-8"
    )
    (run_dir / "failure_cases.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in failures), encoding="utf-8"
    )
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reproducible FinEvidence MiniBench baselines.")
    parser.add_argument("--config", default="configs/mini_cpu.json")
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[3]
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config.setdefault("benchmark_root", str(project_root / "benchmarks" / "mini_finance"))
    config.setdefault("artifact_root", str(project_root / "artifacts" / "runs"))
    run_dir = run_once(config)
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
