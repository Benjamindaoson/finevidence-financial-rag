from __future__ import annotations

import re
import hashlib

from finevidence.contracts.evidence import Evidence
from finevidence.contracts.p0_h import HSBCHardCase
from finevidence.ranking.facets import evidence_facets, extract_facets


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _facet_map(query: str) -> dict[str, str | None]:
    facets = extract_facets(query)
    return {field: getattr(facets, field) for field in ("entity", "metric", "period", "segment", "basis", "currency", "geography", "period_type")}


def build_hsbc_hard_case(question: str, positive: Evidence, negatives: list[Evidence], category: str) -> HSBCHardCase:
    if not negatives:
        raise ValueError("hard case requires a negative")
    query_tokens = _tokens(question)
    positive_facets = evidence_facets(positive)
    query_facets = _facet_map(question)
    for field, expected in query_facets.items():
        actual = getattr(positive_facets, field)
        if expected and actual and expected.lower() != actual.lower():
            raise ValueError(f"positive does not match query facet: {field}")
    valid_negatives = []
    for negative in negatives:
        if len(query_tokens & _tokens(negative.text)) == 0:
            raise ValueError("hard negative is not similar to query")
        negative_facets = evidence_facets(negative)
        conflicts = [field for field in query_facets if getattr(positive_facets, field) != getattr(negative_facets, field)]
        if positive.document_id != negative.document_id:
            conflicts.append("document_source")
        if not conflicts:
            raise ValueError("hard negative lacks facet conflict")
        valid_negatives.append(negative)
    evidence = [positive, *valid_negatives]
    case_key = "|".join([question, positive.evidence_id, *[item.evidence_id for item in valid_negatives]])
    return HSBCHardCase(dataset_name="HSBCNaturalHard-v1", case_id=f"hsbc-hard-{hashlib.sha256(case_key.encode()).hexdigest()[:12]}", question=question, category=category, positive_evidence_id=positive.evidence_id, hard_negative_ids=[item.evidence_id for item in valid_negatives], candidate_evidence_ids=[item.evidence_id for item in evidence], source_hashes={item.evidence_id: item.content_hash for item in evidence}, adjudicated_facets={field: getattr(positive_facets, field) for field in query_facets}, verification_method="model_assisted_adjudicated", human_verified=False)


def _query_for(evidence: Evidence) -> str:
    facets = evidence_facets(evidence)
    parts = [facets.entity or "HSBC Holdings", facets.period or "2025", facets.metric or "financial results"]
    for field in ("segment", "basis", "currency", "geography", "period_type"):
        value = getattr(facets, field)
        if value and str(value) not in parts:
            parts.append(str(value))
    return " ".join(parts)


def mine_hsbc_natural_hard_cases(evidence: list[Evidence], target_count: int = 60) -> list[HSBCHardCase]:
    facets = {item.evidence_id: evidence_facets(item) for item in evidence}
    fields = ("period", "metric", "entity", "segment", "basis", "currency", "geography", "period_type")
    candidates = []
    for positive in evidence:
        query = _query_for(positive)
        query_tokens = _tokens(query)
        if not facets[positive.evidence_id].metric:
            continue
        scored = []
        for negative in evidence:
            if negative.evidence_id == positive.evidence_id:
                continue
            negative_facets = facets[negative.evidence_id]
            overlap = len(query_tokens & _tokens(negative.text)) / max(len(query_tokens), 1)
            conflicts = [field for field in fields if getattr(facets[positive.evidence_id], field) != getattr(negative_facets, field) and (getattr(facets[positive.evidence_id], field) or getattr(negative_facets, field))]
            if positive.document_id != negative.document_id:
                conflicts.append("document_source")
            if overlap >= 0.30 and conflicts:
                scored.append((overlap, negative.evidence_id, negative, conflicts))
        for overlap, _, negative, conflicts in sorted(scored, key=lambda item: (-item[0], item[1]))[:8]:
            for field in ("period", "metric", "entity", "segment", "basis", "currency", "geography", "period_type", "document_source"):
                if field not in conflicts:
                    continue
                category = {"period": "TEMPORAL", "metric": "RELATED_METRIC" if facets[positive.evidence_id].metric and facets[negative.evidence_id].metric and "CET1" in facets[positive.evidence_id].metric and "CET1" in facets[negative.evidence_id].metric else "METRIC", "entity": "ENTITY", "segment": "SEGMENT", "basis": "BASIS", "currency": "CURRENCY", "geography": "GEOGRAPHY", "period_type": "PERIOD_TYPE", "document_source": "DOCUMENT_SOURCE"}[field]
                candidates.append((category, overlap, positive.evidence_id, query, positive, negative))
    category_order = {name: index for index, name in enumerate(("TEMPORAL", "METRIC", "RELATED_METRIC", "ENTITY", "SEGMENT", "BASIS", "CURRENCY", "GEOGRAPHY", "PERIOD_TYPE", "TABLE_CONTEXT", "DOCUMENT_SOURCE"))}
    selected = []
    used_pairs = set()
    grouped = {category: sorted((item for item in candidates if item[0] == category), key=lambda value: (-value[1], value[2], value[5].evidence_id)) for category in {item[0] for item in candidates}}
    categories = sorted(grouped, key=lambda item: category_order.get(item, 99))
    for offset in range(max(len(grouped), 1)):
        for category in categories:
            pool = grouped[category]
            if offset >= len(pool):
                continue
            item = pool[offset]
            pair = (item[2], item[5].evidence_id)
            if pair in used_pairs:
                continue
            try:
                case = build_hsbc_hard_case(item[3], item[4], [item[5]], category=category)
            except ValueError:
                continue
            selected.append(case)
            used_pairs.add(pair)
            if len(selected) >= target_count:
                return selected
    return selected


