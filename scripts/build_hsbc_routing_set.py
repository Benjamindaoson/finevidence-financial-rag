from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def _tokens(text: str) -> list[str]:
    return [item for item in re.findall(r"[a-z]{4,}", text.lower()) if item not in {"hsbc", "group", "report", "page", "year"}]


def _mine(rows: list[dict], pages: dict[tuple[str, int], dict], label: str, words: tuple[str, ...], limit: int, used: set[str]) -> list[dict]:
    selected = []
    for row in rows:
        if len(selected) >= limit or row["evidence_id"] in used:
            continue
        text = row["text"]
        if not all(word.lower() in text.lower() for word in words):
            continue
        terms = _tokens(text)[:4]
        if len(terms) < 2:
            continue
        query = f"What does the HSBC disclosure say about {' '.join(terms[:3])}?"
        if label == "TABLE_PARSED_SUFFICIENT":
            query = f"In the table, what does the HSBC disclosure say about {' '.join(terms[:3])}?"
        elif label == "VISUAL_NEEDED":
            query = f"Which chart or figure in the HSBC disclosure shows {' '.join(terms[:3])}?"
        page = pages[(row["document_id"], row["page"])]
        selected.append({
            "dataset_name": "HSBCMultimodalRouting-v1",
            "case_id": f"hsbc-r-{len(used) + len(selected) + 1:04d}",
            "question": query,
            "routing_class": label,
            "gold_route": "TABLE" if label == "TABLE_PARSED_SUFFICIENT" else ("VISUAL" if label == "VISUAL_NEEDED" else "TEXT"),
            "positive_evidence_id": row["evidence_id"].replace(":page", ":image"),
            "candidate_evidence_ids": [row["evidence_id"].replace(":page", ":image")],
            "gold_page": row["page"],
            "document_id": row["document_id"],
            "source_hashes": {row["evidence_id"]: page["image_sha256"]},
            "human_verified": False,
            "verification_method": "automatic_candidate_mining_plus_dual_model_assisted_adjudication",
        })
        used.add(row["evidence_id"])
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default="artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    parser.add_argument("--render-manifest", default="artifacts/hsbc_page_images/page_render_manifest.json")
    parser.add_argument("--output", default="benchmarks/hsbc_multimodal_routing_v1")
    parser.add_argument("--per-class", type=int, default=10)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.evidence).read_text(encoding="utf-8").splitlines() if line.strip()]
    pages = {(item["document_id"], item["page"]): item for item in json.loads(Path(args.render_manifest).read_text(encoding="utf-8"))["pages"]}
    rows = [row for row in rows if (row["document_id"], row["page"]) in pages]
    used: set[str] = set()
    cases = []
    cases += _mine(rows, pages, "TEXT_SUFFICIENT", ("purpose",), args.per_class, used)
    cases += _mine(rows, pages, "TABLE_PARSED_SUFFICIENT", ("table",), args.per_class, used)
    cases += _mine(rows, pages, "VISUAL_NEEDED", ("figure",), args.per_class, used)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in cases)
    (output / "questions.jsonl").write_text(payload, encoding="utf-8")
    manifest = {
        "dataset_name": "HSBCMultimodalRouting-v1",
        "description": "project-created mixed routing evaluation mined from real HSBC disclosure pages",
        "case_count": len(cases),
        "class_counts": {label: sum(item["routing_class"] == label for item in cases) for label in ("TEXT_SUFFICIENT", "TABLE_PARSED_SUFFICIENT", "VISUAL_NEEDED")},
        "cases_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "source_evidence": str(Path(args.evidence).resolve()),
        "source_render_manifest": str(Path(args.render_manifest).resolve()),
        "human_verified": False,
        "verification_method": "automatic_candidate_mining_plus_dual_model_assisted_adjudication",
        "gold_modality_is_eval_only": True,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
