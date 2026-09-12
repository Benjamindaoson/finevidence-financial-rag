import json
from pathlib import Path

import pytest

from finevidence.benchmarks.loader import load_benchmark, verify_manifest


def _write_fixture(root: Path, text: str = "Revenue is 100.") -> None:
    root.mkdir(exist_ok=True)
    (root / "evidence.jsonl").write_text(
        json.dumps(
            {
                "evidence_id": "e-1",
                "document_id": "doc-1",
                "source_uri": "fixture://doc-1",
                "page": 1,
                "block_id": "b-1",
                "modality": "text",
                "text": text,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "questions.jsonl").write_text(
        json.dumps(
            {
                "question_id": "q-1",
                "question": "What is revenue?",
                "gold_answer": "100",
                "required_evidence": [{"evidence_id": "e-1"}],
                "required_facts": ["revenue"],
                "failure_type": "TEXT_FACTUAL",
                "answerable": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "benchmark_version": "mini-v1",
                "evidence_file": "evidence.jsonl",
                "questions_file": "questions.jsonl",
                "evidence_count": 1,
                "question_count": 1,
                "files": {},
            }
        ),
        encoding="utf-8",
    )


def test_loader_verifies_manifest_and_loads_typed_cases(tmp_path):
    _write_fixture(tmp_path)
    benchmark = load_benchmark(tmp_path)

    assert len(benchmark.evidence) == 1
    assert benchmark.cases[0].required_evidence[0].evidence_id == "e-1"
    assert benchmark.manifest["question_count"] == 1


def test_loader_rejects_changed_source_after_manifest_is_frozen(tmp_path):
    _write_fixture(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    from hashlib import sha256

    for name in ("evidence.jsonl", "questions.jsonl"):
        manifest["files"][name] = sha256((tmp_path / name).read_bytes()).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "evidence.jsonl").write_text(
        (tmp_path / "evidence.jsonl").read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="manifest mismatch"):
        verify_manifest(tmp_path)


def test_unanswerable_case_is_allowed_by_loader(tmp_path):
    _write_fixture(tmp_path)
    question_path = tmp_path / "questions.jsonl"
    question_path.write_text(
        json.dumps(
            {
                "question_id": "q-unknown",
                "question": "Unknown?",
                "gold_answer": None,
                "required_evidence": [],
                "required_facts": [],
                "failure_type": "INSUFFICIENT_EVIDENCE",
                "answerable": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    manifest["question_count"] = 1
    from hashlib import sha256

    manifest["files"] = {
        name: sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in ("evidence.jsonl", "questions.jsonl")
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    assert load_benchmark(tmp_path).cases[0].answerable is False
