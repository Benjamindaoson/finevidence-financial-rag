from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from finevidence.contracts.evidence_api import EvidenceObject
from finevidence.contracts.requirements import Requirement


class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str | None = None
    source_type: Literal["text", "table", "image", "equation"] | None = None
    entity: str | None = None
    metric: str | None = None
    period: str | None = None
    tenant_id: str | None = None
    user_role: str | None = None


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=10, ge=1, le=100)


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    evidence: list[EvidenceObject]
    catalog_size: int


class CoverageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    required_claims: list[Requirement] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class CoverageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    coverage_score: float
    independent_coverage: float
    critical_coverage: float
    missing_requirements: list[str]
    status: Literal["ELIGIBLE", "PARTIAL", "INSUFFICIENT"]
    evidence: list[EvidenceObject]


class TableQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity: str | None = None
    metric: str | None = None
    period: str | None = None
    top_k: int = Field(default=20, ge=1, le=100)


class TableQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    evidence: list[EvidenceObject]


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class VerifyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    supported: bool
    coverage_score: float
    missing_requirements: list[str]
    supporting_evidence: list[EvidenceObject]


class CitationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    evidence_id: str
    document_id: str
    document_name: str
    page_number: int
    source_url: str
    document_hash: str | None
    table_id: str | None
    row_id: str | None
    column_id: str | None
    bbox: tuple[float, float, float, float] | None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    catalog_size: int
