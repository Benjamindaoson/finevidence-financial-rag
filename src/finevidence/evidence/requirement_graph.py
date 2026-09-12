from __future__ import annotations

from finevidence.contracts.requirements import Requirement, RequirementEdge, RequirementGraph
from finevidence.evidence.fact_understanding import classify_question
from finevidence.ranking.facets import extract_facets


def _base(question: str, requirement_id: str, description: str, fact_type: str, role: str, criticality: str = "CRITICAL", **kwargs) -> Requirement:
    facets = extract_facets(question)
    return Requirement(
        requirement_id=requirement_id,
        description=description,
        fact_type=fact_type,
        role=role,
        entity=facets.entity,
        metric=facets.metric,
        period=facets.period,
        segment=facets.segment,
        basis=facets.basis,
        geography=facets.geography,
        currency=facets.currency,
        criticality=criticality,
        **kwargs,
    )


def decompose_requirement_graph(question: str) -> RequirementGraph:
    kind = classify_question(question)
    requirements: list[Requirement]
    edges: list[RequirementEdge] = []
    if kind == "comparison":
        requirements = [
            _base(question, "R1", "value A required for comparison", "RETRIEVED_FACT", "value_a"),
            _base(question, "R2", "value B required for comparison", "RETRIEVED_FACT", "value_b"),
            _base(question, "R3", "comparison result derived from value A and value B", "DERIVED_FACT", "comparison_result", operation="compare(R1,R2)", depends_on=["R1", "R2"]),
        ]
        edges = [RequirementEdge(source_requirement_id="R3", target_requirement_id=item, edge_type="DEPENDS_ON") for item in ("R1", "R2")]
    elif kind == "numerical":
        requirements = [
            _base(question, "R1", "numerical input 1", "RETRIEVED_FACT", "input_1"),
            _base(question, "R2", "numerical input 2", "RETRIEVED_FACT", "input_2"),
            _base(question, "R3", "calculated result", "DERIVED_FACT", "result", operation="calculate(R1,R2)", depends_on=["R1", "R2"]),
        ]
        edges = [RequirementEdge(source_requirement_id="R3", target_requirement_id=item, edge_type="DERIVED_FROM") for item in ("R1", "R2")]
    elif kind == "trend":
        requirements = [
            _base(question, "R1", "prior-period value", "RETRIEVED_FACT", "prior_value"),
            _base(question, "R2", "current-period value", "RETRIEVED_FACT", "current_value"),
            _base(question, "R3", "trend change derived from prior and current values", "DERIVED_FACT", "trend_change", operation="change(R1,R2)", depends_on=["R1", "R2"]),
        ]
        edges = [RequirementEdge(source_requirement_id="R3", target_requirement_id=item, edge_type="DEPENDS_ON") for item in ("R1", "R2")]
    elif kind == "explanation":
        requirements = [
            _base(question, "R1", "observed outcome or change", "RETRIEVED_FACT", "observed_outcome"),
            _base(question, "R2", "supporting driver", "CONTEXT_FACT", "supporting_driver", "SUPPORTING"),
            _base(question, "R3", "management explanation of the outcome", "EXPLANATORY_FACT", "management_explanation"),
        ]
    elif kind == "multi-document synthesis":
        requirements = [
            _base(question, "R1", "fact from source A", "RETRIEVED_FACT", "source_fact_a"),
            _base(question, "R2", "fact from source B", "RETRIEVED_FACT", "source_fact_b"),
            _base(question, "R3", "relationship between source A and source B", "CONTEXT_FACT", "source_relationship", "SUPPORTING"),
        ]
    else:
        requirements = [_base(question, "R1", "target fact", "RETRIEVED_FACT", "target_fact")]
    return RequirementGraph(requirements=requirements, edges=edges)
