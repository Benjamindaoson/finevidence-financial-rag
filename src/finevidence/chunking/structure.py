from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Literal

from finevidence.contracts.evidence import Evidence


BlockKind = Literal["text", "table"]


@dataclass(frozen=True)
class DocumentBlock:
    text: str
    page: int
    block_id: str
    kind: BlockKind = "text"
    section_path: tuple[str, ...] = ()
    table_id: str | None = None
    row_id: str | None = None
    column_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class StructureAwareChunker:
    """Structure-preserving chunker for financial documents.

    Text blocks are packed within a token budget without crossing table
    boundaries. Tables are emitted atomically so row/column/header identity is
    not silently flattened into neighboring prose. Section and financial
    metadata are contextualized into the emitted text and also preserved as
    typed Evidence fields.
    """

    _FINANCIAL_FIELDS = (
        "entity",
        "metric",
        "period",
        "currency",
        "unit",
        "accounting_basis",
        "segment",
        "scope",
        "source_type",
    )

    def __init__(self, chunk_size: int = 600, overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    @staticmethod
    def _tokens(text: str) -> list[str]:
        # Deterministic tokenizer suitable for CPU regression tests. Production
        # adapters may replace it with the embedding model tokenizer.
        return re.findall(r"[A-Za-z0-9_.%/-]+|[\u4e00-\u9fff]|[^\s]", text)

    @staticmethod
    def _context(block: DocumentBlock) -> str:
        parts: list[str] = []
        if block.section_path:
            parts.append("Section: " + " > ".join(block.section_path))
        for key in StructureAwareChunker._FINANCIAL_FIELDS:
            value = block.metadata.get(key)
            if value:
                parts.append(f"{key}: {value}")
        return " | ".join(parts)

    def _make_evidence(
        self,
        block: DocumentBlock,
        *,
        document_id: str,
        source_uri: str,
        text: str,
        block_id: str,
    ) -> Evidence:
        metadata = {key: block.metadata.get(key) for key in self._FINANCIAL_FIELDS}
        return Evidence.from_content(
            document_id,
            source_uri,
            block.page,
            block_id,
            "table" if block.kind == "table" else "text",
            text,
            table_id=block.table_id,
            row_id=block.row_id,
            column_id=block.column_id,
            section_path=block.section_path,
            **metadata,
        )

    def chunk(
        self,
        blocks: list[DocumentBlock],
        *,
        document_id: str,
        source_uri: str,
    ) -> list[Evidence]:
        evidence: list[Evidence] = []

        for block in blocks:
            prefix = self._context(block)
            contextual_text = f"{prefix}\n{block.text}" if prefix else block.text

            # Tables remain atomic by design; retrieval may later index table,
            # row, or cell views separately without destroying structure here.
            if block.kind == "table":
                evidence.append(
                    self._make_evidence(
                        block,
                        document_id=document_id,
                        source_uri=source_uri,
                        text=contextual_text,
                        block_id=block.block_id,
                    )
                )
                continue

            tokens = self._tokens(contextual_text)
            if len(tokens) <= self.chunk_size:
                evidence.append(
                    self._make_evidence(
                        block,
                        document_id=document_id,
                        source_uri=source_uri,
                        text=contextual_text,
                        block_id=block.block_id,
                    )
                )
                continue

            step = self.chunk_size - self.overlap
            for index, start in enumerate(range(0, len(tokens), step)):
                window = tokens[start : start + self.chunk_size]
                if not window:
                    break
                evidence.append(
                    self._make_evidence(
                        block,
                        document_id=document_id,
                        source_uri=source_uri,
                        text=" ".join(window),
                        block_id=f"{block.block_id}:c{index}",
                    )
                )
                if start + self.chunk_size >= len(tokens):
                    break

        return evidence
