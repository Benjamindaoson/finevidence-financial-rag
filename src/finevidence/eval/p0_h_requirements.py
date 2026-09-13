from __future__ import annotations

from collections import defaultdict

from finevidence.contracts.p0_h import RequirementAdjudicatedCase
from finevidence.contracts.requirements import FactEvidenceAlignment, RequirementGraph
from finevidence.evidence.alignment import align_requirement_to_evidence, evaluate_independent_coverage
from finevidence.evidence.fact_understanding import classify_question, decompose_required_facts_by_variant
from finevidence.evidence.requirement_graph import decompose_requirement_graph
from finevidence.eval.p0_h_annotation import match_requirements
from finevidence.eval.p0_g import _flat_graph
from finevidence.retrieval.hybrid import HybridRetriever


def _graph_for(case, variant: str, d1_graph: RequirementGraph | None = None) -> RequirementGraph:
    if variant == "D1":
        return d1_graph or RequirementGraph(requirements=[])
    if variant == "D4":
        return decompose_requirement_graph(case.question)
    result = decompose_required_facts_by_variant(case.question, variant)
    return _flat_graph(result) if result.status == "READY" else RequirementGraph(requirements=[])


def _coverage(graph: RequirementGraph, question: str, evidence_by_id: dict, retriever: HybridRetriever, top_k: int, max_rounds: int = 2):
    selected = set()
    initial = set()
    queries = []
    query = question
    result = None
    alignments = []
    for round_number in range(max_rounds + 1):
        queries.append(query)
        ids = {item.evidence_id for item in retriever.search(query, top_k)}
        selected.update(ids)
        if round_number == 0:
            initial = set(ids)
        alignments = [align_requirement_to_evidence(requirement, evidence_by_id[evidence_id]) for requirement in graph.requirements for evidence_id in sorted(selected) if evidence_id in evidence_by_id and requirement.fact_type != "DERIVED_FACT"]
        result = evaluate_independent_coverage(graph, alignments, selected)
        if result.answer_eligible or round_number >= max_rounds:
            break
        missing = graph.requirement(result.missing_critical_requirements[0])
        query = f"{question} Evidence needed: {missing.description}"
    return initial, selected, queries, alignments, result


def _mean(values):
    return sum(values) / len(values) if values else "N/A"


