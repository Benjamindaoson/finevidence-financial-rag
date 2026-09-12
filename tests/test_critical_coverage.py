from finevidence.contracts.requirements import FactEvidenceAlignment, Requirement, RequirementGraph
from finevidence.evidence.alignment import evaluate_independent_coverage


def test_missing_critical_requirement_blocks_but_missing_supporting_does_not():
    graph = RequirementGraph(
        requirements=[
            Requirement(requirement_id="F1", description="critical numerator", fact_type="RETRIEVED_FACT", role="numerator", criticality="CRITICAL", acceptable_evidence_ids=["E1"]),
            Requirement(requirement_id="F2", description="supporting context", fact_type="CONTEXT_FACT", role="context", criticality="SUPPORTING", acceptable_evidence_ids=["E2"]),
        ],
        edges=[],
    )

    missing = evaluate_independent_coverage(graph, [], set())
    supporting_only = evaluate_independent_coverage(
        graph,
        [FactEvidenceAlignment(requirement_id="F1", evidence_id="E1", support_type="DIRECT_SUPPORT", alignment_score=1.0, reusable=False, reason="direct")],
        {"E1"},
    )

    assert missing.answer_eligible is False
    assert "CRITICAL_REQUIREMENT_MISSING" in missing.warnings
    assert supporting_only.answer_eligible is True
