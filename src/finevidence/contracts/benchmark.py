from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .evidence import Evidence


class RequiredEvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    document_id: str | None = None
    page: int | None = Field(default=None, ge=1)
    block_id: str | None = None
    table_id: str | None = None
    row_id: str | None = None
    column_id: str | None = None


class FactSlots(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_type: str
    entity: str | None = None
    metric: str | None = None
    period: str | None = None
    segment: str | None = None
    basis: str | None = None
    operation: str | None = None
    unit: str | None = None
    role: str
    critical: bool = True


class FactRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str
    description: str = Field(min_length=1)
    acceptable_evidence_ids: list[str] = Field(min_length=1)
    slots: FactSlots | None = None


class MiniCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    question: str = Field(min_length=1)
    gold_answer: str | None
    required_evidence: list[RequiredEvidenceRef] = Field(default_factory=list)
    required_facts: list[FactRequirement | str] = Field(default_factory=list)
    failure_type: str
    answerable: bool
    positive_evidence_id: str | None = None
    hard_negative_ids: list[str] = Field(default_factory=list)
    source_dataset: str | None = None
    source_split: str | None = None
    source_record_id: str | None = None
    source_question_id: str | None = None
    gold_supporting_facts: dict[str, Any] | None = None
    reasoning_program: str | None = None
    gold_execution_answer: Any = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_gold_evidence_for_answerable_case(self) -> "MiniCase":
        if self.answerable and not self.required_evidence:
            raise ValueError("answerable cases require required_evidence")
        return self


class Benchmark(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    evidence: list[Evidence]
    cases: list[MiniCase]
    manifest: dict
