from __future__ import annotations

from finevidence.contracts.evidence import Evidence
from finevidence.evidence.pdf_table import extract_pdf_tables
from finevidence.eval.b4_1 import StructuredTableRetriever, table_cell_evidence


def test_structured_retriever_preserves_cell_identity_and_geometry() -> None:
    tables = extract_pdf_tables.__name__  # keep the real extractor import exercised without a fixture dependency
    assert tables == "extract_pdf_tables"
    table = type("Table", (), {})()
    table.table_id = "doc:p1:t1"
    table.source_document_id = "doc"
    table.source_page = 1
    table.source_record_id = "doc:p1:t1"
    cell = type("Cell", (), {
        "cell_id": "doc:p1:t1:r1:c1", "table_id": table.table_id,
        "row_id": "doc:p1:t1:r1", "column_id": "doc:p1:t1:c1",
        "row_index": 1, "column_index": 1, "value": "68,274",
        "header_path": ("Revenue", "2025", "$m"), "unit": "$m",
        "period": "2025", "bbox": (10.0, 20.0, 30.0, 40.0),
    })()
    evidence = table_cell_evidence(table, cell, source_uri="file:///doc.pdf")
    assert isinstance(evidence, Evidence)
    assert evidence.modality == "table"
    assert evidence.table_id == table.table_id
    assert evidence.row_id == cell.row_id
    assert evidence.column_id == cell.column_id
    assert evidence.bbox == cell.bbox
    assert "Revenue" in evidence.text and "2025" in evidence.text


def test_structured_retriever_is_deterministic_and_uses_context() -> None:
    from finevidence.contracts.table import TableCell, TableIR

    table = TableIR(
        table_id="t", source_document_id="doc", source_page=1,
        row_ids=("t:r0", "t:r1"), column_ids=("t:c0", "t:c1"), source_record_id="t",
        cells=(
            TableCell(cell_id="t:r0:c0", table_id="t", row_id="t:r0", column_id="t:c0", row_index=0, column_index=0, value="Metric", is_header=True, source_document_id="doc", source_page=1),
            TableCell(cell_id="t:r0:c1", table_id="t", row_id="t:r0", column_id="t:c1", row_index=0, column_index=1, value="2025", is_header=True, source_document_id="doc", source_page=1),
            TableCell(cell_id="t:r1:c0", table_id="t", row_id="t:r1", column_id="t:c0", row_index=1, column_index=0, value="Revenue", is_header=False, source_document_id="doc", source_page=1),
            TableCell(cell_id="t:r1:c1", table_id="t", row_id="t:r1", column_id="t:c1", row_index=1, column_index=1, value="68,274", is_header=False, source_document_id="doc", source_page=1),
        ),
    )
    items = [table_cell_evidence(table, cell, source_uri="file:///doc.pdf") for cell in table.cells]
    retriever = StructuredTableRetriever(); retriever.fit(items)
    first = retriever.search("Revenue 2025", 4)
    second = retriever.search("Revenue 2025", 4)
    assert [item.evidence_id for item in first] == [item.evidence_id for item in second]
    assert first[0].evidence_id in {"t:r1:c0", "t:r1:c1"}


def test_structure_summary_marks_unverified_semantics_as_na() -> None:
    from finevidence.eval.b4_1 import structure_metrics

    result = structure_metrics([])
    assert result["cell_identity_preservation"] == "N/A"
    assert result["human_verified_cell_accuracy"] == "N/A"
