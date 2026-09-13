"""Final RAG evaluation contracts.

These functions deliberately refuse to turn candidate annotations into scores.
The project has no human-verified annotation records yet, so every formal track
must remain ``N/A`` until the required rows are reviewed and promoted.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

NA = "N/A"


def _blocked(track: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"track": track, "status": "BLOCKED", "reason": reason, **extra}


def _verified(records: Iterable[Mapping[str, Any]]) -> bool:
    rows = list(records)
    return bool(rows) and all(row.get("human_verified") is True for row in rows)


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _as_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    return {str(item) for item in value}


def _accuracy(values: list[bool]) -> float | str:
    return sum(values) / len(values) if values else NA


def citation_metrics(
    gold_records: Iterable[Mapping[str, Any]],
    predicted_records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Score claim-to-citation mappings, only after all gold rows are verified.

    A citation is supported when its evidence id belongs to the claim's
    verified supporting set. Page/block/cell accuracy is evaluated only for
    claims that carry the corresponding gold location and prediction field.
    """

    gold = list(gold_records)
    predicted = {str(row["case_id"]): row for row in predicted_records if "case_id" in row}
    if not _verified(gold):
        return _blocked(
            "claim_citation",
            "HUMAN_VERIFICATION_REQUIRED",
            citation_precision=NA,
            citation_recall=NA,
            citation_f1=NA,
            claim_support_rate=NA,
            unsupported_citation_rate=NA,
            page_accuracy=NA,
            block_accuracy=NA,
            cell_accuracy=NA,
        )

    true_positive = predicted_total = gold_total = unsupported = 0
    supported_claims = 0
    page_values: list[bool] = []
    block_values: list[bool] = []
    cell_values: list[bool] = []
    for row in gold:
        case_id = str(row["case_id"])
        gold_ids = _as_set(row.get("supporting_evidence_ids"))
        pred = predicted.get(case_id, {})
        pred_ids = _as_set(pred.get("cited_evidence_ids"))
        overlap = gold_ids & pred_ids
        true_positive += len(overlap)
        predicted_total += len(pred_ids)
        gold_total += len(gold_ids)
        unsupported += len(pred_ids - gold_ids)
        supported_claims += bool(overlap)

        if row.get("page") is not None and pred.get("cited_pages") is not None:
            page_values.append(str(row["page"]) in _as_set(pred["cited_pages"]))
        if row.get("block_id") is not None and pred.get("cited_block_ids") is not None:
            block_values.append(str(row["block_id"]) in _as_set(pred["cited_block_ids"]))
        if row.get("cell_id") is not None and pred.get("cited_cell_ids") is not None:
            cell_values.append(str(row["cell_id"]) in _as_set(pred["cited_cell_ids"]))

    precision = true_positive / predicted_total if predicted_total else 0.0
    recall = true_positive / gold_total if gold_total else 0.0
    return {
        "track": "claim_citation",
        "status": "SCORED",
        "citation_precision": precision,
        "citation_recall": recall,
        "citation_f1": _f1(precision, recall),
        "claim_support_rate": supported_claims / len(gold),
        "unsupported_citation_rate": unsupported / predicted_total if predicted_total else 0.0,
        "page_accuracy": _accuracy(page_values),
        "block_accuracy": _accuracy(block_values),
        "cell_accuracy": _accuracy(cell_values),
        "claims": len(gold),
    }


def table_semantic_metrics(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Score semantic table labels without conflating structure and semantics."""

    records = list(rows)
    semantic_fields = (
        "cell_value_correct",
        "row_mapping_correct",
        "column_mapping_correct",
        "header_path_correct",
        "unit_correct",
        "period_correct",
        "entity_correct",
        "merged_semantics_correct",
        "footnote_association_correct",
    )
    if not _verified(records):
        return _blocked(
            "table_semantics",
            "HUMAN_VERIFICATION_REQUIRED",
            **{field: NA for field in semantic_fields},
            structure_recoverable_rate=NA,
        )

    result: dict[str, Any] = {
        "track": "table_semantics",
        "status": "SCORED",
        "structure_recoverable_rate": _accuracy(
            [bool(row["structure_recoverable"]) for row in records if row.get("structure_recoverable") is not None]
        ),
    }
    for field in semantic_fields:
        result[field] = _accuracy([bool(row[field]) for row in records if row.get(field) is not None])
    result["regions"] = len(records)
    return result


def answerability_metrics(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Score answer/retrieve-more/abstain decisions against verified labels."""

    rows = list(records)
    valid_statuses = {"ANSWERABLE", "PARTIAL_EVIDENCE", "UNANSWERABLE"}
    valid_actions = {"ANSWER", "RETRIEVE_MORE", "ABSTAIN"}
    if not _verified(rows):
        return _blocked(
            "answerability",
            "HUMAN_VERIFICATION_REQUIRED",
            answerability_accuracy=NA,
            abstention_precision=NA,
            abstention_recall=NA,
            abstention_f1=NA,
            false_answer_rate=NA,
            false_abstention_rate=NA,
            partial_detection_rate=NA,
        )
    if any(row.get("answerability") not in valid_statuses or row.get("action") not in valid_actions for row in rows):
        return _blocked("answerability", "INVALID_LABEL")

    expected_action = {
        "ANSWERABLE": "ANSWER",
        "PARTIAL_EVIDENCE": "RETRIEVE_MORE",
        "UNANSWERABLE": "ABSTAIN",
    }
    correct = sum(row["action"] == expected_action[row["answerability"]] for row in rows)
    gold_abstain = sum(row["answerability"] == "UNANSWERABLE" for row in rows)
    pred_abstain = sum(row["action"] == "ABSTAIN" for row in rows)
    abstain_tp = sum(row["answerability"] == "UNANSWERABLE" and row["action"] == "ABSTAIN" for row in rows)
    abstain_precision = abstain_tp / pred_abstain if pred_abstain else 0.0
    abstain_recall = abstain_tp / gold_abstain if gold_abstain else 0.0
    non_answerable = [row for row in rows if row["answerability"] != "ANSWERABLE"]
    answerable = [row for row in rows if row["answerability"] == "ANSWERABLE"]
    return {
        "track": "answerability",
        "status": "SCORED",
        "answerability_accuracy": correct / len(rows),
        "abstention_precision": abstain_precision,
        "abstention_recall": abstain_recall,
        "abstention_f1": _f1(abstain_precision, abstain_recall),
        "false_answer_rate": sum(row["action"] == "ANSWER" for row in non_answerable) / len(non_answerable)
        if non_answerable
        else NA,
        "false_abstention_rate": sum(row["action"] == "ABSTAIN" for row in answerable) / len(answerable)
        if answerable
        else NA,
        "partial_detection_rate": sum(
            row["answerability"] == "PARTIAL_EVIDENCE" and row["action"] == "RETRIEVE_MORE" for row in rows
        )
        / sum(row["answerability"] == "PARTIAL_EVIDENCE" for row in rows)
        if any(row["answerability"] == "PARTIAL_EVIDENCE" for row in rows)
        else NA,
        "cases": len(rows),
    }
