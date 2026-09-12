from __future__ import annotations

import re
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field

from finevidence.contracts.benchmark import FactRequirement, FactSlots
from finevidence.evidence.decomposition import decompose_required_facts
from finevidence.ranking.facets import extract_facets


QuestionType = Literal["factual", "comparison", "numerical", "explanation", "trend", "multi-document synthesis"]


class DecompositionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant: str
    status: Literal["READY", "N/A"]
    question_type: QuestionType | None = None
    facts: list[FactRequirement] = Field(default_factory=list)
    reason: str | None = None


def classify_question(question: str) -> QuestionType:
    text = question.lower()
    if re.search(r"\bwhy\b|\breason\b|\bexplain\b|\bdue to\b", text):
        return "explanation"
    if re.search(r"which .*\b(largest|highest|lowest|smallest)\b|\bcompare\b|\bversus\b|\bdifference\b", text):
        return "comparison"
    if re.search(r"\bpercentage\b|\bcalculate\b|\bhow much\b|\bchange in\b|\bwhat is the amount\b", text):
        return "numerical"
    if re.search(r"\btrend\b|\bincrease\b|\bdecrease\b|\bover time\b", text):
        return "trend"
    if re.search(r"\baccording to\b|\bboth\b|\bdifferent documents?\b", text):
        return "multi-document synthesis"
    return "factual"


def _slots(question: str, fact_type: str, role: str, critical: bool = True) -> FactSlots:
    facets = extract_facets(question)
    return FactSlots(
        fact_type=fact_type,
        entity=facets.entity,
        metric=facets.metric,
        period=facets.period,
        segment=facets.segment,
        basis=facets.basis,
        role=role,
        critical=critical,
    )


def _template_facts(question: str) -> list[FactRequirement]:
    question_type = classify_question(question)
    if question_type == "comparison":
        roles = ("comparison_value_a", "comparison_value_b", "comparison_basis")
    elif question_type == "numerical":
        roles = ("numerator", "denominator", "operation") if re.search(r"percentage|ratio|rate|change", question, re.I) else ("target_value",)
    elif question_type == "explanation":
        roles = ("observed_change", "management_cause")
    elif question_type == "trend":
        roles = ("prior_state", "current_state", "trend_direction")
    elif question_type == "multi-document synthesis":
        roles = ("source_fact_a", "source_fact_b")
    else:
        roles = ("target_value",)
    return [
        FactRequirement(
            fact_id=f"predicted-{index}",
            description=f"{role.replace('_', ' ')} required to answer: {question}",
            acceptable_evidence_ids=["__unresolved__"],
            slots=_slots(question, "financial_metric", role, role not in {"comparison_basis", "trend_direction"}),
        )
        for index, role in enumerate(roles, start=1)
    ]


def _evidence_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def decompose_required_facts_by_variant(
    question: str,
    variant: Literal["D0", "D1", "D2", "D3"],
    candidate_evidence: Sequence[tuple[str, str]] | None = None,
) -> DecompositionResult:
    question_type = classify_question(question)
    if variant == "D1":
        return DecompositionResult(variant=variant, status="N/A", question_type=question_type, reason="LLM_PROVIDER_NOT_CONFIGURED")
    if variant == "D0":
        facts = [
            fact.model_copy(update={"slots": _slots(question, "financial_metric", "legacy_fact")})
            for fact in decompose_required_facts(question)
        ]
        return DecompositionResult(variant=variant, status="READY", question_type=question_type, facts=facts)
    facts = _template_facts(question)
    if variant == "D2" or not candidate_evidence:
        return DecompositionResult(variant=variant, status="READY", question_type=question_type, facts=facts)
    query_tokens = _evidence_tokens(question)
    bounded = []
    for fact in facts:
        best_id = "__unresolved__"
        best_score = 0.0
        for evidence_id, evidence_text in candidate_evidence:
            evidence_tokens = _evidence_tokens(evidence_text)
            score = len(query_tokens & evidence_tokens) / max(len(query_tokens), 1)
            if score > best_score:
                best_id, best_score = evidence_id, score
        bounded.append(fact.model_copy(update={"acceptable_evidence_ids": [best_id]}))
    return DecompositionResult(variant=variant, status="READY", question_type=question_type, facts=bounded)
