"""Build a performance-blind natural HSBC page control set."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9'/-]{2,}|\$?[0-9]+(?:\.[0-9]+)?%?", text)


def _query_seed(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines() if len(line.split()) >= 3]
    seed = lines[0] if lines else "the reported disclosure"
    return " ".join(_tokens(seed)[:12]) or "the reported disclosure"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default="artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    parser.add_argument("--render-manifest", default="artifacts/hsbc_page_images/page_render_manifest.json")
    parser.add_argument("--stress", default="benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    parser.add_argument("--output", default="benchmarks/hsbc_natural_multimodal_v1")
    parser.add_argument("--per-document", type=int, default=40)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    evidence_path, render_path, stress_path = root / args.evidence, root / args.render_manifest, root / args.stress
    render = json.loads(render_path.read_text(encoding="utf-8"))
    render_pages = {(item["document_id"], int(item["page"])): item for item in render["pages"]}
    raw = [json.loads(line) for line in evidence_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    stress = [json.loads(line) for line in stress_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    excluded = {item.replace(":image", ":page") for row in stress for item in row.get("candidate_evidence_ids", [])}
    pages = [item for item in raw if item["evidence_id"] not in excluded and (item["document_id"], int(item["page"])) in render_pages and len(_tokens(item.get("text", ""))) >= 12]
    grouped: dict[str, list[dict]] = {}
    for item in pages:
        grouped.setdefault(item["document_id"], []).append(item)
    selected = []
    for document_id in sorted(grouped):
        pool = sorted(grouped[document_id], key=lambda item: hashlib.sha256(f"{item['document_id']}:p{item['page']}:{item['content_hash']}".encode()).hexdigest())
        selected.extend(pool[: args.per_document])
    target = args.per_document * len(grouped)
    if not 60 <= target <= 100:
        raise ValueError(f"natural control target must be 60-100, got {target}")
    selected_keys = {(item["document_id"], int(item["page"])) for item in selected}
    by_doc_page = {(item["document_id"], int(item["page"])): item for item in raw}
    rows = []
    for index, positive in enumerate(selected, 1):
        key = (positive["document_id"], int(positive["page"]))
        negatives = []
        for delta in (-1, 1, -2, 2, -3, 3):
            candidate = by_doc_page.get((key[0], key[1] + delta))
            if candidate and candidate["evidence_id"] not in excluded and candidate["evidence_id"] != positive["evidence_id"]:
                negatives.append(candidate)
            if len(negatives) >= 3:
                break
        if not negatives:
            continue
        all_pages = [positive, *negatives]
        image_ids = [item["evidence_id"].replace(":page", ":image") for item in all_pages]
        rows.append({
            "dataset_name": "HSBCNaturalMultimodal-v1", "case_id": f"hsbc-n-{len(rows)+1:04d}",
            "question": f"What does the HSBC disclosure state about {_query_seed(positive['text'])}?",
            "query_source": "first_heading_like_line_from_positive_page", "category": "NATURAL_CORPUS_CONTROL",
            "document_id": positive["document_id"], "gold_page": int(positive["page"]),
            "positive_evidence_id": positive["evidence_id"].replace(":page", ":image"), "hard_negative_ids": image_ids[1:], "candidate_evidence_ids": image_ids,
            "source_hashes": {item["evidence_id"]: item["content_hash"] for item in all_pages},
            "image_hashes": {item["evidence_id"].replace(":page", ":image"): render_pages[(item["document_id"], int(item["page"]))]["image_sha256"] for item in all_pages},
            "gold_bbox": None, "human_verified": False, "verification_method": "corpus_hash_selection_plus_real_page_adjudication",
        })
    if not 60 <= len(rows) <= 100:
        raise ValueError(f"natural control valid case count must be 60-100, got {len(rows)}")
    output = root / args.output
    output.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    (output / "questions.jsonl").write_text(payload, encoding="utf-8")
    manifest = {
        "dataset_name": "HSBCNaturalMultimodal-v1", "description": "project-created natural control set from public HSBC disclosure pages",
        "case_count": len(rows), "cases_sha256": hashlib.sha256(payload.encode()).hexdigest(), "human_verified": False,
        "verification_method": "corpus_hash_selection_plus_real_page_adjudication", "selection_basis": "SHA256-ranked eligible corpus pages per document",
        "selection_frozen_before_retrieval": True, "performance_blind": True, "stress_candidate_pages_excluded": True,
        "source_evidence_sha256": _sha256(evidence_path), "source_render_manifest_sha256": _sha256(render_path), "stress_cases_sha256": _sha256(stress_path),
        "excluded_stress_page_count": len(excluded), "selected_source_pages": len(selected), "documents": sorted(grouped),
        "selection_note": "Selection was made from corpus identity and page content hashes only; T0/V0 rankings were unavailable to this script.",
    }
    (output / "selection_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
