from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TableCell(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cell_id: str
    table_id: str
    row_id: str
    column_id: str
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    value: str
    is_header: bool
    header_path: tuple[str, ...] = ()
    unit: str | None = None
    period: str | None = None
    entity: str | None = None
    metric: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    source_document_id: str
    source_page: int = Field(ge=1)


class TableIR(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    table_id: str
    source_document_id: str
    source_page: int = Field(ge=1)
    caption: str | None = None
    header_rows: tuple[int, ...] = ()
    row_ids: tuple[str, ...]
    column_ids: tuple[str, ...]
    cells: tuple[TableCell, ...]
    footnote_ids: tuple[str, ...] = ()
    bbox: tuple[float, float, float, float] | None = None
    source_record_id: str