def evaluate_requirement_methods(cases: list, annotations: dict[str, RequirementAdjudicatedCase], d1_graphs: dict[str, RequirementGraph], evidence: list, top_k: int = 5) -> dict:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    retriever = HybridRetriever()
    retriever.fit(evidence)
    methods = [("D0", "D0 Heuristic"), ("D1", "D1 LLM Direct"), ("D2", "D2 Schema-constrained"), ("D3", "D3 Evidence-aware"), ("D4", "D4 Requirement-Graph-Constrained")]
    rows = defaultdict(list)
    traces = []
    failures = []
    adjudicated_coverage = []
    for case in cases:
        gold = annotations[case.question_id]
        _, _, _, _, gold_cov = _coverage(gold.requirements, case.question, evidence_by_id, retriever, top_k)
        adjudicated_coverage.append(gold_cov)
        for variant, label in methods:
            graph = _graph_for(case, variant, d1_graphs.get(case.question_id))
            if variant == "D1" and not d1_graphs.get(case.question_id):
                rows[label].append({"status": "N/A", "reason": "NO_VALID_LLM_REQUIREMENTS"})
                traces.append({"question_id": case.question_id, "method": label, "status": "N/A", "reason": "NO_VALID_LLM_REQUIREMENTS"})
                continue
            matches = match_requirements(graph, gold.requirements)
            initial, selected, queries, alignments, coverage = _coverage(graph, case.question, evidence_by_id, retriever, top_k)
            pred_total, gold_total = len(graph.requirements), len(gold.requirements.requirements)
            matched = len(matches.matches)
            gold_critical = {item.requirement_id for item in gold.requirements.requirements if item.criticality == "CRITICAL"}
            matched_critical = {item.gold_requirement_id for item in matches.matches if item.gold_requirement_id in gold_critical}
            type_acc = _mean([float(graph.requirement(item.predicted_requirement_id).fact_type == gold.requirements.requirement(item.gold_requirement_id).fact_type) for item in matches.matches])
            role_acc = _mean([float(graph.requirement(item.predicted_requirement_id).role == gold.requirements.requirement(item.gold_requirement_id).role) for item in matches.matches])
            critical_acc = _mean([float(graph.requirement(item.predicted_requirement_id).criticality == gold.requirements.requirement(item.gold_requirement_id).criticality) for item in matches.matches])
            dep_acc = _mean([float(set(graph.requirement(item.predicted_requirement_id).depends_on) == set(gold.requirements.requirement(item.gold_requirement_id).depends_on)) for item in matches.matches if graph.requirement(item.predicted_requirement_id).fact_type == "DERIVED_FACT" or gold.requirements.requirement(item.gold_requirement_id).fact_type == "DERIVED_FACT"])
            metric = {"status": "READY", "requirement_precision": matched / pred_total if pred_total else 0.0, "requirement_recall": matched / gold_total if gold_total else 0.0, "critical_requirement_recall": len(matched_critical) / len(gold_critical) if gold_critical else "N/A", "question_type_accuracy": float(classify_question(case.question) == gold.question_type), "fact_type_accuracy": type_acc, "role_accuracy": role_acc, "criticality_accuracy": critical_acc, "dependency_accuracy": dep_acc, "requirement_count_error": abs(pred_total - gold_total), "independent_cer": coverage.independent_coverage, "critical_coverage": coverage.critical_coverage, "raw_self_coverage": coverage.raw_self_coverage, "evidence_reuse_rate": coverage.evidence_reuse_rate, "invalid_reuse_rate": coverage.invalid_reuse_rate, "answer_eligible_rate": float(coverage.answer_eligible), "faer": float(coverage.raw_self_coverage == 1.0 and not coverage.answer_eligible), "unmatched_predicted": matches.unmatched_predicted, "unmatched_gold": matches.unmatched_gold}
            rows[label].append(metric)
            trace = {"question_id": case.question_id, "method": label, "gold_requirements": [item.model_dump() for item in gold.requirements.requirements], "predicted_requirements": [item.model_dump() for item in graph.requirements], "matches": [item.model_dump() for item in matches.matches], "unmatched_predicted": matches.unmatched_predicted, "unmatched_gold": matches.unmatched_gold, "initial_evidence": sorted(initial), "targeted_queries": queries, "final_evidence": sorted(selected), "alignments": [item.model_dump() for item in alignments], "coverage": coverage.model_dump(), "failure_types": _failure_types(matches, graph, gold.requirements, coverage)}
            traces.append(trace)
            if trace["failure_types"]:
                failures.append(trace)
    summary = {}
    for label, values in rows.items():
        if values and values[0].get("status") == "N/A":
            summary[label] = values[0]
            continue
        numeric = sorted(set(values[0]) - {"status", "unmatched_predicted", "unmatched_gold"})
        summary[label] = {"status": "READY", **{field: _mean([item[field] for item in values if isinstance(item.get(field), (int, float))]) for field in numeric}}
    gold_cov = {"independent_cer": _mean([item.independent_coverage for item in adjudicated_coverage]), "critical_coverage": _mean([item.critical_coverage for item in adjudicated_coverage])}
    return {"summary": summary, "traces": traces, "failures": failures, "adjudicated_coverage": gold_cov}


def _failure_types(matches, graph: RequirementGraph, gold: RequirementGraph, coverage) -> list[str]:
    failures = []
    if matches.unmatched_gold:
        failures.append("MISSING_REQUIREMENT")
    if matches.unmatched_predicted:
        failures.append("OVER_SPECIFIED_REQUIREMENT")
    for item in matches.matches:
        predicted, expected = graph.requirement(item.predicted_requirement_id), gold.requirement(item.gold_requirement_id)
        if predicted.fact_type != expected.fact_type:
            failures.append("WRONG_REQUIREMENT_TYPE")
        if predicted.role != expected.role:
            failures.append("WRONG_ROLE")
        if predicted.criticality != expected.criticality:
            failures.append("WRONG_CRITICALITY")
    if "EVIDENCE_REUSE_INFLATION" in coverage.warnings:
        failures.append("EVIDENCE_REUSE_INFLATION")
    if not coverage.answer_eligible:
        failures.append("EVIDENCE_MAPPING_FAILURE")
    return sorted(set(failures))
