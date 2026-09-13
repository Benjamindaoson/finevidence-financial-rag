from .coverage import CoverageResult, coverage_for_case
from .fact_understanding import DecompositionResult, classify_question, decompose_required_facts_by_variant
from .alignment import EvidenceReusePolicy, align_requirement_to_evidence, evaluate_independent_coverage
from .requirement_graph import decompose_requirement_graph
from .graph import EvidenceGraph

__all__ = ["CoverageResult", "coverage_for_case", "DecompositionResult", "EvidenceGraph", "classify_question", "decompose_required_facts_by_variant", "EvidenceReusePolicy", "align_requirement_to_evidence", "evaluate_independent_coverage", "decompose_requirement_graph"]
