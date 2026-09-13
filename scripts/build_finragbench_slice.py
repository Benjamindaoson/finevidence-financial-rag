from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/finragbench_v_source")
    parser.add_argument("--output", default="benchmarks/finragbench_v_slice_v1")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--revision", default="d0d65255c94e687caa81ac9da7758ed25ff046a5")
    args = parser.parse_args()
    source = Path(args.source)
    queries = json.loads((source / "queries_en.json").read_text(encoding="utf-8"))
    qrels = {}
    for line in (source / "qrels_en.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        query_id, corpus_id, score = line.split("\t")
        qrels.setdefault(query_id, []).append({"corpus_id": corpus_id, "score": int(score)})
    selected = [item for item in queries if item["query-id"] in qrels][: args.limit]
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps({"query_id": item["query-id"], "query": item["query"], "answer": item.get("answer"), "category": item.get("category"), "from_pages": item.get("from_pages"), "qrels": qrels[item["query-id"]]}, ensure_ascii=False, sort_keys=True) + "\n" for item in selected)
    (output / "queries.jsonl").write_text(payload, encoding="utf-8")
    manifest = {"dataset_name": "FinRAGBench-V-Slice-v1", "source_dataset": "zhaosuifeng/FinRAGBench-V", "source_url": "https://huggingface.co/datasets/zhaosuifeng/FinRAGBench-V", "dataset_revision": args.revision, "license": "repository LICENSE; dataset terms must be checked before redistribution", "source_files": {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in ("queries_en.json", "qrels_en.tsv")}, "query_count": len(selected), "queries_sha256": hashlib.sha256(payload.encode()).hexdigest(), "pdf_status": "UNAVAILABLE_HF_ARCHIVE_TIMEOUT", "pdf_required": "pdfs_for_QA/pdf_en.tar.gz", "note": "Metadata and qrels are fixed; page-image metrics remain N/A until the revision-pinned PDF archive is obtained."}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
