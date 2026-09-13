"""Audit VisualStress construction and explain the frozen T0 @K results."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from finevidence.contracts.evidence import Evidence
from finevidence.retrieval.hybrid import HybridRetriever


ATTRIBUTIONS = (
    "QUERY_CONSTRUCTION_BIAS", "TEXT_RETRIEVAL_MISS", "OCR_CORRUPTION",
    "TABLE_STRUCTURE_LOSS", "LAYOUT_DEPENDENCY", "CHART_VISUAL_ONLY",
    "PAGE_FRAGMENTATION", "GOLD_MAPPING_ERROR", "OTHER",
)
_TOKENS = re.compile(r"[a-z0-9]+")
_YEARS = re.compile(r"20\d{2}")
_METRICS = {"ratio", "capital", "revenue", "profit", "growth", "increase", "decrease", "value", "amount", "income", "expenses", "risk", "return", "share", "cost", "loss", "assets", "liabilities", "performance"}
_ENTITY = {"hsbc", "group", "holdings", "bank", "uk", "china", "hong", "kong", "asia", "global"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tokens(text: str) -> set[str]:
    return set(_TOKENS.findall(text.lower()))


def _load_pages(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source_block(row: dict, evidence_by_page: dict[tuple[str, int], dict]) -> dict | None:
    return evidence_by_page.get((row["document_id"], int(row["gold_page"])))


def _overlap(query: str, source: str) -> dict:
    q, s = _tokens(query), _tokens(source)
    return {
        "query_token_count": len(q),
        "lexical_token_overlap_count": len(q & s),
        "lexical_token_overlap_rate": len(q & s) / max(len(q), 1),
        "entity_overlap": sorted((q & s) & _ENTITY),
        "metric_overlap": sorted((q & s) & _METRICS),
        "period_overlap": sorted(set(_YEARS.findall(query)) & set(_YEARS.findall(source))),
    }


def _page_ids(ranking: list[str], by_id: dict[str, Evidence]) -> list[str]:
    output = []
    for evidence_id in ranking:
        evidence = by_id.get(evidence_id)
        page = f"{evidence.document_id}:p{evidence.page}" if evidence else None
        if page and page not in output:
            output.append(page)
    return output


def _classification(row: dict, t0_pages: dict[str, list[str]], source_exists: bool, overlap: dict) -> tuple[str, list[str]]:
    category = row.get("category", "")
    reasons = []
    if not source_exists:
        return "GOLD_MAPPING_ERROR", ["positive page is absent from the frozen HSBC evidence pool"]
    if row.get("query_construction", {}).get("fixed_template") and overlap["lexical_token_overlap_rate"] < 0.20:
        return "QUERY_CONSTRUCTION_BIAS", ["fixed template query has weak lexical anchoring to its selected source page"]
    if category in {"CHART_VALUE", "CHART_LEGEND", "VISUAL_ONLY_INFORMATION", "CAPTION_MISMATCH"}:
        return "CHART_VISUAL_ONLY", ["category is explicitly chart/figure/visual and text-only evidence is not a visual relation"]
    if category in {"MULTI_COLUMN_READING_ORDER"}:
        return "LAYOUT_DEPENDENCY", ["category requires page layout or reading-order relation"]
    if category in {"TABLE_ROW_MIXING", "TABLE_COLUMN_MIXING", "MULTI_LEVEL_HEADER", "UNIT_HEADER_LOSS"}:
        return "TABLE_STRUCTURE_LOSS", ["category requires row/column/header/unit structure not present in T1 Parsed Page Text"]
    if category == "FOOTNOTE_LOSS":
        return "PAGE_FRAGMENTATION", ["category depends on a footnote or page-local exception relationship"]
    if not t0_pages["50"]:
        return "TEXT_RETRIEVAL_MISS", ["gold page is absent through T0 @50; no stronger parser diagnosis was established"]
    return "OTHER", reasons or ["gold page is present by @50 but not at the evaluated cutoff"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="benchmarks/hsbc_visual_stress_v1/questions.jsonl")
    parser.add_argument("--selection", default="benchmarks/hsbc_visual_stress_v1/audit_selection.json")
    parser.add_argument("--evidence", default="artifacts/hsbc_local_sources/hsbc_evidence.jsonl")
    parser.add_argument("--render-manifest", default="artifacts/hsbc_page_images/page_render_manifest.json")
    parser.add_argument("--output", default="artifacts/b3_2_runs/visualstress_audit")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases_path, selection_path = root / args.cases, root / args.selection
    cases = _load_pages(cases_path)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selected_ids = set(selection["case_ids"])
    render = json.loads((root / args.render_manifest).read_text(encoding="utf-8"))
    render_pages = {(item["document_id"], int(item["page"])): item for item in render["pages"]}
    raw_evidence = _load_pages(root / args.evidence)
    evidence_by_page = {(item["document_id"], int(item["page"])): item for item in raw_evidence}
    evidence = []
    by_id: dict[str, Evidence] = {}
    for raw in raw_evidence:
        page = render_pages.get((raw["document_id"], int(raw["page"])))
        if not page:
            continue
        item = Evidence.from_content(document_id=raw["document_id"], source_uri=raw["source_uri"], page=int(raw["page"]), block_id=raw["block_id"], modality="text", text=raw["text"], evidence_id=raw["evidence_id"])
        evidence.append(item)
        by_id[item.evidence_id] = item
    retriever = HybridRetriever()
    retriever.fit(evidence)
    records = []
    for row in cases:
        source = _source_block(row, evidence_by_page)
        source_text = source.get("text", "") if source else ""
        rankings = [item.evidence_id for item in retriever.search(row["question"], 50)]
        page_rank = _page_ids(rankings, by_id)
        t0_pages = {str(k): page_rank[:k] for k in (1, 5, 10, 50)}
        gold_page = f"{row['document_id']}:p{row['gold_page']}"
        gold_text_id = row["positive_evidence_id"].replace(":image", ":page")
        mapping = {"positive_evidence_id": row["positive_evidence_id"], "text_evidence_id": gold_text_id, "page_exists_in_evidence": gold_text_id in by_id, "gold_page": gold_page, "gold_page_in_render_manifest": (row["document_id"], int(row["gold_page"])) in render_pages}
        overlap = _overlap(row["question"], source_text)
        record = {
            "case_id": row["case_id"], "question": row["question"], "category": row.get("category"), "gold_page": gold_page,
            "source_block": {"evidence_id": gold_text_id, "block_id": source.get("block_id") if source else None, "content_hash": source.get("content_hash") if source else None, "text_excerpt": source_text[:500]},
            "t0_candidates": {f"@{k}": rankings[:k] for k in (1, 5, 10, 50)}, "t0_pages": t0_pages,
            "t0_gold_page_hit": {f"@{k}": gold_page in t0_pages[str(k)] for k in (1, 5, 10, 50)},
            "overlap": overlap, "gold_mapping": mapping,
            "query_construction": {"builder": "scripts/build_hsbc_visual_stress.py", "fixed_template": True, "keyword_selection": True, "category_keywords": row.get("category"), "source_cases_sha256": selection["source_cases_sha256"], "selection_rule": selection["selection_rule"]},
        }
        attribution, reasons = _classification(row, t0_pages, mapping["page_exists_in_evidence"], overlap)
        record["attribution"] = attribution
        record["attribution_reasons"] = reasons
        record["attribution_confidence"] = "deterministic_audit_inference"
        record["causal_claim"] = "not_proven_by_this_audit"
        record["selected_for_fixed_sample"] = row["case_id"] in selected_ids
        records.append(record)
    selected = [row for row in records if row["selected_for_fixed_sample"]]
    summary = {
        "dataset_name": "HSBCVisualStress-v1", "source_cases_sha256": _sha256(cases_path), "selection_manifest_sha256": _sha256(selection_path),
        "case_count": len(records), "fixed_sample_count": len(selected), "fixed_sample_ids": [row["case_id"] for row in selected],
        "t0_page_recall": {f"@{k}": sum(row["t0_gold_page_hit"][f"@{k}"] for row in records) / len(records) for k in (1, 5, 10, 50)},
        "fixed_sample_attribution": dict(Counter(row["attribution"] for row in selected)),
        "all_case_attribution": dict(Counter(row["attribution"] for row in records)),
        "construction_bias_indicators": {"fixed_template_all_cases": all(row["query_construction"]["fixed_template"] for row in records), "keyword_selected_positive_pages": True, "performance_blind_selection": selection["performance_blind"]},
        "interpretation": "T0 @10 is an observed result; attribution labels are deterministic audit inferences and do not prove a single causal mechanism.",
    }
    output = root / args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "all_cases.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    (output / "fixed_sample.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
