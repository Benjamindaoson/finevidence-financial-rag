from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PageImage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_image_id: str
    document_id: str
    page: int = Field(ge=1)
    image_path: str
    image_sha256: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    dpi: int = Field(gt=0)
    render_version: str
    source_pdf_sha256: str


class VisualModelManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    model_revision: str
    runtime: str
    device: str
    image_encoder: bool
    weights_sha256: str | None = None
    status: Literal["READY", "N/A"]
    reason: str | None = None


class RoutingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: Literal["TEXT", "TABLE", "VISUAL", "MIXED", "UNKNOWN"]
    visual_invoked: bool
    reason: str
    score: float = Field(ge=0.0, le=1.0)


class CitationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_page_ids: list[str]
    gold_page_ids: list[str]
    page_precision: float | str
    page_recall: float | str
    page_f1: float | str
    bbox_iou: float | str = "N/A"
    region_precision: float | str = "N/A"
    region_recall: float | str = "N/A"
