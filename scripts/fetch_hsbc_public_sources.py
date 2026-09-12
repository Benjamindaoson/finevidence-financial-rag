from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


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
    output_root.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for index, document in enumerate(manifest["documents"], start=1):
        suffix = Path(document["source_url"].split("?", 1)[0]).suffix or ".bin"
        output = output_root / f"{index:02d}-{document['document_type'].lower().replace(' ', '-')}-{document['reporting_period']}{suffix}"
        request = Request(document["source_url"], headers={"User-Agent": "finevidence-provenance-fetch/0.1"})
        with urlopen(request, timeout=60) as response:
            payload = response.read()
        output.write_bytes(payload)
        downloaded.append({**document, "local_path": str(output), "sha256": hashlib.sha256(payload).hexdigest(), "downloaded_at": datetime.now(timezone.utc).isoformat()})
    result = output_root / "manifest.json"
    result.write_text(json.dumps({"source_page": manifest["source_page"], "documents": downloaded}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


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
