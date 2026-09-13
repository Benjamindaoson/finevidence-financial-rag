"""Build review queues for the final RAG evaluation tracks.

This script projects existing source records into annotation queues.  It does
not create gold labels and never sets ``human_verified`` to true.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    questions_path = root / "benchmarks" / "real_finance_v1" / "questions.jsonl"
    table_path = root / "artifacts" / "b4_1_runs" / "20260914T013551" / "table_ir.jsonl"
    questions = read_jsonl(questions_path)
    tables = read_jsonl(table_path)

    citation = []
    for row in questions[:50]:
        citation.append(
            {
                "case_id": row["question_id"],
                "claim": row["question"],
                "candidate_answer": row.get("gold_answer"),
                "supporting_evidence_ids": [item["evidence_id"] for item in row.get("required_evidence", [])],
                "source_dataset": row.get("source_dataset"),
                "source_case_id": row.get("source_record_id"),
                "annotation_status": "candidate_only",
                "annotation_method": "source_projection_pending_human_review",
                "annotator_count": 0,
                "human_verified": False,
                "provenance": {
                    "source_file": str(questions_path.relative_to(root)),
                    "source_sha256": digest(questions_path),
                    "review_required": True,
                },
            }
        )

    semantic = []
    for table in tables:
        semantic.append(
            {
                "table_id": table["table_id"],
                "document_id": table["source_document_id"],
                "page": table["source_page"],
                "source_record_id": table.get("source_record_id"),
                "cells": table.get("cells", []),
                "structure_recoverable": None,
                "cell_value_correct": None,
                "row_mapping_correct": None,
                "column_mapping_correct": None,
                "header_path_correct": None,
                "unit_correct": None,
                "period_correct": None,
                "entity_correct": None,
                "merged_semantics_correct": None,
                "footnote_association_correct": None,
                "annotation_status": "candidate_only",
                "annotation_method": "table_ir_projection_pending_human_review",
                "annotator_count": 0,
                "human_verified": False,
                "provenance": {
                    "source_file": str(table_path.relative_to(root)),
                    "source_sha256": digest(table_path),
                    "review_required": True,
                },
            }
        )

    answerability = []
    for row in questions[:60]:
        answerability.append(
            {
                "case_id": row["question_id"],
                "question": row["question"],
                "source_dataset": row.get("source_dataset"),
                "proposed_answerability": "ANSWERABLE" if row.get("answerable") else "UNANSWERABLE",
                "proposed_action": "ANSWER" if row.get("answerable") else "ABSTAIN",
                "annotation_status": "candidate_only",
                "annotation_method": "source_projection_pending_human_review",
                "annotator_count": 0,
                "human_verified": False,
                "provenance": {
                    "source_file": str(questions_path.relative_to(root)),
                    "source_sha256": digest(questions_path),
                    "review_required": True,
                    "warning": "Existing slice is answerable-only; no partial/unanswerable labels were inferred.",
                },
            }
        )

    write_jsonl(output / "claim_citation_candidates.jsonl", citation)
    write_jsonl(output / "table_semantic_candidates.jsonl", semantic)
    write_jsonl(output / "answerability_candidates.jsonl", answerability)
    manifest = {
        "dataset_version": "FinalRAGEvalCandidate-v0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "human_verified": False,
        "annotation_status": "candidate_only",
        "tracks": {
            "claim_citation": {"count": len(citation), "source": str(questions_path.relative_to(root))},
            "table_semantics": {"count": len(semantic), "source": str(table_path.relative_to(root))},
            "answerability": {
                "count": len(answerability),
                "source": str(questions_path.relative_to(root)),
                "class_counts": {
                    "ANSWERABLE": sum(row["proposed_answerability"] == "ANSWERABLE" for row in answerability),
                    "PARTIAL_EVIDENCE": 0,
                    "UNANSWERABLE": sum(row["proposed_answerability"] == "UNANSWERABLE" for row in answerability),
                },
                "status": "BLOCKED",
                "reason": "No verified partial/unanswerable annotation source exists in the frozen slice.",
            },
        },
        "sources": {
            "questions_sha256": digest(questions_path),
            "table_ir_sha256": digest(table_path),
        },
    }
    (output / "candidate_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = (args.output or root / "artifacts" / "final_rag_eval" / "candidates").resolve()
    print(json.dumps(build(root, output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
