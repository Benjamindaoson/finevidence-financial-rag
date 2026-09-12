from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .requirements import RequirementGraph


QuestionType = Literal["factual", "comparison", "numerical", "trend", "explanation", "multi-document synthesis"]


class AnnotationPass(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pass_name: Literal["A", "B", "ADJUDICATION"]
    method: str
    status: Literal["READY", "N/A"] = "READY"
    requirements: RequirementGraph
    question_type: QuestionType | None = None
    raw_output: str | None = None
    output_sha256: str | None = None
    created_at_utc: str | None = None
    reason: str | None = None


class RequirementMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_requirement_id: str
    gold_requirement_id: str
    score: float = Field(ge=0.0, le=1.0)
    matched_slots: list[str] = Field(default_factory=list)


class RequirementMatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matches: list[RequirementMatch]
    unmatched_predicted: list[str]
    unmatched_gold: list[str]


class RequirementAdjudicatedCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: Literal["RequirementAdjudicated-v1"]
    case_id: str
    source_dataset: str = "unknown"
    source_record_id: str | None = None
    source_question_id: str | None = None
    question: str
    question_type: QuestionType
    requirements: RequirementGraph
    pass_a: AnnotationPass
    pass_b: AnnotationPass
    disagreements: list[str] = Field(default_factory=list)
    annotation_method: Literal["dual_pass_model_assisted_adjudication"]
    human_verified: bool = False


class P0HAnnotationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: Literal["RequirementAdjudicated-v1"]
    source_benchmark: str
    source_manifest_sha256: str
    case_count: int = Field(ge=0)
    question_type_distribution: dict[str, int]
    annotation_method: Literal["dual_pass_model_assisted_adjudication"]
    human_verified: bool = False
    pass_a_method: str
    pass_b_method: str
    adjudication_method: str
    cases_sha256: str


class LocalLLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    model_path: str | None = None
    revision: str = "local-cache"
    model_sha256: str | None = None
    runtime: str = "transformers"
    device: str = "cpu"
    prompt_version: str = "p0-h-d1-v1"
    max_new_tokens: int = Field(default=256, ge=1, le=1024)
    temperature: float = Field(default=0.0, ge=0.0, le=0.0)
    local_files_only: bool = True


class LLMDecompositionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["READY", "N/A"]
    question_type: QuestionType | None = None
    graph: RequirementGraph = Field(default_factory=lambda: RequirementGraph(requirements=[]))
    raw_output: str | None = None
    retry_count: int = Field(default=0, ge=0, le=1)
    reason: str | None = None


class HSBCHardCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: Literal["HSBCNaturalHard-v1"]
    case_id: str
    question: str
    category: str
    positive_evidence_id: str
    hard_negative_ids: list[str] = Field(min_length=1)
    candidate_evidence_ids: list[str]
    source_hashes: dict[str, str]
    adjudicated_facets: dict[str, str | None]
    verification_method: Literal["model_assisted_adjudicated"]
    human_verified: bool = False
