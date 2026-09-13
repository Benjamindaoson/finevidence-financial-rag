from __future__ import annotations

import argparse
import hashlib
import json
import platform
import traceback
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Download only the FinRAGBench-V PDF archive with the official HF cache client.")
    parser.add_argument("--revision", default="d0d65255c94e687caa81ac9da7758ed25ff046a5")
    parser.add_argument("--cache-dir", default="artifacts/hf_cache")
    parser.add_argument("--output-dir", default="artifacts/finragbench_v_source/downloads")
    parser.add_argument("--manifest", default="benchmarks/finragbench_v_slice_v1/manifest.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cache_dir = root / args.cache_dir
    output_dir = root / args.output_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    record = {"dataset": "zhaosuifeng/FinRAGBench-V", "revision": args.revision, "filename": "pdfs_for_QA/pdf_en.tar.gz", "started_at": started, "cache_dir": str(cache_dir.resolve()), "output_dir": str(output_dir.resolve()), "python": platform.python_version(), "platform": platform.platform()}
    try:
        from huggingface_hub import hf_hub_download

        path = Path(hf_hub_download(repo_id=record["dataset"], repo_type="dataset", filename=record["filename"], revision=args.revision, cache_dir=str(cache_dir), local_dir=str(output_dir), force_download=False))
        record.update({"status": "DOWNLOADED", "path": str(path.resolve()), "size_bytes": path.stat().st_size, "sha256": _sha256(path), "completed_at": datetime.now(timezone.utc).isoformat()})
        manifest_path = root / args.manifest
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update({"dataset_revision": args.revision, "pdf_status": "DOWNLOADED_OFFICIAL_HF_CACHE", "pdf_archive_sha256": record["sha256"], "pdf_archive_size_bytes": record["size_bytes"]})
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, ensure_ascii=False))
        return 0
    except Exception as exc:
        record.update({"status": "BLOCKED", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(), "completed_at": datetime.now(timezone.utc).isoformat()})
        (root / "data/finragbench_v_source").mkdir(parents=True, exist_ok=True)
        (root / "data/finragbench_v_source/download_blocker.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
