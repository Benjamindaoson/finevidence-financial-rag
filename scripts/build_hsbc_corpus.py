from __future__ import annotations

import argparse
import json
from pathlib import Path

from finevidence.benchmarks.hsbc import build_hsbc_evidence, download_hsbc_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and minimally parse the fixed official HSBC P0-H corpus.")
    parser.add_argument("--source-manifest", default="data/hsbc_public_sources.json")
    parser.add_argument("--output", default="artifacts/hsbc_local_sources")
    args = parser.parse_args()
    manifest_path = Path(args.output) / "hsbc_corpus_manifest.json"
    if not manifest_path.exists():
        download_hsbc_corpus(args.source_manifest, args.output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    evidence = build_hsbc_evidence(manifest)
    evidence_path = Path(args.output) / "hsbc_evidence.jsonl"
    evidence_path.write_text("".join(item.model_dump_json() + "\n" for item in evidence), encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path.resolve()), "evidence": str(evidence_path.resolve()), "evidence_count": len(evidence)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
