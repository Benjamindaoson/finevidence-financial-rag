from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from finevidence.contracts.evidence import Evidence


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _page_count(path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(str(path), strict=False).pages)


def validate_hsbc_corpus_manifest(manifest: dict) -> None:
    for document in manifest.get("documents", []):
        required = ("document_id", "official_source_url", "local_artifact_path", "sha256", "file_size", "page_count", "document_type", "reporting_period", "issuer", "language")
        missing = [field for field in required if field not in document]
        if missing:
            raise ValueError(f"missing HSBC provenance fields: {missing}")
        if not document["official_source_url"].startswith("https://www.hsbc.com/"):
            raise ValueError("HSBC source URL is not official")
        path = Path(document["local_artifact_path"])
        if not path.exists():
            raise ValueError(f"HSBC local artifact missing: {path}")
        if _sha256(path) != document["sha256"]:
            raise ValueError("HSBC sha256 mismatch")
        if path.stat().st_size != document["file_size"]:
            raise ValueError("HSBC file_size mismatch")
        if document["page_count"] < 1:
            raise ValueError("HSBC page_count must be positive")


def download_hsbc_corpus(source_manifest_path: str | Path | dict, output_dir: str | Path) -> dict:
    source = source_manifest_path if isinstance(source_manifest_path, dict) else json.loads(Path(source_manifest_path).read_text(encoding="utf-8"))
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    documents = []
    for index, item in enumerate(source["documents"], start=1):
        document_id = f"hsbc-{item['reporting_period'].lower()}-{item['document_type'].lower().replace(' ', '-') }"
        path = output_root / f"{index:02d}-{document_id}.pdf"
        request = Request(item["source_url"], headers={"User-Agent": "finevidence-p0-h/0.1"})
        with urlopen(request, timeout=120) as response:
            path.write_bytes(response.read())
        documents.append({
            "document_id": document_id,
            "official_source_url": item["source_url"],
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "sha256": _sha256(path),
            "file_size": path.stat().st_size,
            "page_count": _page_count(path),
            "document_type": item["document_type"],
            "reporting_period": item["reporting_period"],
            "issuer": "HSBC Holdings plc",
            "language": "en",
            "local_artifact_path": str(path.resolve()),
        })
    manifest = {"source_page": source["source_page"], "generated_at": datetime.now(timezone.utc).isoformat(), "documents": documents}
    validate_hsbc_corpus_manifest(manifest)
    manifest_path = output_root / "hsbc_corpus_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_hsbc_pdf(path: str | Path, document: dict) -> list[Evidence]:
    from pypdf import PdfReader

    evidence = []
    for page_number, page in enumerate(PdfReader(str(path), strict=False).pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        evidence.append(Evidence.from_content(document_id=document["document_id"], source_uri=document["official_source_url"], page=page_number, block_id=f"page-{page_number}", modality="text", text=text, evidence_id=f"{document['document_id']}:p{page_number}:page"))
    return evidence


def build_hsbc_evidence(manifest: dict) -> list[Evidence]:
    validate_hsbc_corpus_manifest(manifest)
    evidence = []
    for document in manifest["documents"]:
        evidence.extend(parse_hsbc_pdf(document["local_artifact_path"], document))
    return evidence
