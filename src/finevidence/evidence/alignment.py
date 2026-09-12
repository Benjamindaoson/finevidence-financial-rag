from __future__ import annotations

import re
from collections import defaultdict

from finevidence.contracts.evidence import Evidence
from finevidence.contracts.requirements import (
    EvidenceReuseEvent,
    FactEvidenceAlignment,
    IndependentCoverageResult,
    Requirement,
    RequirementGraph,
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def align_requirement_to_evidence(requirement: Requirement, evidence: Evidence) -> FactEvidenceAlignment:
    requirement_tokens = _tokens(" ".join(filter(None, [requirement.description, requirement.entity, requirement.metric, requirement.period, requirement.segment, requirement.basis, requirement.role])))
    evidence_tokens = _tokens(evidence.text)
    score = len(requirement_tokens & evidence_tokens) / max(len(requirement_tokens), 1)
    matched_slots = []
    mismatched_slots = []
    for field in ("entity", "metric", "period", "segment", "basis", "geography", "currency", "unit"):
        value = getattr(requirement, field)
        if not value:
            continue
        if value.lower() in evidence.text.lower():
            matched_slots.append(field)
        elif getattr(evidence, field, None) and getattr(evidence, field).lower() != value.lower():
            mismatched_slots.append(field)
    causal = bool(re.search(r"because|due to|driven by|resulted from|impact|reflects|原因|由于|驱动", evidence.text, re.I))
    if requirement.fact_type == "EXPLANATORY_FACT":
        support_type = "EXPLANATORY_SUPPORT" if causal and score >= 0.1 else ("PARTIAL_SUPPORT" if score else "NO_SUPPORT")
    elif requirement.fact_type == "DERIVED_FACT":
        support_type = "DERIVATION_INPUT" if score else "NO_SUPPORT"
    elif requirement.fact_type == "CONTEXT_FACT":
        support_type = "CONTEXT_ONLY" if score else "NO_SUPPORT"
    else:
        support_type = "DIRECT_SUPPORT" if score >= 0.15 and not mismatched_slots else ("PARTIAL_SUPPORT" if score else "NO_SUPPORT")
    return FactEvidenceAlignment(
        requirement_id=requirement.requirement_id,
        evidence_id=evidence.evidence_id,
        support_type=support_type,
        alignment_score=score,
        matched_slots=matched_slots,
        mismatched_slots=mismatched_slots,
        reusable=False,
        reason="slot and lexical alignment" if score else "no supporting overlap",
    )


def _same_slot(left: Requirement, right: Requirement, field: str) -> bool:
    return getattr(left, field) == getattr(right, field)


class EvidenceReusePolicy:
    """Conservative in-memory policy for independent requirement coverage."""

    def __init__(self, require_same_role: bool = True, require_same_period: bool = True, require_same_metric: bool = True, require_same_entity: bool = True) -> None:
        self.require_same_role = require_same_role
        self.require_same_period = require_same_period
        self.require_same_metric = require_same_metric
        self.require_same_entity = require_same_entity

    def compatible(self, left: Requirement, right: Requirement) -> bool:
        fields = []
        if self.require_same_role:
            fields.append("role")
        if self.require_same_period:
            fields.append("period")
        if self.require_same_metric:
            fields.append("metric")
        if self.require_same_entity:
            fields.append("entity")
        return all(_same_slot(left, right, field) for field in fields)


def _independent_ids(graph: RequirementGraph, supported: set[str], invalid_ids: set[str]) -> set[str]:
    independent = supported - invalid_ids
    changed = True
    while changed:
        changed = False
        for requirement in graph.requirements:
            if requirement.fact_type == "DERIVED_FACT" and requirement.requirement_id not in independent:
                if requirement.operation and set(requirement.depends_on) <= independent:
                    independent.add(requirement.requirement_id)
                    changed = True
    return independent


def evaluate_independent_coverage(
    graph: RequirementGraph,
    alignments: list[FactEvidenceAlignment],
    selected_evidence_ids: set[str],
    reuse_policy: EvidenceReusePolicy | None = None,
) -> IndependentCoverageResult:
    requirements = {item.requirement_id: item for item in graph.requirements}
    candidates = [
        item for item in alignments
        if item.evidence_id in selected_evidence_ids
        and item.requirement_id in requirements
        and item.support_type != "NO_SUPPORT"
        and (not requirements[item.requirement_id].acceptable_evidence_ids or item.evidence_id in requirements[item.requirement_id].acceptable_evidence_ids)
    ]
    by_evidence: dict[str, list[FactEvidenceAlignment]] = defaultdict(list)
    for item in candidates:
        by_evidence[item.evidence_id].append(item)
    events = []
    invalid_ids: set[str] = set()
    policy = reuse_policy or EvidenceReusePolicy()
    reuse_groups = 0
    for evidence_id, group in by_evidence.items():
        if len(group) < 2:
            continue
        reuse_groups += 1
        first = group[0]
        compatible = all(policy.compatible(requirements[first.requirement_id], requirements[item.requirement_id]) for item in group[1:])
        if compatible:
            events.append(EvidenceReuseEvent(evidence_id=evidence_id, requirement_ids=[item.requirement_id for item in group], valid=True, reason="compatible role and slots"))
        else:
            invalid_ids.update(item.requirement_id for item in group[1:])
            events.append(EvidenceReuseEvent(evidence_id=evidence_id, requirement_ids=[item.requirement_id for item in group], valid=False, reason="incompatible requirement roles or slots"))
    supported = {item.requirement_id for item in candidates}
    independent = _independent_ids(graph, supported, invalid_ids)
    critical = {item.requirement_id for item in graph.requirements if item.criticality == "CRITICAL"}
    missing_critical = sorted(critical - independent)
    total = len(requirements)
    critical_total = len(critical)
    raw = len(supported) / total if total else 0.0
    independent_rate = len(independent) / total if total else 0.0
    critical_rate = len(critical & independent) / critical_total if critical_total else 1.0
    warnings = []
    if raw > independent_rate:
        warnings.append("EVIDENCE_REUSE_INFLATION")
    if missing_critical:
        warnings.append("CRITICAL_REQUIREMENT_MISSING")
    return IndependentCoverageResult(
        raw_self_coverage=raw,
        independent_coverage=independent_rate,
        critical_coverage=critical_rate,
        critical_missing_rate=(len(missing_critical) / critical_total if critical_total else 0.0),
        evidence_reuse_rate=(sum(len(group) for group in by_evidence.values() if len(group) > 1) / len(candidates) if candidates else 0.0),
        invalid_reuse_rate=(sum(not event.valid for event in events) / len(events) if events else 0.0),
        answer_eligible=not missing_critical,
        covered_requirement_ids=sorted(supported),
        independent_requirement_ids=sorted(independent),
        missing_critical_requirements=missing_critical,
        invalid_reuse_events=[event for event in events if not event.valid],
        warnings=warnings,
    )
