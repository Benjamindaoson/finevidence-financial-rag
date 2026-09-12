from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

from finevidence.contracts.benchmark import FactRequirement, MiniCase
from finevidence.contracts.p0_h import AnnotationPass, P0HAnnotationManifest, RequirementAdjudicatedCase, RequirementMatch, RequirementMatchResult
from finevidence.contracts.requirements import Requirement, RequirementGraph
from finevidence.evidence.fact_understanding import classify_question
from finevidence.evidence.requirement_graph import decompose_requirement_graph


def _tokens(text: str) -> set[str]:
    return {token for token in text.lower().replace("/", " ").replace("-", " ").split() if token}


def _pair_score(predicted: Requirement, gold: Requirement) -> tuple[float, list[str]]:
    score = 0.0
    matched = []
    if predicted.fact_type == gold.fact_type:
        score += 0.35
    if predicted.role == gold.role:
        score += 0.30
        matched.append("role")
    for field in ("entity", "metric", "period", "segment", "basis", "geography", "currency", "unit"):
        left, right = getattr(predicted, field), getattr(gold, field)
        if left and right:
            if left.lower() == right.lower():
                score += 0.05
                matched.append(field)
            else:
                score -= 0.05
    overlap = _tokens(predicted.description) & _tokens(gold.description)
    score += 0.15 * len(overlap) / max(len(_tokens(predicted.description) | _tokens(gold.description)), 1)
    return max(0.0, min(1.0, score)), matched


def match_requirements(predicted: RequirementGraph, gold: RequirementGraph, threshold: float = 0.45) -> RequirementMatchResult:
    pairs = []
    for p, g in itertools.product(predicted.requirements, gold.requirements):
        score, slots = _pair_score(p, g)
        if score >= threshold:
            pairs.append((score, p.requirement_id, g.requirement_id, slots))
    pairs.sort(key=lambda item: (-item[0], item[1], item[2]))
    used_p, used_g, matches = set(), set(), []
    for score, p_id, g_id, slots in pairs:
        if p_id in used_p or g_id in used_g:
            continue
        used_p.add(p_id)
        used_g.add(g_id)
        matches.append(RequirementMatch(predicted_requirement_id=p_id, gold_requirement_id=g_id, score=score, matched_slots=slots))
    return RequirementMatchResult(
        matches=sorted(matches, key=lambda item: item.predicted_requirement_id),
        unmatched_predicted=sorted({item.requirement_id for item in predicted.requirements} - used_p),
        unmatched_gold=sorted({item.requirement_id for item in gold.requirements} - used_g),
    )


def _source_graph(case: MiniCase, evidence_ids: list[str]) -> RequirementGraph:
    facts = [item for item in case.required_facts if isinstance(item, FactRequirement)]
    derivation = str((case.gold_supporting_facts or {}).get("derivation") or "")
    if derivation and len(facts) >= 1:
        inputs = []
        for index, fact in enumerate(facts[:2], start=1):
            inputs.append(Requirement(requirement_id=f"R{index}", description=fact.description, fact_type="RETRIEVED_FACT", role=f"derivation_input_{index}", criticality="CRITICAL", acceptable_evidence_ids=fact.acceptable_evidence_ids, evidence_role="DERIVATION_INPUT"))
        inputs.append(Requirement(requirement_id="R3", description=f"derived answer for: {case.question}", fact_type="DERIVED_FACT", role="derived_result", operation=derivation, depends_on=[item.requirement_id for item in inputs], criticality="CRITICAL", evidence_role="DERIVATION_INPUT"))
        return RequirementGraph(requirements=inputs, edges=[])
    fact = facts[0] if facts else None
    return RequirementGraph(requirements=[Requirement(requirement_id="R1", description=fact.description if fact else case.question, fact_type="RETRIEVED_FACT", role="target_value", criticality="CRITICAL", acceptable_evidence_ids=fact.acceptable_evidence_ids if fact else evidence_ids, evidence_role="VALUE_SUPPORT")])


def _adjudicated_graph(case: MiniCase, evidence_ids: list[str]) -> RequirementGraph:
    """Build requirements from the question/program, not from flattened support prose."""
    kind = classify_question(case.question)
    derivation = str((case.gold_supporting_facts or {}).get("derivation") or "")
    if kind in {"comparison", "numerical", "trend", "explanation", "multi-document synthesis"} or derivation:
        template = decompose_requirement_graph(case.question)
        requirements = []
        for requirement in template.requirements:
            if requirement.fact_type == "DERIVED_FACT":
                requirements.append(requirement.model_copy(update={"acceptable_evidence_ids": [], "evidence_role": None}))
                continue
            evidence_role = "EXPLANATION_SUPPORT" if requirement.fact_type == "EXPLANATORY_FACT" else (
                "CONTEXT_SUPPORT" if requirement.fact_type == "CONTEXT_FACT" else (
                    "COMPARISON_SUPPORT" if kind == "comparison" else "DERIVATION_INPUT" if kind in {"numerical", "trend"} else "VALUE_SUPPORT"
                )
            )
            requirements.append(requirement.model_copy(update={"acceptable_evidence_ids": sorted(set(evidence_ids)), "evidence_role": evidence_role}))
        return RequirementGraph(requirements=requirements, edges=template.edges)
    return _source_graph(case, evidence_ids)


