import pytest
from pydantic import ValidationError

from finevidence.contracts.requirements import Requirement, RequirementEdge, RequirementGraph


def _requirement(requirement_id, role, fact_type="RETRIEVED_FACT", criticality="CRITICAL", **kwargs):
    return Requirement(
        requirement_id=requirement_id,
        description=role,
        fact_type=fact_type,
        role=role,
        criticality=criticality,
        **kwargs,
    )


def test_requirement_graph_rejects_cycles():
    with pytest.raises(ValidationError, match="cycle"):
        RequirementGraph(
            requirements=[_requirement("F1", "a"), _requirement("F2", "b")],
            edges=[
                RequirementEdge(source_requirement_id="F1", target_requirement_id="F2", edge_type="DEPENDS_ON"),
                RequirementEdge(source_requirement_id="F2", target_requirement_id="F1", edge_type="DEPENDS_ON"),
            ],
        )


def test_requirement_graph_rejects_cycles_declared_by_depends_on():
    with pytest.raises(ValidationError, match="cycle"):
        RequirementGraph(
            requirements=[
                _requirement("F1", "a", depends_on=["F2"]),
                _requirement("F2", "b", depends_on=["F1"]),
            ],
            edges=[],
        )


def test_derived_requirement_has_dependencies_without_direct_evidence():
    graph = RequirementGraph(
        requirements=[
            _requirement("F1", "value_a", acceptable_evidence_ids=["E1"]),
            _requirement("F2", "value_b", acceptable_evidence_ids=["E2"]),
            _requirement("F3", "difference", fact_type="DERIVED_FACT", depends_on=["F1", "F2"], operation="F1-F2"),
        ],
        edges=[
            RequirementEdge(source_requirement_id="F3", target_requirement_id="F1", edge_type="DEPENDS_ON"),
            RequirementEdge(source_requirement_id="F3", target_requirement_id="F2", edge_type="DEPENDS_ON"),
        ],
    )

    assert graph.requirement("F3").fact_type == "DERIVED_FACT"
