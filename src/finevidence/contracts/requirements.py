from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


RequirementType = Literal["RETRIEVED_FACT", "DERIVED_FACT", "EXPLANATORY_FACT", "CONTEXT_FACT"]
Criticality = Literal["CRITICAL", "SUPPORTING", "OPTIONAL"]
EdgeType = Literal["DEPENDS_ON", "DERIVED_FROM", "EXPLAINS", "COMPARED_WITH"]
SupportType = Literal["DIRECT_SUPPORT", "PARTIAL_SUPPORT", "DERIVATION_INPUT", "EXPLANATORY_SUPPORT", "CONTEXT_ONLY", "NO_SUPPORT"]


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    description: str = Field(min_length=1)
    fact_type: RequirementType
    role: str
    entity: str | None = None
    metric: str | None = None
    period: str | None = None
    segment: str | None = None
    basis: str | None = None
    geography: str | None = None
    currency: str | None = None
    unit: str | None = None
    operation: str | None = None
    criticality: Criticality = "CRITICAL"
    depends_on: list[str] = Field(default_factory=list)
    acceptable_evidence_ids: list[str] = Field(default_factory=list)
    evidence_role: Literal["VALUE_SUPPORT", "COMPARISON_SUPPORT", "DERIVATION_INPUT", "EXPLANATION_SUPPORT", "CONTEXT_SUPPORT"] | None = None


class RequirementEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_requirement_id: str
    target_requirement_id: str
    edge_type: EdgeType


class RequirementGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[Requirement]
    edges: list[RequirementEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph(self) -> "RequirementGraph":
        ids = [item.requirement_id for item in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate requirement_id")
        known = set(ids)
        adjacency = {item: [] for item in ids}
        for requirement in self.requirements:
            if any(parent not in known for parent in requirement.depends_on):
                raise ValueError("unknown requirement dependency")
            adjacency[requirement.requirement_id].extend(requirement.depends_on)
        for edge in self.edges:
            if edge.source_requirement_id not in known or edge.target_requirement_id not in known:
                raise ValueError("unknown requirement edge endpoint")
            if edge.source_requirement_id == edge.target_requirement_id:
                raise ValueError("self-edge is not allowed")
            adjacency[edge.source_requirement_id].append(edge.target_requirement_id)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("requirement graph cycle")
            if node in visited:
                return
            visiting.add(node)
            for child in adjacency[node]:
                visit(child)
            visiting.remove(node)
            visited.add(node)

        for node in ids:
            visit(node)
        return self

    def requirement(self, requirement_id: str) -> Requirement:
        for requirement in self.requirements:
            if requirement.requirement_id == requirement_id:
                return requirement
        raise KeyError(requirement_id)


class FactEvidenceAlignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    evidence_id: str
    support_type: SupportType
    alignment_score: float = Field(ge=0.0, le=1.0)
    matched_slots: list[str] = Field(default_factory=list)
    mismatched_slots: list[str] = Field(default_factory=list)
    reusable: bool
    reason: str


class EvidenceReuseEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    requirement_ids: list[str]
    valid: bool
    reason: str


class IndependentCoverageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_self_coverage: float
    independent_coverage: float
    critical_coverage: float
    critical_missing_rate: float
    evidence_reuse_rate: float
    invalid_reuse_rate: float
    answer_eligible: bool
    covered_requirement_ids: list[str]
    independent_requirement_ids: list[str]
    missing_critical_requirements: list[str]
    invalid_reuse_events: list[EvidenceReuseEvent]
    warnings: list[str]
