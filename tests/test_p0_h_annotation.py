from finevidence.contracts.p0_h import (
    AnnotationPass,
    RequirementAdjudicatedCase,
    RequirementMatch,
    RequirementMatchResult,
)
from finevidence.contracts.requirements import Requirement, RequirementGraph
from finevidence.eval.p0_h_annotation import match_requirements


def _req(requirement_id: str, role: str, fact_type: str = "RETRIEVED_FACT"):
    return Requirement(requirement_id=requirement_id, description=role, fact_type=fact_type, role=role)


def test_requirement_matching_is_one_to_one():
    predicted = RequirementGraph(requirements=[_req("P1", "current value"), _req("P2", "current value")])
    gold = RequirementGraph(requirements=[_req("G1", "current value")])

    result = match_requirements(predicted, gold)

    assert len(result.matches) == 1
    assert result.unmatched_predicted == ["P2"]
    assert result.unmatched_gold == []
    assert len({item.gold_requirement_id for item in result.matches}) == len(result.matches)


def test_adjudicated_case_records_non_human_provenance():
    case = RequirementAdjudicatedCase(
        dataset_name="RequirementAdjudicated-v1",
        case_id="case-1",
        question="What was revenue?",
        question_type="factual",
        requirements=RequirementGraph(requirements=[_req("R1", "target value")]),
        pass_a=AnnotationPass(pass_name="A", method="source_rules", requirements=RequirementGraph(requirements=[])),
        pass_b=AnnotationPass(pass_name="B", method="local_model", requirements=RequirementGraph(requirements=[])),
        disagreements=["requirement_count"],
        annotation_method="dual_pass_model_assisted_adjudication",
        human_verified=False,
    )

    assert case.annotation_method == "dual_pass_model_assisted_adjudication"
    assert case.human_verified is False
