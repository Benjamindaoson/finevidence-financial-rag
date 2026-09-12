import json

from scripts.fetch_hsbc_public_sources import load_manifest


def test_hsbc_manifest_contains_official_urls_without_document_payloads():
    manifest = load_manifest("data/hsbc_public_sources.json")

    assert manifest["source_page"].startswith("https://www.hsbc.com/")
    assert manifest["documents"]
    assert all(item["source_url"].startswith("https://www.hsbc.com/") for item in manifest["documents"])
    assert all("content" not in item and "bytes" not in item for item in manifest["documents"])
