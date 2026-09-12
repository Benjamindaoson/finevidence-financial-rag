from finevidence.benchmarks.public_sources import audit_public_sources


def test_public_source_audit_reports_repo_commit_file_hash_and_counts(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.json").write_text("[]", encoding="utf-8")

    result = audit_public_sources({"TAT-QA": {"repo": source, "files": ["sample.json"]}})

    item = result["TAT-QA"]["files"][0]
    assert item["relative_path"] == "sample.json"
    assert len(item["sha256"]) == 64
    assert item["byte_size"] == 2
    assert result["TAT-QA"]["status"] == "READY"
