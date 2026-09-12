from finevidence.contracts.evidence import Evidence
from finevidence.contracts.requirements import FactEvidenceAlignment, Requirement
from finevidence.evidence.alignment import evaluate_independent_coverage, align_requirement_to_evidence
from finevidence.contracts.requirements import RequirementEdge, RequirementGraph


def test_same_evidence_for_incompatible_roles_is_invalid_reuse():
    graph = RequirementGraph(
        requirements=[
            Requirement(requirement_id="F1", description="current value", fact_type="RETRIEVED_FACT", role="current_value", acceptable_evidence_ids=["E1"]),
            Requirement(requirement_id="F2", description="management explanation", fact_type="EXPLANATORY_FACT", role="management_explanation", acceptable_evidence_ids=["E1"]),
        ],
        edges=[],
    )
    alignments = [
        FactEvidenceAlignment(requirement_id="F1", evidence_id="E1", support_type="DIRECT_SUPPORT", alignment_score=0.9, reusable=True, reason="value"),
        FactEvidenceAlignment(requirement_id="F2", evidence_id="E1", support_type="DIRECT_SUPPORT", alignment_score=0.9, reusable=True, reason="lexical overlap"),
    ]

    result = evaluate_independent_coverage(graph, alignments, {"E1"})

    assert result.raw_self_coverage == 1.0
    assert result.independent_coverage < result.raw_self_coverage
    assert result.invalid_reuse_rate > 0
    assert "EVIDENCE_REUSE_INFLATION" in result.warnings


def test_derived_fact_is_covered_by_independent_inputs_and_alternative_is_valid():
    graph = RequirementGraph(
        requirements=[
            Requirement(requirement_id="F1", description="numerator", fact_type="RETRIEVED_FACT", role="numerator", acceptable_evidence_ids=["E1", "E2"]),
            Requirement(requirement_id="F2", description="denominator", fact_type="RETRIEVED_FACT", role="denominator", acceptable_evidence_ids=["E3"]),
            Requirement(requirement_id="F3", description="ratio", fact_type="DERIVED_FACT", role="ratio", acceptable_evidence_ids=[], depends_on=["F1", "F2"], operation="F1/F2"),
        ],
        edges=[
            RequirementEdge(source_requirement_id="F3", target_requirement_id="F1", edge_type="DEPENDS_ON"),
            RequirementEdge(source_requirement_id="F3", target_requirement_id="F2", edge_type="DEPENDS_ON"),
        ],
    )
    result = evaluate_independent_coverage(
        graph,
        [
            FactEvidenceAlignment(requirement_id="F1", evidence_id="E2", support_type="DIRECT_SUPPORT", alignment_score=1.0, reusable=False, reason="alternative"),
            FactEvidenceAlignment(requirement_id="F2", evidence_id="E3", support_type="DIRECT_SUPPORT", alignment_score=1.0, reusable=False, reason="direct"),
        ],
        {"E2", "E3"},
    )

    assert result.answer_eligible is True
    assert result.independent_coverage == 1.0


def test_numeric_evidence_does_not_count_as_explanatory_support():
    requirement = Requirement(requirement_id="F1", description="why cost of risk increased", fact_type="EXPLANATORY_FACT", role="management_explanation", acceptable_evidence_ids=["E1"])
    evidence = Evidence.from_content(document_id="D1", source_uri="fixture://D1", page=1, block_id="b1", modality="table", text="Cost of risk 2024: 30 bps", evidence_id="E1")

    alignment = align_requirement_to_evidence(requirement, evidence)

    assert alignment.support_type != "EXPLANATORY_SUPPORT"
    assert alignment.requirement_id == "F1"
