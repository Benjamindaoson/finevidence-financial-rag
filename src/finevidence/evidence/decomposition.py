from __future__ import annotations

import re

from finevidence.contracts.benchmark import FactRequirement


def decompose_required_facts(question: str) -> list[FactRequirement]:
    parts = [part.strip(" ,;:?.") for part in re.split(r"\band\b|\bthen\b|\balso\b", question, flags=re.IGNORECASE)]
    parts = [part for part in parts if part]
    if not parts:
        parts = [question.strip()]
    return [
        FactRequirement(fact_id=f"predicted-{index}", description=part, acceptable_evidence_ids=["__predicted__"])
        for index, part in enumerate(parts, start=1)
    ]
