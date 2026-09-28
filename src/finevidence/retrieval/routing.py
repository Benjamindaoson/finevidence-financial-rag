from __future__ import annotations

import re

from finevidence.contracts.b3 import RoutingDecision


_VISUAL = re.compile(r"\b(chart|figure|diagram|plot|graph|legend|shown|where|position|layout|visual|image|table row|column)\b", re.I)
_TABLE = re.compile(r"\b(table|row|column|revenue|ratio|percent|amount|higher|lower|compare|calculation)\b", re.I)


def route_query(question: str, *, initial_critical_coverage: float = 1.0, parser_confidence: float = 1.0) -> RoutingDecision:
    visual = bool(_VISUAL.search(question))
    table = bool(_TABLE.search(question))
    if visual and table:
        route, reason = "MIXED", "visual and tabular cues"
    elif visual or initial_critical_coverage < 1.0 and parser_confidence < 0.75:
        route, reason = "VISUAL", "visual cue or unresolved low-confidence text evidence"
    elif table:
        route, reason = "TABLE", "tabular/numeric cue"
    elif not question.strip():
        route, reason = "UNKNOWN", "empty question"
    else:
        route, reason = "TEXT", "no visual cue and text evidence sufficient"
    return RoutingDecision(route=route, visual_invoked=route in {"VISUAL", "MIXED"}, reason=reason, score=1.0 if route != "UNKNOWN" else 0.0)
