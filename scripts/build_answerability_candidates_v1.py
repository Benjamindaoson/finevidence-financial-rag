"""Build a balanced, human-review-only answerability queue from real cases.

The questions and evidence references are real frozen RealFinance rows.  The
partial/unanswerable variants describe a scoped evidence-availability failure;
they are proposed labels and require human adjudication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
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
    output = (args.output or root / "artifacts" / "final_rag_eval" / "answerability_candidates_v1.jsonl").resolve()
    if output.exists():
        raise FileExistsError(output)
    rows = read_jsonl(source)
    answerable = rows[:20]
    partial_pool = [row for row in rows[20:] if len(row.get("required_evidence", [])) >= 2]
    partial = partial_pool[:20]
    unanswerable = [row for row in rows[40:] if row not in partial][:20]
    if len(partial) < 20 or len(unanswerable) < 20:
        raise RuntimeError("frozen source does not provide enough distinct real cases")

    records: list[dict[str, Any]] = []
    for index, row in enumerate(answerable):
        evidence = [item["evidence_id"] for item in row.get("required_evidence", [])]
        records.append(
            {
                "case_id": f"{row['question_id']}:answerable",
                "source_case_id": row["question_id"],
                "question": row["question"],
                "source_dataset": row.get("source_dataset"),
                "candidate_status": "ANSWERABLE",
                "candidate_basis": "frozen_real_finance_case_with_source_evidence",
                "required_evidence_ids": evidence,
                "available_evidence_ids": evidence,
                "missing_evidence_ids": [],
                "required_facts": row.get("required_facts", []),
                "annotation_status": "candidate_only",
                "human_verified": False,
                "annotator_count": 0,
                "provenance": {"source_file": str(source.relative_to(root)), "source_sha256": sha256(source), "selection_index": index},
            }
        )
    for index, row in enumerate(partial):
        required = [item["evidence_id"] for item in row.get("required_evidence", [])]
        available = required[: max(1, len(required) // 2)]
        records.append(
            {
                "case_id": f"{row['question_id']}:partial-scoped-evidence",
                "source_case_id": row["question_id"],
                "question": row["question"],
                "source_dataset": row.get("source_dataset"),
                "candidate_status": "PARTIAL_EVIDENCE",
                "candidate_basis": "real_case_with_required_evidence_partially_withheld_in_scoped_pool",
                "required_evidence_ids": required,
                "available_evidence_ids": available,
                "missing_evidence_ids": [item for item in required if item not in available],
                "required_facts": row.get("required_facts", []),
                "annotation_status": "candidate_only",
                "human_verified": False,
                "annotator_count": 0,
                "provenance": {"source_file": str(source.relative_to(root)), "source_sha256": sha256(source), "selection_index": index + 20},
            }
        )
    for index, row in enumerate(unanswerable):
        required = [item["evidence_id"] for item in row.get("required_evidence", [])]
        records.append(
            {
                "case_id": f"{row['question_id']}:unanswerable-scoped-evidence",
                "source_case_id": row["question_id"],
                "question": row["question"],
                "source_dataset": row.get("source_dataset"),
                "candidate_status": "UNANSWERABLE",
                "candidate_basis": "real_question_with_no_supporting_evidence_in_scoped_pool",
                "required_evidence_ids": required,
                "available_evidence_ids": [],
                "missing_evidence_ids": required,
                "required_facts": row.get("required_facts", []),
                "annotation_status": "candidate_only",
                "human_verified": False,
                "annotator_count": 0,
                "provenance": {
                    "source_file": str(source.relative_to(root)),
                    "source_sha256": sha256(source),
                    "selection_index": index + 40,
                    "warning": "Scoped evidence withholding is a candidate construction; reviewer must decide partial vs unanswerable.",
                },
            }
        )

    output.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    manifest = {
        "dataset_name": "FinancialAnswerabilityCandidate-v1",
        "status": "CANDIDATE_ONLY",
        "human_verified": False,
        "source_dataset": "RealFinance-v1",
        "source_file": str(source.relative_to(root)),
        "source_sha256": sha256(source),
        "record_count": len(records),
        "class_counts": {name: sum(row["candidate_status"] == name for row in records) for name in ("ANSWERABLE", "PARTIAL_EVIDENCE", "UNANSWERABLE")},
        "construction": "real questions plus explicit scoped evidence-availability conditions; labels require human review",
        "output_sha256": sha256(output),
    }
    manifest_path = output.with_name("answerability_candidates_v1_manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