def build_requirement_adjudicated_subset(benchmark, case_ids: list[str], output_dir: Path, pass_b_graphs: dict[str, RequirementGraph] | None = None, created_at_utc: str = "2026-09-13T00:00:00Z") -> P0HAnnotationManifest:
    selected = [case for case in benchmark.cases if case.question_id in set(case_ids)]
    selected.sort(key=lambda case: case.question_id)
    rows = []
    for case in selected:
        evidence_ids = [item.evidence_id for item in case.required_evidence]
        adjudicated = _adjudicated_graph(case, evidence_ids)
        pass_a = AnnotationPass(pass_name="A", method="source_supporting_evidence_rules", requirements=adjudicated, question_type=classify_question(case.question), created_at_utc=created_at_utc)
        pass_b_graph = (pass_b_graphs or {}).get(case.question_id, decompose_requirement_graph(case.question))
        pass_b = AnnotationPass(pass_name="B", method="local_llm_or_independent_template", requirements=pass_b_graph, question_type=classify_question(case.question), created_at_utc=created_at_utc)
        disagreements = []
        if len(pass_a.requirements.requirements) != len(pass_b.requirements.requirements):
            disagreements.append("requirement_count")
        if pass_a.question_type != pass_b.question_type:
            disagreements.append("question_type")
        rows.append(RequirementAdjudicatedCase(dataset_name="RequirementAdjudicated-v1", case_id=case.question_id, source_dataset=case.source_dataset or "unknown", source_record_id=case.source_record_id, source_question_id=case.source_question_id, question=case.question, question_type=classify_question(case.question), requirements=adjudicated, pass_a=pass_a, pass_b=pass_b, disagreements=disagreements, annotation_method="dual_pass_model_assisted_adjudication", human_verified=False))
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = "".join(item.model_dump_json() + "\n" for item in rows)
    (output_dir / "requirement_annotations.jsonl").write_text(payload, encoding="utf-8")
    cases_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    manifest = P0HAnnotationManifest(dataset_name="RequirementAdjudicated-v1", source_benchmark=benchmark.manifest["benchmark_id"], source_manifest_sha256=hashlib.sha256(json.dumps(benchmark.manifest, sort_keys=True).encode()).hexdigest(), case_count=len(rows), question_type_distribution={kind: sum(item.question_type == kind for item in rows) for kind in {item.question_type for item in rows}}, annotation_method="dual_pass_model_assisted_adjudication", human_verified=False, pass_a_method="source_supporting_evidence_rules", pass_b_method="local_llm_or_independent_template", adjudication_method="source evidence + gold answer/program adjudication", cases_sha256=cases_hash)
    (output_dir / "annotation_manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (output_dir / "annotation_pass_a.jsonl").write_text("".join(item.pass_a.model_dump_json() + "\n" for item in rows), encoding="utf-8")
    (output_dir / "annotation_pass_b.jsonl").write_text("".join(item.pass_b.model_dump_json() + "\n" for item in rows), encoding="utf-8")
    (output_dir / "annotation_adjudicated.jsonl").write_text(payload, encoding="utf-8")
    agreements = {"requirement_count_agreement": [], "question_type_agreement": [], "fact_type_agreement": [], "criticality_agreement": [], "role_agreement": [], "dependency_agreement": [], "evidence_mapping_agreement": []}
    for item in rows:
        a, b = item.pass_a.requirements, item.pass_b.requirements
        match = match_requirements(b, a)
        agreements["requirement_count_agreement"].append(float(len(a.requirements) == len(b.requirements)))
        agreements["question_type_agreement"].append(float(item.pass_a.question_type == item.pass_b.question_type))
        for key, predicate in (("fact_type_agreement", lambda p, g: p.fact_type == g.fact_type), ("criticality_agreement", lambda p, g: p.criticality == g.criticality), ("role_agreement", lambda p, g: p.role == g.role), ("dependency_agreement", lambda p, g: set(p.depends_on) == set(g.depends_on)), ("evidence_mapping_agreement", lambda p, g: set(p.acceptable_evidence_ids) == set(g.acceptable_evidence_ids))):
            agreements[key].append(sum(predicate(b.requirement(pair.predicted_requirement_id), a.requirement(pair.gold_requirement_id)) for pair in match.matches) / len(match.matches) if match.matches else 0.0)
    (output_dir / "annotation_agreement.json").write_text(json.dumps({key: sum(value) / len(value) if value else 0.0 for key, value in agreements.items()}, indent=2) + "\n", encoding="utf-8")
    return manifest
