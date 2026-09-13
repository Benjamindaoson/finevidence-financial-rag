from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict


FailureCause = Literal["TEXT_RETRIEVAL_MISS", "TABLE_STRUCTURE_LOSS", "PAGE_FRAGMENTATION", "LAYOUT_DEPENDENCY", "CHART_VISUAL_ONLY", "UNKNOWN"]
RecoveryAction = Literal["TEXT_RETRY", "STRUCTURED_TABLE_RETRIEVAL", "ADJACENT_PAGE_RETRIEVAL", "VISUAL_RETRIEVAL", "ABSTAIN_ESCALATE"]


class FailureRoute(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cause: FailureCause
    action: RecoveryAction
    confidence: float
    oracle: bool
    reason: str


def oracle_failure_route(cause: str) -> FailureRoute:
    if cause.startswith("TABLE_") or cause == "MULTI_LEVEL_HEADER" or cause == "UNIT_HEADER_LOSS":
        return FailureRoute(cause="TABLE_STRUCTURE_LOSS", action="STRUCTURED_TABLE_RETRIEVAL", confidence=1.0, oracle=True, reason="gold evaluation category")
    if cause in {"CHART_VALUE", "CHART_LEGEND", "VISUAL_ONLY_INFORMATION", "CAPTION_MISMATCH"}:
        return FailureRoute(cause="CHART_VISUAL_ONLY", action="VISUAL_RETRIEVAL", confidence=1.0, oracle=True, reason="gold evaluation category")
    if cause == "MULTI_COLUMN_READING_ORDER":
        return FailureRoute(cause="LAYOUT_DEPENDENCY", action="VISUAL_RETRIEVAL", confidence=1.0, oracle=True, reason="gold evaluation category")
    if cause == "FOOTNOTE_LOSS" or cause == "PAGE_FRAGMENTATION":
        return FailureRoute(cause="PAGE_FRAGMENTATION", action="ADJACENT_PAGE_RETRIEVAL", confidence=1.0, oracle=True, reason="gold evaluation category")
    if cause == "TEXT_RETRIEVAL_MISS":
        return FailureRoute(cause="TEXT_RETRIEVAL_MISS", action="TEXT_RETRY", confidence=1.0, oracle=True, reason="gold evaluation category")
    return FailureRoute(cause="UNKNOWN", action="ABSTAIN_ESCALATE", confidence=1.0, oracle=True, reason="unmapped gold category")


def predict_failure_route(question: str, *, initial_coverage: float, parser_has_table_ir: bool) -> FailureRoute:
    lower = question.lower()
    if re.search(r"chart|figure|plot|graph|legend|illustration|diagram", lower):
        cause, action, reason = "CHART_VISUAL_ONLY", "VISUAL_RETRIEVAL", "visual cue in question"
    elif re.search(r"table|row|column|unit|header", lower) and parser_has_table_ir:
        cause, action, reason = "TABLE_STRUCTURE_LOSS", "STRUCTURED_TABLE_RETRIEVAL", "table cue with available Table IR"
    elif re.search(r"footnote|note|exception|continued|continuation", lower):
        cause, action, reason = "PAGE_FRAGMENTATION", "ADJACENT_PAGE_RETRIEVAL", "page-context cue in question"
    elif initial_coverage < 1.0:
        cause, action, reason = "TEXT_RETRIEVAL_MISS", "TEXT_RETRY", "missing initial qualified coverage"
    else:
        cause, action, reason = "UNKNOWN", "ABSTAIN_ESCALATE", "no observable failure cue"
    return FailureRoute(cause=cause, action=action, confidence=0.7, oracle=False, reason=reason)
