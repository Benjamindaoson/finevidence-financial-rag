"""Run the final evaluation contracts against candidate or verified queues.

The current repository contains candidate-only annotations.  The runner still
produces the complete, reproducible artifact shape, but formal metrics stay
blocked until a real human reviewer promotes every required annotation row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from finevidence.eval.final_rag import answerability_metrics, citation_metrics, table_semantic_metrics


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--candidate-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    root = args.project_root.resolve()
    candidate_dir = (args.candidate_dir or root / "artifacts" / "final_rag_eval" / "candidates").resolve()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or root / "artifacts" / "final_rag_eval" / f"run_{run_id}").resolve()
    output.mkdir(parents=True, exist_ok=False)

    citation = load_jsonl(candidate_dir / "claim_citation_candidates.jsonl")
    tables = load_jsonl(candidate_dir / "table_semantic_candidates.jsonl")
    answerability = load_jsonl(candidate_dir / "answerability_candidates.jsonl")
    candidate_manifest = load_json(candidate_dir / "candidate_manifest.json")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()

    metrics = {
        "status": "BLOCKED_FOR_HUMAN_VERIFICATION",
        "human_verified_required": True,
        "claim_citation": citation_metrics(citation, []),
        "table_semantics": table_semantic_metrics(tables),
        "answerability": answerability_metrics(answerability),
        "candidate_counts": {
            "claim_citation": len(citation),
            "table_semantics": len(tables),
            "answerability": len(answerability),
        },
        "historical_metrics_unchanged": True,
    }
    config = {
        "run_id": run_id,
        "code_commit": commit,
        "status": metrics["status"],
        "human_verification_required": True,
        "scoring": "N/A until human_verified=true rows exist",
    }
    annotation_manifest = {
        "dataset": "FinalRAGEvalCandidate-v0",
        "annotation_status": "candidate_only",
        "human_verified": False,
        "promotion_rule": "Every scored row requires real human review and explicit promotion.",
        "candidate_manifest": candidate_manifest,
    }
    dataset_manifest = {
        "sources": candidate_manifest["sources"],
        "candidate_manifest_sha256": sha256(candidate_dir / "candidate_manifest.json"),
        "frozen_historical_data": True,
    }
    for name, value in (
        ("config.json", config),
        ("annotation_manifest.json", annotation_manifest),
        ("dataset_manifest.json", dataset_manifest),
        ("metrics.json", metrics),
    ):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for name in ("claim_citation_candidates.jsonl", "table_semantic_candidates.jsonl", "answerability_candidates.jsonl"):
        shutil.copyfile(candidate_dir / name, output / name)
    (output / "predictions.jsonl").write_text(
        json.dumps(
            {"status": "N/A", "reason": "No formal model predictions are scored without verified gold.", "code_commit": commit},
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    blocked = [
        {"track": "claim_citation", "type": "EVALUATION_BLOCKER", "reason": "HUMAN_VERIFICATION_REQUIRED"},
        {"track": "table_semantics", "type": "EVALUATION_BLOCKER", "reason": "HUMAN_VERIFICATION_REQUIRED"},
        {"track": "answerability", "type": "EVALUATION_BLOCKER", "reason": "MISSING_PARTIAL_UNANSWERABLE_VERIFIED_SET"},
    ]
    (output / "failure_cases.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in blocked), encoding="utf-8"
    )
    (output / "run_manifest.json").write_text(
        json.dumps({"run_id": run_id, "code_commit": commit, "status": metrics["status"], "candidate_dir": str(candidate_dir)}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "output": str(output), "status": metrics["status"]}, indent=2))


if __name__ == "__main__":
    main()
