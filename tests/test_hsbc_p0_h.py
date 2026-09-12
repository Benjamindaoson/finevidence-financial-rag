import hashlib

import pytest

from finevidence.benchmarks.hsbc import validate_hsbc_corpus_manifest


def test_hsbc_manifest_requires_hash_page_count_and_source_metadata(tmp_path):
    payload = b"pdf-like fixture"
    path = tmp_path / "report.pdf"
    path.write_bytes(payload)
    manifest = {
        "documents": [{
            "document_id": "hsbc-test",
            "official_source_url": "https://www.hsbc.com/test.pdf",
            "local_artifact_path": str(path),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "file_size": len(payload),
            "page_count": 1,
            "document_type": "Annual Report",
            "reporting_period": "FY2025",
            "issuer": "HSBC Holdings plc",
            "language": "en",
        }]
    }
    assert validate_hsbc_corpus_manifest(manifest) is None


def test_hsbc_manifest_rejects_wrong_hash(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"pdf-like fixture")
    with pytest.raises(ValueError, match="sha256"):
        validate_hsbc_corpus_manifest({"documents": [{"document_id": "x", "official_source_url": "https://www.hsbc.com/x.pdf", "local_artifact_path": str(path), "sha256": "bad", "file_size": 1, "page_count": 1, "document_type": "Annual Report", "reporting_period": "FY2025", "issuer": "HSBC", "language": "en"}]})