def _ranking_metrics(cases, rankings, top_k: int = 5) -> dict:
    import math

    recall, rr, ndcg, errors, top1 = [], [], [], [], []
    for case in cases:
        ranking = rankings[case.case_id]
        positive_rank = ranking.index(case.positive_evidence_id) + 1 if case.positive_evidence_id in ranking else math.inf
        negative_rank = min((ranking.index(item) + 1 for item in case.hard_negative_ids if item in ranking), default=math.inf)
        top = ranking[:top_k]
        recall.append(float(case.positive_evidence_id in top))
        rr.append(1.0 / positive_rank if math.isfinite(positive_rank) else 0.0)
        ndcg.append(1.0 / math.log2(positive_rank + 1) if positive_rank <= 10 else 0.0)
        errors.append(float(negative_rank < positive_rank))
        top1.append(float(bool(ranking) and ranking[0] == case.positive_evidence_id))
    return {"recall_at_5": sum(recall) / len(recall) if recall else "N/A", "mrr": sum(rr) / len(rr) if rr else "N/A", "ndcg_at_10": sum(ndcg) / len(ndcg) if ndcg else "N/A", "hn_error": sum(errors) / len(errors) if errors else "N/A", "top1_positive_rate": sum(top1) / len(top1) if top1 else "N/A"}


def _rank_with_facets(query: str, candidates, evidence_by_id: dict[str, Evidence], facets, top_k: int):
    """Rank using an explicit facet set so predicted and adjudicated runs stay separate."""
    from finevidence.ranking.rerankers import _ranked

    scores = []
    for item in candidates:
        actual = evidence_facets(evidence_by_id[item.evidence_id])
        matches = sum(
            1.0
            for field, expected in facets.items()
            if expected and getattr(actual, field, None) and str(expected).lower() == str(getattr(actual, field)).lower()
        )
        scores.append(max(item.retrieval_score, 0.0) * 0.1 + matches)
    return [item.evidence_id for item in _ranked(candidates, scores, top_k)]


def evaluate_hsbc_ranking(cases: list[HSBCHardCase], evidence: list[Evidence], top_k: int = 5) -> dict:
    from finevidence.ranking.rerankers import FacetAwareReranker, HardNegativeAwareReranker
    from finevidence.retrieval.dense import DenseRetriever
    from finevidence.retrieval.hybrid import HybridRetriever

    by_id = {item.evidence_id: item for item in evidence}
    dense, hybrid = DenseRetriever(), HybridRetriever()
    dense.fit(evidence)
    hybrid.fit(evidence)
    dense_rankings = {case.case_id: [item.evidence_id for item in dense.search(case.question, len(evidence))] for case in cases}
    hybrid_rankings = {case.case_id: [item.evidence_id for item in hybrid.search(case.question, len(evidence))] for case in cases}
    facet = FacetAwareReranker()
    predicted_rankings = {case.case_id: [item.evidence_id for item in facet.rank(case.question, hybrid.search(case.question, len(evidence)), by_id, len(evidence))] for case in cases}
    adjudicated_rankings = {
        case.case_id: _rank_with_facets(
            case.question,
            hybrid.search(case.question, len(evidence)),
            by_id,
            case.adjudicated_facets,
            len(evidence),
        )
        for case in cases
    }
    trained = HardNegativeAwareReranker().fit([_as_mini_case(case) for case in cases], by_id)
    aware_rankings = {case.case_id: [item.evidence_id for item in trained.rank(case.question, hybrid.search(case.question, len(evidence)), by_id, len(evidence))] for case in cases}
    rankings = {"Dense": dense_rankings, "Hybrid + Generic": hybrid_rankings, "+ Predicted Facets": predicted_rankings, "+ Adjudicated Facets": adjudicated_rankings, "+ Financial-aware deterministic reranker": aware_rankings}
    result = {name: _ranking_metrics(cases, values, top_k) for name, values in rankings.items()}
    result["per_category_hn_error"] = {name: {category: _ranking_metrics([case for case in cases if case.category == category], values, top_k)["hn_error"] for category in sorted({case.category for case in cases})} for name, values in rankings.items()}
    facet_rows = []
    for case in cases:
        predicted = _facet_map(case.question)
        for field, expected in case.adjudicated_facets.items():
            if expected is None:
                continue
            facet_rows.append({"field": field, "correct": bool(predicted.get(field) and str(predicted[field]).lower() == str(expected).lower())})
    result["facet_accuracy"] = {
        field: (sum(item["correct"] for item in facet_rows if item["field"] == field) / sum(1 for item in facet_rows if item["field"] == field))
        if any(item["field"] == field for item in facet_rows) else "N/A"
        for field in sorted({item["field"] for item in facet_rows})
    }
    predicted_hn = result["+ Predicted Facets"]["hn_error"]
    adjudicated_hn = result["+ Adjudicated Facets"]["hn_error"]
    result["ranking_oracle_gap"] = predicted_hn - adjudicated_hn if isinstance(predicted_hn, (int, float)) and isinstance(adjudicated_hn, (int, float)) else "N/A"
    result["rankings"] = rankings
    return result


def _as_mini_case(case: HSBCHardCase):
    from finevidence.contracts.benchmark import MiniCase, RequiredEvidenceRef

    return MiniCase(question_id=case.case_id, question=case.question, gold_answer=case.positive_evidence_id, required_evidence=[RequiredEvidenceRef(evidence_id=case.positive_evidence_id)], required_facts=[], failure_type=f"HARD_NEGATIVE_{case.category}", answerable=True, positive_evidence_id=case.positive_evidence_id, hard_negative_ids=case.hard_negative_ids)
