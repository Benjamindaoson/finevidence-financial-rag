from __future__ import annotations

from finevidence.contracts.b5 import SearchAction, SearchBudget, SearchControllerState


class TypedSearchController:
    """Deterministic bounded action selector; it does not call tools itself."""

    def __init__(self, budget: SearchBudget | None = None) -> None:
        self.budget = budget or SearchBudget()

    def choose(self, state: SearchControllerState, *, requirement_id: str, query: str, failure_type: str | None = None) -> SearchAction | None:
        if len(state.retrieval_history) >= self.budget.max_steps or len(state.tool_history) >= self.budget.max_queries:
            return None
        if failure_type in {"TABLE_STRUCTURE_LOSS", "MULTI_LEVEL_HEADER", "UNIT_HEADER_LOSS"} and state.tool_history.count("table_query") < self.budget.max_table_calls:
            tool, reason = "table_query", "structured evidence is the capable recovery tool"
        elif failure_type in {"CHART_VISUAL_ONLY", "LAYOUT_DEPENDENCY"} and state.tool_history.count("visual_search") < self.budget.max_visual_calls:
            tool, reason = "visual_search", "visual/layout evidence is the capable recovery tool"
        elif failure_type == "CROSS_DOCUMENT_DEPENDENCY" and state.tool_history.count("graph_lookup") < self.budget.max_graph_calls:
            tool, reason = "graph_lookup", "cross-document relation needs graph lookup"
        else:
            tool, reason = "text_search", "bounded text retry for unresolved requirement"
        return SearchAction(step_id=len(state.retrieval_history) + 1, requirement_id=requirement_id, query=query, tool=tool, reason=reason, coverage_before=state.coverage_delta, coverage_after=state.coverage_delta, coverage_delta=0.0, latency_ms=0.0, cost=0.0, failure_type=failure_type)
