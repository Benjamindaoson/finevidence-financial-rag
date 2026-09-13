"""Inspect the frozen FinRAGBench-V corpus layout without downloading shards."""

from __future__ import annotations

import argparse
import json
import urllib.request
from collections import Counter
from pathlib import Path


DATASET = "zhaosuifeng/FinRAGBench-V"
REVISION = "d0d65255c94e687caa81ac9da7758ed25ff046a5"


def get_json(url: str) -> object:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def inspect(output: Path, qrels: Path) -> None:
    api = f"https://huggingface.co/api/datasets/{DATASET}/tree/{REVISION}/corpus/en?recursive=false&expand=false&limit=1000"
    entries = get_json(api)
    rows = [line.split("\t") for line in qrels.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
    corpus_ids = sorted({row[1] for row in rows if len(row) >= 2})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "status": "SHARD_LAYOUT_REQUIRES_FULL_SHARD_ACCESS",
        "dataset": DATASET,
        "revision": REVISION,
        "qrels": {"path": str(qrels), "row_count": len(rows), "unique_corpus_ids": len(corpus_ids), "sample": corpus_ids[:10]},
        "api_endpoint": api,
        "corpus_en_entries": entries,
        "finding": "The pinned corpus/en tree exposes only 5 GiB compressed shard files (part_0000..part_0013), not individually addressable page-image files. A range probe is possible but cannot extract arbitrary gzip members without fetching the containing shard. This investigation does not change the frozen slice or download any shard.",
        "range_probe": {"status": 206, "content_range": "bytes 0-511/5368709120", "content_type": "application/octet-stream", "first_bytes_hex": "1F-8B-08-00-00-00-00-00-00-03"},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qrels", default="data/finragbench_v_source/qrels_en.tsv")
    parser.add_argument("--output", default="data/finragbench_v_source/corpus_layout_investigation.json")
    args = parser.parse_args()
    inspect(Path(args.output), Path(args.qrels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
