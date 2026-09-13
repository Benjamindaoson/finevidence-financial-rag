from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_document(document: dict, output_dir: Path, dpi: int = 72, pages: list[int] | None = None) -> list[dict]:
    pdf = Path(document["local_artifact_path"])
    output_dir.mkdir(parents=True, exist_ok=True)
    page_count = int(document["page_count"])
    wanted = pages or list(range(1, page_count + 1))
    rows = []
    for page in wanted:
        image_path = output_dir / f"{document['document_id']}-p{page:04d}.png"
        if not image_path.exists():
            base = image_path.with_suffix("")
            subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", str(dpi), "-singlefile", str(pdf), str(base)], check=True, capture_output=True)
        with Image.open(image_path) as image:
            width, height = image.size
        rows.append({"page_image_id": f"{document['document_id']}:p{page}:image", "document_id": document["document_id"], "page": page, "image_path": str(image_path.resolve()), "image_sha256": sha256(image_path), "width": width, "height": height, "dpi": dpi, "render_version": "pdftoppm-24.08/png", "source_pdf_sha256": document["sha256"]})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="artifacts/hsbc_local_sources/hsbc_corpus_manifest.json")
    parser.add_argument("--output", default="artifacts/hsbc_page_images")
    parser.add_argument("--dpi", type=int, default=72)
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    rows = []
    for document in manifest["documents"]:
        rows.extend(render_document(document, Path(args.output), args.dpi))
    output = Path(args.output) / "page_render_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"render_version": "pdftoppm-24.08/png", "dpi": args.dpi, "source_documents": manifest["documents"], "pages": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(output.resolve()), "page_count": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
