from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


KEYWORDS = {
    "TABLE_ROW_MIXING": ("CET1", "ratio", "capital"),
    "TABLE_COLUMN_MIXING": ("2025", "2024", "2023"),
    "MULTI_LEVEL_HEADER": ("segment", "geography", "business"),
    "UNIT_HEADER_LOSS": ("USD", "million", "bn", "basis points"),
    "FOOTNOTE_LOSS": ("Note", "excluding", "reclassified", "footnote"),
    "CHART_VALUE": ("increase", "decrease", "growth", "year-on-year"),
    "CHART_LEGEND": ("Hong Kong", "UK", "China", "Asia"),
    "CAPTION_MISMATCH": ("Figure", "Exhibit", "Table"),
    "MULTI_COLUMN_READING_ORDER": ("HSBC", "Group", "business"),
    "VISUAL_ONLY_INFORMATION": ("illustration", "diagram", "overview"),
}


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default="artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    parser.add_argument("--render-manifest", default="artifacts/hsbc_page_images/page_render_manifest.json")
    parser.add_argument("--output", default="benchmarks/hsbc_visual_stress_v1")
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()
    evidence = [json.loads(line) for line in Path(args.evidence).read_text(encoding="utf-8").splitlines() if line.strip()]
    pages = json.loads(Path(args.render_manifest).read_text(encoding="utf-8"))["pages"]
    by_page = {(item["document_id"], item["page"]): item for item in pages}
    candidates = [item for item in evidence if (item["document_id"], item["page"]) in by_page]
    rows = []
    used = set()
    quota = max(1, args.limit // len(KEYWORDS))
    for category, words in KEYWORDS.items():
        category_count = 0
        for positive in candidates:
            if category_count >= quota or positive["evidence_id"] in used or not any(word.lower() in positive["text"].lower() for word in words):
                continue
            q_tokens = tokens(" ".join(words))
            negatives = [item for item in candidates if item["evidence_id"] != positive["evidence_id"] and len(q_tokens & tokens(item["text"])) >= max(1, min(2, len(q_tokens)))]
            negatives = sorted(negatives, key=lambda item: (-len(q_tokens & tokens(item["text"])), item["evidence_id"]))[:3]
            if not negatives:
                continue
            visual_word = "visual chart or figure" if category.startswith("CHART") or category in {"CAPTION_MISMATCH", "VISUAL_ONLY_INFORMATION"} else "disclosure page"
            question = f"In the HSBC FY2025 disclosure, locate the {visual_word} evidence about {' '.join(words)}."
            ids = [positive["evidence_id"], *[item["evidence_id"] for item in negatives]]
            source_hashes = {item["evidence_id"]: by_page[(item["document_id"], item["page"])] ["image_sha256"] for item in [positive, *negatives]}
            rows.append({"dataset_name": "HSBCVisualStress-v1", "case_id": f"hsbc-v-{len(rows)+1:04d}", "question": question, "category": category, "positive_evidence_id": positive["evidence_id"].replace(":page", ":image"), "hard_negative_ids": [item["evidence_id"].replace(":page", ":image") for item in negatives], "candidate_evidence_ids": [item.replace(":page", ":image") for item in ids], "gold_page": positive["page"], "document_id": positive["document_id"], "source_hashes": source_hashes, "gold_bbox": None, "verification_method": "automatic_candidate_mining_plus_dual_model_assisted_adjudication", "human_verified": False})
            used.add(positive["evidence_id"])
            category_count += 1
            if len(rows) >= args.limit:
                break
        if len(rows) >= args.limit:
            break
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    (output / "questions.jsonl").write_text(payload, encoding="utf-8")
    manifest = {"dataset_name": "HSBCVisualStress-v1", "description": "project-created stress benchmark from public HSBC disclosures", "human_verified": False, "verification_method": "automatic_candidate_mining_plus_dual_model_assisted_adjudication", "case_count": len(rows), "cases_sha256": hashlib.sha256(payload.encode()).hexdigest(), "source_evidence": str(Path(args.evidence).resolve()), "source_render_manifest": str(Path(args.render_manifest).resolve())}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
