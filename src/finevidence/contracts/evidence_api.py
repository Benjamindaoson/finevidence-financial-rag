from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .evidence import Evidence


class VisualReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_image_id: str | None = None
    image_path: str | None = None
    render_hash: str | None = None
    region_bbox: tuple[float, float, float, float] | None = None


class EvidenceContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    table: dict[str, Any] | None = None
    visual_reference: VisualReference | None = None


class EvidenceProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_name: str
    page_number: int = Field(ge=1)
    source_url: str
    document_hash: str | None = None


class FinancialMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity: str | None = None
    metric: str | None = None
    period: str | None = None
    unit: str | None = None
    category: str | None = None


class EvidenceStructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_id: str | None = None
    row_id: str | None = None
    column_id: str | None = None
    bbox: tuple[float, float, float, float] | None = None


class EvidenceVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_type: Literal["TEXT", "TABLE_CELL", "IMAGE", "EQUATION"]
    confidence: float = Field(ge=0.0, le=1.0)
    coverage_status: Literal["RETRIEVED", "SUPPORTED", "PARTIAL", "UNSUPPORTED", "UNVERIFIED"]


class EvidenceObject(BaseModel):
    """Versioned external contract; internal Evidence remains backward compatible."""

    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    evidence_id: str
    document_id: str
    source_type: Literal["text", "table_cell", "page_image", "equation"]
    score: float | None = None
    content: EvidenceContent
    provenance: EvidenceProvenance
    financial: FinancialMetadata
    structure: EvidenceStructure
    verification: EvidenceVerification

    @classmethod
    def from_evidence(cls, evidence: Evidence, *, document_hash: str | None = None, score: float | None = None, coverage_status: str = "RETRIEVED", confidence: float = 0.0) -> "EvidenceObject":
        source_type = {"text": "text", "table": "table_cell", "image": "page_image", "equation": "equation"}[evidence.modality]
        evidence_type = {"text": "TEXT", "table": "TABLE_CELL", "image": "IMAGE", "equation": "EQUATION"}[evidence.modality]
        table = None
        if evidence.modality == "table":
            table = {key: value for key, value in {"table_id": evidence.table_id, "row_id": evidence.row_id, "column_id": evidence.column_id, "value": evidence.text}.items() if value is not None}
        return cls(
            evidence_id=evidence.evidence_id,
            document_id=evidence.document_id,
            source_type=source_type,
            score=score,
            content=EvidenceContent(text=evidence.text, table=table, visual_reference=VisualReference(page_image_id=evidence.page_image_id, image_path=evidence.image_path, render_hash=evidence.render_hash, region_bbox=evidence.region_bbox)),
            provenance=EvidenceProvenance(document_name=evidence.document_id, page_number=evidence.page, source_url=evidence.source_uri, document_hash=document_hash),
            financial=FinancialMetadata(entity=evidence.entity, metric=evidence.metric, period=evidence.period, unit=None),
            structure=EvidenceStructure(table_id=evidence.table_id, row_id=evidence.row_id, column_id=evidence.column_id, bbox=evidence.bbox),
            verification=EvidenceVerification(evidence_type=evidence_type, confidence=confidence, coverage_status=coverage_status),
        )
