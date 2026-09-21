from __future__ import annotations

import math

from finevidence.contracts.evidence import RetrievedEvidence


def _normalise(items: list[RetrievedEvidence]) -> dict[str, float]:
    if not items:
        return {}
    values = [float(item.retrieval_score) for item in items]
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return {item.evidence_id: 1.0 for item in items}
    return {
        item.evidence_id: (float(item.retrieval_score) - lo) / (hi - lo)
        for item in items
    }


def weighted_fusion(
    text: list[RetrievedEvidence],
    visual: list[RetrievedEvidence],
    *,
    text_weight: float = 0.5,
    top_k: int = 10,
) -> list[RetrievedEvidence]:
    text_scores, visual_scores = _normalise(text), _normalise(visual)
    ids = set(text_scores) | set(visual_scores)
    scores = {
        evidence_id: text_weight * text_scores.get(evidence_id, 0.0)
        + (1 - text_weight) * visual_scores.get(evidence_id, 0.0)
        for evidence_id in ids
    }
    return [
        RetrievedEvidence(evidence_id=evidence_id, rank=rank, retrieval_score=score)
        for rank, (evidence_id, score) in enumerate(
            sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k],
            start=1,
        )
    ]


def reciprocal_rank_fusion(
    rankings: list[list[RetrievedEvidence]],
    *,
    k: int = 60,
    top_k: int = 10,
    expose_as_rerank_score: bool = True,
) -> list[RetrievedEvidence]:
    """Fuse heterogeneous rankings without assuming comparable raw scores."""

    scores: dict[str, float] = {}
    for items in rankings:
        for item in items:
            scores[item.evidence_id] = scores.get(item.evidence_id, 0.0) + 1.0 / (
                k + item.rank
            )

    return [
        RetrievedEvidence(
            evidence_id=evidence_id,
            rank=rank,
            retrieval_score=float(score),
            rerank_score=float(score) if expose_as_rerank_score else None,
        )
        for rank, (evidence_id, score) in enumerate(
            sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k],
            start=1,
        )
    ]


def rrf_fusion(
    text: list[RetrievedEvidence],
    visual: list[RetrievedEvidence],
    *,
    k: int = 60,
    top_k: int = 10,
) -> list[RetrievedEvidence]:
    # Backward-compatible two-list wrapper used by the multimodal experiments.
    return reciprocal_rank_fusion(
        [text, visual],
        k=k,
        top_k=top_k,
        expose_as_rerank_score=False,
    )
