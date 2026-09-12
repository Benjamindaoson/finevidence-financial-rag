from __future__ import annotations

import hashlib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Modality = Literal["text", "table", "image", "equation"]


def normalize_content(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_content(text).encode("utf-8")).hexdigest()


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str
    document_id: str
    source_uri: str
    page: int = Field(ge=1)
    block_id: str
    bbox: tuple[float, float, float, float] | None = None
    modality: Modality
    text: str = Field(min_length=1)
    table_id: str | None = None
    row_id: str | None = None
    column_id: str | None = None
    entity: str | None = None
    metric: str | None = None
    period: str | None = None
    retrieval_score: float | None = None
    rerank_score: float | None = None
    content_hash: str

    @model_validator(mode="after")
    def validate_content_hash(self) -> "Evidence":
        expected = content_hash(self.text)
        if self.content_hash != expected:
            raise ValueError(f"content_hash does not match normalized text; expected {expected}")
        return self

    @classmethod
    def from_content(
        cls,
        document_id: str,
        source_uri: str,
        page: int,
        block_id: str,
        modality: Modality,
        text: str,
        *,
        evidence_id: str | None = None,
        content_hash: str | None = None,
        **metadata,
    ) -> "Evidence":
        expected = globals()["content_hash"](text)
        if content_hash is not None and content_hash != expected:
            raise ValueError("content_hash does not match normalized text")
        return cls(
            evidence_id=evidence_id or f"{document_id}:p{page}:{block_id}",
            document_id=document_id,
            source_uri=source_uri,
            page=page,
            block_id=block_id,
            modality=modality,
            text=text,
            content_hash=expected,
            **metadata,
        )


class RetrievedEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str
    rank: int = Field(ge=1)
    retrieval_score: float
    rerank_score: float | None = None
