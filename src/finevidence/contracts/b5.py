from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ModelStatus = Literal["READY", "N/A", "FAILED"]
ToolName = Literal["text_search", "table_query", "visual_search", "graph_lookup"]
StopReason = Literal[
    "ALL_CRITICAL_REQUIREMENTS_COVERED",
    "NO_MEANINGFUL_COVERAGE_GAIN",
    "BUDGET_EXHAUSTED",
    "REPEATED_QUERY",
    "NO_CAPABLE_TOOL",
    "UNANSWERABLE",
]


class ModelManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    model_revision: str | None = None
    runtime: str
    device: str
    status: ModelStatus
    image_encoder: bool = False
    weights_sha256: str | None = None
    error: str | None = None


class SearchBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_steps: int = Field(default=3, ge=1)
    max_queries: int = Field(default=3, ge=1)
    max_visual_calls: int = Field(default=1, ge=0)
    max_table_calls: int = Field(default=1, ge=0)
    max_graph_calls: int = Field(default=1, ge=0)
    max_latency_ms: float = Field(default=5000.0, gt=0)
    max_cost: float = Field(default=1.0, ge=0)
    minimum_coverage_delta: float = Field(default=0.0, ge=0, le=1)


class SearchAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: int = Field(ge=1)
    requirement_id: str | None = None
    query: str = Field(min_length=1)
    tool: ToolName
    reason: str = Field(min_length=1)
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    returned_evidence_ids: list[str] = Field(default_factory=list)
    coverage_before: float = Field(ge=0, le=1)
    coverage_after: float = Field(ge=0, le=1)
    coverage_delta: float
    latency_ms: float = Field(ge=0)
    cost: float = Field(ge=0)
    failure_type: str | None = None
    stop_reason: StopReason | None = None


class SearchControllerState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    covered_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    retrieval_history: list[SearchAction] = Field(default_factory=list)
    tool_history: list[ToolName] = Field(default_factory=list)
    remaining_budget: SearchBudget = Field(default_factory=SearchBudget)
    coverage_delta: float = 0.0
    failure_type: str | None = None
    stop_reason: StopReason | None = None


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: Literal["Entity", "Metric", "Period", "Segment", "Basis", "Document", "Evidence"]
    label: str
    provenance_ids: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    target_id: str
    relation: Literal[
        "ENTITY_HAS_METRIC",
        "METRIC_HAS_PERIOD",
        "METRIC_HAS_BASIS",
        "METRIC_REPORTED_IN",
        "EVIDENCE_SUPPORTS_METRIC",
        "EVIDENCE_FROM_DOCUMENT",
        "SEGMENT_OF_ENTITY",
        "RELATED_DISCLOSURE",
    ]
    provenance_ids: list[str] = Field(default_factory=list)
