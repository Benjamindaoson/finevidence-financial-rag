from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from finevidence.contracts.table import TableIR
from finevidence.evidence.table_ir import parse_table


_NUMERIC = re.compile(r"^\(?[-–—$£€]?\d[\d,.]*(?:%|bn|m)?\)?[,.]?$|^[-–—]$", re.I)


def _is_numeric(text: str) -> bool:
    return bool(_NUMERIC.fullmatch(text.strip()))


def _group_rows(words: Iterable[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    tops: list[float] = []
    for word in sorted(words, key=lambda item: (float(item["top"]), float(item["x0"]))):
        top = float(word["top"])
        index = next((index for index, known in enumerate(tops) if abs(known - top) <= 2.0), None)
        if index is None:
            tops.append(top)
            groups.append([word])
        else:
            groups[index].append(word)
    return groups


def _nearest_anchor(x1: float, anchors: list[float]) -> int:
    return min(range(len(anchors)), key=lambda index: abs(x1 - anchors[index]))


def words_to_rows(words: list[dict[str, Any]], *, anchors: list[float]) -> tuple[list[list[str]], list[list[tuple[float, float, float, float] | None]]]:
    """Turn positioned PDF words into inferred row/column cells.

    This preserves positions observed by pdfplumber, but it cannot recover a
    semantic merged-cell graph without verified page-level annotations.
    """
    if not anchors:
        raise ValueError("at least one column anchor is required")
    rows: list[list[str]] = []
    boxes: list[list[tuple[float, float, float, float] | None]] = []
    for line in _group_rows(words):
        values = ["" for _ in range(len(anchors) + 1)]
        cell_words: list[list[dict[str, Any]]] = [[] for _ in values]
        for word in sorted(line, key=lambda item: float(item["x0"])):
            column = 0 if float(word["x0"]) < anchors[0] - 10 else _nearest_anchor(float(word["x0"]), anchors) + 1
            cell_words[column].append(word)
        for column, grouped in enumerate(cell_words):
            values[column] = " ".join(str(item["text"]).strip() for item in grouped).strip()
        rows.append(values)
        boxes.append([
            (min(float(item["x0"]) for item in grouped), min(float(item["top"]) for item in grouped), max(float(item["x1"]) for item in grouped), max(float(item["bottom"]) for item in grouped)) if grouped else None
            for grouped in cell_words
        ])
    return rows, boxes


def _anchors(words: list[dict[str, Any]], left: float) -> list[float]:
    positions = sorted(
        float(word["x0"])
        for word in words
        if float(word["x0"]) >= left - 4 and _is_numeric(str(word["text"]))
    )
    clusters: list[float] = []
    for x0 in positions:
        if not clusters or x0 - clusters[-1] > 14:
            clusters.append(x0)
        else:
            clusters[-1] = (clusters[-1] + x0) / 2
    return clusters


def _with_geometry(table: TableIR, boxes: list[list[tuple[float, float, float, float] | None]]) -> TableIR:
    cells = []
    for cell in table.cells:
        cell_box = boxes[cell.row_index][cell.column_index] if cell.row_index < len(boxes) and cell.column_index < len(boxes[cell.row_index]) else None
        cells.append(cell.model_copy(update={"bbox": cell_box}))
    present = [box for row in boxes for box in row if box]
    bbox = (min(box[0] for box in present), min(box[1] for box in present), max(box[2] for box in present), max(box[3] for box in present)) if present else None
    return table.model_copy(update={"cells": tuple(cells), "bbox": bbox})


def extract_pdf_tables(pdf_path: Path, *, pages: Iterable[int] | None = None, min_rows: int = 3) -> list[TableIR]:
    """Extract table-like regions from real PDF pages using pdfplumber geometry."""
    import pdfplumber

    wanted = set(pages) if pages is not None else None
    results: list[TableIR] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            if wanted is not None and page_number not in wanted:
                continue
            words = page.extract_words(x_tolerance=1, y_tolerance=3, keep_blank_chars=False)
            for table_number, found in enumerate(page.find_tables(), start=1):
                left, top, right, bottom = found.bbox
                if top < 20 or bottom - top < 30:
                    continue
                scoped = [word for word in words if float(word["top"]) >= top - 3 and float(word["bottom"]) <= bottom + 3 and 35 <= float(word["x0"]) <= right + 3 and float(word["x0"]) >= max(35, left - 230)]
                anchors = _anchors(scoped, left)
                if len(anchors) < 2:
                    continue
                rows, boxes = words_to_rows(scoped, anchors=anchors)
                if len(rows) < min_rows or sum(bool(value) for row in rows for value in row) < min_rows * 2:
                    continue
                source = {"uid": f"{pdf_path.stem}:p{page_number}:t{table_number}", "table": rows}
                table = parse_table(source, document_id=pdf_path.stem, page=page_number, source_record_id=source["uid"])
                results.append(_with_geometry(table, boxes))
    return results


def pdf_structure_summary(tables: list[TableIR]) -> dict[str, int | float | str]:
    if not tables:
        return {"table_count": 0, "page_count": 0, "cells_with_bbox_rate": "N/A", "header_path_rate": "N/A"}
    cells = [cell for table in tables for cell in table.cells]
    return {"table_count": len(tables), "page_count": len({(table.source_document_id, table.source_page) for table in tables}), "cells_with_bbox_rate": sum(cell.bbox is not None for cell in cells) / len(cells), "header_path_rate": sum(bool(cell.header_path) for cell in cells) / len(cells)}
