from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from finevidence.contracts.benchmark import FactRequirement, MiniCase, RequiredEvidenceRef
from finevidence.contracts.evidence import Evidence


def _table_rows(table: Any) -> list[list[str]]:
    raw = table.get("table", []) if isinstance(table, dict) else table
    return [[str(cell) for cell in row] for row in raw]


def _table_text(table: Any) -> str:
    return "\n".join(" | ".join(row) for row in _table_rows(table))


def _evidence(case_id: str, page: int, block_id: str, modality: str, text: str, **metadata) -> Evidence:
    return Evidence.from_content(
        document_id=case_id,
        source_uri=f"fixture://{case_id}",
        page=page,
        block_id=block_id,
        modality=modality,
        text=text,
        evidence_id=f"{case_id}:{block_id}",
        **metadata,
    )


def project_tatqa_record(record: dict, question: dict, report_id: str, split: str) -> tuple[list[Evidence], MiniCase]:
    evidence = [_evidence(f"tatqa:{report_id}", 1, "table", "table", _table_text(record["table"]), table_id=record["table"].get("uid", report_id))]
    paragraphs = {}
    for paragraph in record.get("paragraphs", []):
        order = str(paragraph["order"])
        paragraphs[order] = _evidence(
            f"tatqa:{report_id}", int(paragraph["order"]), f"paragraph:{order}", "text", paragraph["text"]
        )
        evidence.append(paragraphs[order])
    answer_from = question.get("answer_from", "")
    refs: list[RequiredEvidenceRef] = []
    if "table" in answer_from:
        refs.append(RequiredEvidenceRef(evidence_id=f"tatqa:{report_id}:table"))
    if "text" in answer_from:
        refs.extend(RequiredEvidenceRef(evidence_id=paragraphs[order].evidence_id) for order in question.get("rel_paragraphs", []) if order in paragraphs)
    facts = [
        FactRequirement(
            fact_id=f"{question['uid']}-F{index}",
            description=next(item.text for item in evidence if item.evidence_id == ref.evidence_id),
            acceptable_evidence_ids=[ref.evidence_id],
        )
        for index, ref in enumerate(refs, start=1)
    ]
    case = MiniCase(
        question_id=f"tatqa:{question['uid']}",
        question=question["question"],
        gold_answer=json.dumps(question.get("answer"), ensure_ascii=False),
        required_evidence=refs,
        required_facts=facts,
        failure_type="REAL_FINANCE_TATQA",
        answerable=bool(refs),
        source_dataset="TAT-QA",
        source_split=split,
        source_record_id=report_id,
        source_question_id=question["uid"],
        gold_supporting_facts={key: question.get(key) for key in ("answer", "answer_from", "rel_paragraphs", "derivation", "answer_type", "scale")},
        gold_execution_answer=question.get("answer"),
        source_metadata={"report_table_uid": record["table"].get("uid")},
    )
    return evidence, case


def _finqa_text_id(record_id: str, key: str, pre_count: int, post_count: int) -> str | None:
    match = re.fullmatch(r"text_(\d+)", key)
    if not match:
        return None
    index = int(match.group(1))
    if index < pre_count:
        return f"finqa:{record_id}:text:pre:{index}"
    if index - pre_count < post_count:
        return f"finqa:{record_id}:text:post:{index - pre_count}"
    return None


