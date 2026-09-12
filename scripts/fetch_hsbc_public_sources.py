from __future__ import annotations

import argparse
import json
from pathlib import Path

from finevidence.benchmarks.hsbc import download_hsbc_corpus


def load_manifest(path: str | Path) -> dict:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if not manifest.get("source_page", "").startswith("https://www.hsbc.com/"):
        raise ValueError("source_page must be an official HSBC URL")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("documents must be a non-empty list")
    for document in documents:
        if not document.get("source_url", "").startswith("https://www.hsbc.com/"):
            raise ValueError("every source_url must be an official HSBC URL")
        for field in ("document_type", "reporting_period"):
            if not document.get(field):
                raise ValueError(f"missing {field}")
    return manifest


def fetch(manifest: dict, output_root: Path) -> Path:
    result = download_hsbc_corpus(Path("data/hsbc_public_sources.json"), output_root)
    path = output_root / "hsbc_corpus_manifest.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in fetcher for official HSBC source documents; files stay local and ignored.")
    parser.add_argument("--manifest", default="data/hsbc_public_sources.json")
    parser.add_argument("--output", default="artifacts/hsbc_local_sources")
    parser.add_argument("--download", action="store_true", help="download files; without this flag only validate the manifest")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    if not args.download:
        print(f"validated {len(manifest['documents'])} official HSBC document URLs; no files downloaded")
        return 0
    print(fetch(manifest, Path(args.output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
