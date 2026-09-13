"""Build a citation review queue with real historical retrieval predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    root = args.project_root.resolve()
    source = root / "benchmarks" / "real_finance_v1" / "questions.jsonl"
    trace_path = root / "artifacts" / "p0_d_runs" / "20260912T202612338140Z-c2f60731" / "per_query_trace.jsonl"
    output = (args.output or root / "artifacts" / "final_rag_eval" / "claim_citation_candidates_v1.jsonl").resolve()
    if output.exists():
        raise FileExistsError(output)
    traces = {row["question_id"]: row for row in jsonl(trace_path)}
    records = []
    for row in jsonl(source)[:50]:
        question_id = row["question_id"]
        trace = traces.get(question_id, {})
        predicted = trace.get("initial_ids", [])
        proposed_support = [item["evidence_id"] for item in row.get("required_evidence", [])]
        records.append(
            {
                "case_id": question_id,
                "claim": row["question"],
                "candidate_answer": row.get("gold_answer"),
                "predicted_evidence_ids": predicted,
                "proposed_supporting_evidence_ids": proposed_support,
                "evidence_candidate_ids": list(dict.fromkeys(predicted + proposed_support)),
                "source_dataset": row.get("source_dataset"),
                "source_case_id": row.get("source_record_id"),
                "annotation_status": "candidate_only",
                "annotation_method": "historical_top_k_plus_source_projection_pending_human_review",
                "annotator_count": 0,
                "human_verified": False,
                "provenance": {
                    "question_source_file": str(source.relative_to(root)),
                    "question_source_sha256": sha256(source),
                    "prediction_source_file": str(trace_path.relative_to(root)),
                    "prediction_source_sha256": sha256(trace_path),
                    "prediction_policy": "P0-D initial Top-K, top_k=5",
                    "review_required": True,
                },
            }
        )
    output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    manifest = {
        "dataset_name": "ClaimCitationCandidate-v1",
        "status": "CANDIDATE_ONLY",
        "human_verified": False,
        "record_count": len(records),
        "source_question_sha256": sha256(source),
        "source_prediction_sha256": sha256(trace_path),
        "prediction_policy": "P0-D initial Top-K, top_k=5",
        "output_sha256": sha256(output),
    }
    output.with_name("claim_citation_candidates_v1_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
