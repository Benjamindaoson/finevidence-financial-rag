from __future__ import annotations

import hashlib
import json
from pathlib import Path

from finevidence.contracts.benchmark import Benchmark, MiniCase
from finevidence.contracts.evidence import Evidence


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(root: Path) -> None:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    for name, expected in files.items():
        path = root / name
        if not path.exists() or _sha256(path) != expected:
            raise ValueError(f"manifest mismatch: {name}")

    evidence_file = root / manifest["evidence_file"]
    questions_file = root / manifest["questions_file"]
    evidence_count = sum(1 for line in evidence_file.read_text(encoding="utf-8").splitlines() if line.strip())
    question_count = sum(1 for line in questions_file.read_text(encoding="utf-8").splitlines() if line.strip())
    if evidence_count != manifest["evidence_count"]:
        raise ValueError("manifest mismatch: evidence_count")
    if question_count != manifest["question_count"]:
        raise ValueError("manifest mismatch: question_count")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_benchmark(root: Path) -> Benchmark:
    root = Path(root)
    verify_manifest(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    evidence = [Evidence.from_content(**raw) for raw in _read_jsonl(root / manifest["evidence_file"])]
    cases = [MiniCase.model_validate(raw) for raw in _read_jsonl(root / manifest["questions_file"])]
    ids = {item.evidence_id for item in evidence}
    unknown = {
        ref.evidence_id
        for case in cases
        for ref in case.required_evidence
        if ref.evidence_id not in ids
    }
    if unknown:
        raise ValueError(f"unknown required evidence: {sorted(unknown)}")
    return Benchmark(evidence=evidence, cases=cases, manifest=manifest)
