from finevidence.chunking import DocumentBlock, StructureAwareChunker


def test_table_is_atomic_and_financial_metadata_is_preserved():
    chunker = StructureAwareChunker(chunk_size=40, overlap=10)
    blocks = [
        DocumentBlock(
            text="Reported revenue | 2025 | 42.1",
            page=8,
            block_id="table-1",
            kind="table",
            section_path=("Financial statements", "Revenue"),
            table_id="t1",
            row_id="reported-revenue",
            metadata={
                "entity": "HSBC Group",
                "metric": "revenue",
                "period": "2025",
                "currency": "USD",
                "unit": "billion",
                "accounting_basis": "reported",
                "scope": "Group",
                "source_type": "annual_report",
            },
        )
    ]

    result = chunker.chunk(
        blocks,
        document_id="hsbc-2025",
        source_uri="fixture://hsbc-2025",
    )

    assert len(result) == 1
    evidence = result[0]
    assert evidence.modality == "table"
    assert evidence.table_id == "t1"
    assert evidence.accounting_basis == "reported"
    assert evidence.currency == "USD"
    assert evidence.section_path == ("Financial statements", "Revenue")
    assert "accounting_basis: reported" in evidence.text


def test_long_text_respects_chunk_budget_with_overlap():
    chunker = StructureAwareChunker(chunk_size=12, overlap=3)
    block = DocumentBlock(
        text=" ".join(f"token{i}" for i in range(30)),
        page=1,
        block_id="b1",
        section_path=("MD&A",),
    )

    result = chunker.chunk(
        [block],
        document_id="d",
        source_uri="fixture://d",
    )

    assert len(result) > 1
    assert all(item.modality == "text" for item in result)
    assert result[0].block_id == "b1:c0"
