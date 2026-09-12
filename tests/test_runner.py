import json
from pathlib import Path

from finevidence.eval.run import run_once


def _benchmark(root: Path):
    root.mkdir()
    evidence = {
        "document_id": "d1",
        "source_uri": "fixture://d1",
        "page": 1,
        "block_id": "b1",
        "modality": "text",
        "text": "Revenue is 100 million.",
    }
    question = {
        "question_id": "q1",
        "question": "What is revenue?",
        "gold_answer": "100 million",
        "required_evidence": [{"evidence_id": "d1:p1:b1"}],
        "required_facts": ["revenue"],
        "failure_type": "TEXT_FACTUAL",
        "answerable": True,
    }
    (root / "evidence.jsonl").write_text(json.dumps(evidence) + "\n", encoding="utf-8")
    (root / "questions.jsonl").write_text(json.dumps(question) + "\n", encoding="utf-8")
    from hashlib import sha256

    manifest = {
        "benchmark_version": "mini-v1",
        "evidence_file": "evidence.jsonl",
        "questions_file": "questions.jsonl",
        "evidence_count": 1,
        "question_count": 1,
        "files": {
            name: sha256((root / name).read_bytes()).hexdigest()
            for name in ("evidence.jsonl", "questions.jsonl")
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_runner_saves_required_artifacts_and_never_overwrites(tmp_path):
    benchmark_root = tmp_path / "benchmark"
    _benchmark(benchmark_root)
    config = {
        "benchmark_root": str(benchmark_root),
        "artifact_root": str(tmp_path / "runs"),
        "top_k": 3,
        "baselines": ["B0", "B1", "B2", "B3"],
    }

    first = run_once(config)
    second = run_once(config)

    required = {"config.json", "dataset_manifest.json", "predictions.jsonl", "metrics.json", "failure_cases.jsonl"}
    assert required <= {path.name for path in first.iterdir()}
    assert first != second
    assert "git_commit" in json.loads((first / "config.json").read_text(encoding="utf-8"))
    assert json.loads((first / "metrics.json").read_text(encoding="utf-8"))["B3"]["status"] == "N/A"