def project_finqa_record(record: dict, split: str) -> tuple[list[Evidence], MiniCase]:
    record_id = record["id"]
    rows = _table_rows(record.get("table", []))
    header = rows[0] if rows else []
    evidence = []
    for index, row in enumerate(rows):
        values = [f"{header[column]}: {cell}" for column, cell in enumerate(row)] if index else row
        evidence.append(_evidence(f"finqa:{record_id}", 1, f"table:{index}", "table", " | ".join(values), table_id=record_id, row_id=str(index)))
    pre = record.get("pre_text", [])
    post = record.get("post_text", [])
    for index, text in enumerate(pre):
        evidence.append(_evidence(f"finqa:{record_id}", 1, f"text:pre:{index}", "text", text))
    for index, text in enumerate(post):
        evidence.append(_evidence(f"finqa:{record_id}", 1, f"text:post:{index}", "text", text))
    gold_inds = record["qa"].get("gold_inds", {})
    refs = []
    unmatched = []
    for key, description in gold_inds.items():
        if key.startswith("table_"):
            evidence_id = f"finqa:{record_id}:table:{key.removeprefix('table_')}"
        else:
            evidence_id = _finqa_text_id(record_id, key, len(pre), len(post))
        if evidence_id and any(item.evidence_id == evidence_id for item in evidence):
            refs.append(RequiredEvidenceRef(evidence_id=evidence_id))
        else:
            unmatched.append(key)
    facts = [
        FactRequirement(fact_id=f"{record_id}-F{index}", description=description, acceptable_evidence_ids=[refs[index - 1].evidence_id])
        for index, description in enumerate(gold_inds.values(), start=1)
        if index <= len(refs)
    ]
    qa = record["qa"]
    case = MiniCase(
        question_id=f"finqa:{record_id}",
        question=qa["question"],
        gold_answer=str(qa.get("answer", "")),
        required_evidence=refs,
        required_facts=facts,
        failure_type="REAL_FINANCE_FINQA",
        answerable=bool(refs) and not unmatched,
        source_dataset="FinQA",
        source_split=split,
        source_record_id=record_id,
        source_question_id=record_id,
        gold_supporting_facts=gold_inds,
        reasoning_program=qa.get("program"),
        gold_execution_answer=qa.get("exe_ans"),
        source_metadata={"unmatched_gold_ind_keys": unmatched},
    )
    return evidence, case


def _commit(path: Path) -> str:
    repo = path.parents[1] if path.parent.name in {"dataset", "dataset_raw"} else path.parent
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "N/A"


def build_real_finance_slice(tatqa_path: Path, finqa_path: Path, output_root: Path, tatqa_limit: int = 50, finqa_limit: int = 50) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    tatqa_data = json.loads(Path(tatqa_path).read_text(encoding="utf-8"))
    finqa_data = json.loads(Path(finqa_path).read_text(encoding="utf-8"))
    all_evidence: dict[str, Evidence] = {}
    cases: list[MiniCase] = []
    tatqa_count = 0
    for report_index, report in enumerate(tatqa_data):
        for question in report.get("questions", []):
            if tatqa_count >= tatqa_limit or question.get("answer_from") != "table-text":
                continue
            items, case = project_tatqa_record(report, question, str(report_index), "dev")
            all_evidence.update({item.evidence_id: item for item in items})
            cases.append(case)
            tatqa_count += 1
        if tatqa_count >= tatqa_limit:
            break
    finqa_count = 0
    for record in finqa_data:
        if finqa_count >= finqa_limit:
            break
        items, case = project_finqa_record(record, "dev")
        if not case.answerable:
            continue
        all_evidence.update({item.evidence_id: item for item in items})
        cases.append(case)
        finqa_count += 1
    evidence_path = output_root / "evidence.jsonl"
    questions_path = output_root / "questions.jsonl"
    evidence_path.write_text("".join(json.dumps(item.model_dump(), ensure_ascii=False) + "\n" for item in all_evidence.values()), encoding="utf-8")
    questions_path.write_text("".join(json.dumps(case.model_dump(), ensure_ascii=False) + "\n" for case in cases), encoding="utf-8")
    manifest = {
        "benchmark_id": "RealFinance-v1",
        "version": "1.0.0",
        "evidence_file": "evidence.jsonl",
        "questions_file": "questions.jsonl",
        "evidence_count": len(all_evidence),
        "question_count": len(cases),
        "selection": {"TAT-QA": tatqa_count, "FinQA": finqa_count, "TAT-QA_rule": "first table-text questions in dev order", "FinQA_rule": "first answerable dev records in order"},
        "sources": {
            "TAT-QA": {"path": str(Path(tatqa_path)), "commit": _commit(Path(tatqa_path)), "sha256": hashlib.sha256(Path(tatqa_path).read_bytes()).hexdigest()},
            "FinQA": {"path": str(Path(finqa_path)), "commit": _commit(Path(finqa_path)), "sha256": hashlib.sha256(Path(finqa_path).read_bytes()).hexdigest()},
        },
        "files": {
            "evidence.jsonl": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            "questions.jsonl": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
        },
    }
    (output_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_root
