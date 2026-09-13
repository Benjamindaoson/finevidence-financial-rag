"""Freeze a performance-blind VisualStress audit sample."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    parser.add_argument("--output", default="benchmarks/hsbc_visual_stress_v1/audit_selection.json")
    parser.add_argument("--per-category", type=int, default=2)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases_path = root / args.cases
    rows = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["category"]].append(row)
    selected = []
    for category in sorted(grouped):
        selected.extend(row["case_id"] for row in grouped[category][: args.per_category])
    payload = {
        "dataset_name": "HSBCVisualStress-v1",
        "audit_name": "HSBCVisualStress-v1-construction-audit-sample",
        "selection_rule": "first N cases in original frozen case order within each category; category and order only",
        "performance_blind": True,
        "forbidden_inputs": ["T0 rankings", "V0 rankings", "B3/B3.1 metrics", "failure labels"],
        "source_cases": str(cases_path.resolve()),
        "source_cases_sha256": _sha256(cases_path),
        "case_count": len(selected),
        "per_category": args.per_category,
        "case_ids": selected,
    }
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
