from __future__ import annotations

import re
from typing import Any

from finevidence.contracts.table import TableCell, TableIR


_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_UNIT = re.compile(r"\b(?:USD|US\s*dollars?|EUR|GBP|million|billion|bn|mm|%)\b", re.I)


def _rows(source: Any) -> list[list[str]]:
    raw = source.get("table", []) if isinstance(source, dict) else source
    return [[str(value) for value in row] for row in raw]


def _header_count(rows: list[list[str]]) -> int:
    for index, row in enumerate(rows[1:], start=1):
        values = [value.strip() for value in row if value.strip()]
        has_period = any(_YEAR.search(value) for value in values)
        has_label = any(not _YEAR.fullmatch(value) for value in values)
        if has_period and has_label:
            return index + 1
    return min(1, len(rows))


def parse_table(source: dict, *, document_id: str, page: int = 1, source_record_id: str | None = None) -> TableIR:
    rows = _rows(source)
    if not rows or not any(value.strip() for row in rows for value in row):
        raise ValueError("table must contain at least one non-empty cell")
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    table_id = str(source.get("uid") or source_record_id or f"{document_id}:table")
    header_count = _header_count(padded)
    header_rows = tuple(range(header_count))
    column_ids = tuple(f"{table_id}:c{column}" for column in range(width))
    row_ids = tuple(f"{table_id}:r{index}" for index in range(len(padded)))
    cells: list[TableCell] = []
    for row_index, row in enumerate(padded):
        for column_index, raw_value in enumerate(row):
            value = raw_value.strip()
            header_path = []
            for header_row in range(min(row_index, header_count)):
                candidate = padded[header_row][column_index].strip()
                if candidate:
                    header_path.append(candidate)
            header_path = list(dict.fromkeys(header_path))
            unit_match = _UNIT.search(" ".join(header_path))
            period_match = _YEAR.search(" ".join(header_path) + " " + value)
            cells.append(TableCell(
                cell_id=f"{table_id}:r{row_index}:c{column_index}", table_id=table_id,
                row_id=row_ids[row_index], column_id=column_ids[column_index],
                row_index=row_index, column_index=column_index, value=value,
                is_header=row_index < header_count, header_path=tuple(header_path),
                unit=unit_match.group(0) if unit_match else None,
                period=period_match.group(0) if period_match else None,
                source_document_id=document_id, source_page=page,
            ))
    return TableIR(
        table_id=table_id, source_document_id=document_id, source_page=page,
        header_rows=header_rows, row_ids=row_ids, column_ids=column_ids,
        cells=tuple(cells), source_record_id=str(source_record_id or table_id),
    )


def roundtrip_values(table: TableIR) -> list[list[str]]:
    grid = [["" for _ in table.column_ids] for _ in table.row_ids]
    for cell in table.cells:
        grid[cell.row_index][cell.column_index] = cell.value
    return grid


def table_structure_invariants(table: TableIR, source: dict) -> dict[str, bool | int | str]:
    source_rows = _rows(source)
    expected = [row + [""] * (len(table.column_ids) - len(row)) for row in source_rows]
    actual = roundtrip_values(table)
    return {
        "table_id_present": bool(table.table_id),
        "cell_identity_unique": len({cell.cell_id for cell in table.cells}) == len(table.cells),
        "row_column_relations_present": all(cell.row_id and cell.column_id for cell in table.cells),
        "cell_count": len(table.cells),
        "row_count": len(table.row_ids),
        "column_count": len(table.column_ids),
        "raw_value_roundtrip": actual == expected,
        "source_cell_count": sum(len(row) for row in source_rows),
        "caption": "N/A" if table.caption is None else "AVAILABLE",
        "footnotes": "N/A" if not table.footnote_ids else "AVAILABLE",
        "bbox": "N/A" if table.bbox is None else "AVAILABLE",
    }
