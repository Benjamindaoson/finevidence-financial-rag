from __future__ import annotations

from finevidence.contracts.b5 import GraphEdge, GraphNode, SearchBudget, SearchControllerState
from finevidence.evidence.graph import EvidenceGraph
from finevidence.retrieval.controller import TypedSearchController
from finevidence.retrieval.neural import QwenEmbeddingRetriever


def test_unavailable_neural_adapter_is_not_a_heuristic_fallback():
    adapter = QwenEmbeddingRetriever(model_id="missing/model", local_files_only=True)
    assert adapter.available is False
    assert adapter.search("query", 5) == []
    assert adapter.manifest().status == "N/A"


def test_controller_selects_bounded_typed_tool():
    state = SearchControllerState(question="find table value", missing_requirements=["r1"], failure_type="TABLE_STRUCTURE_LOSS")
    action = TypedSearchController(SearchBudget(max_table_calls=1)).choose(state, requirement_id="r1", query="find table value", failure_type="TABLE_STRUCTURE_LOSS")
    assert action is not None
    assert action.tool == "table_query"


def test_controller_stops_at_step_budget():
    state = SearchControllerState(question="q", retrieval_history=[{"step_id": 1, "query": "q", "tool": "text_search", "reason": "r", "coverage_before": 0.0, "coverage_after": 0.0, "coverage_delta": 0.0, "latency_ms": 0.0, "cost": 0.0}], tool_history=["text_search"])
    assert TypedSearchController(SearchBudget(max_steps=1)).choose(state, requirement_id="r1", query="q") is None


def test_evidence_graph_requires_registered_endpoints():
    graph = EvidenceGraph()
    graph.add_node(GraphNode(node_id="e", node_type="Entity", label="HSBC"))
    graph.add_node(GraphNode(node_id="m", node_type="Metric", label="CET1 ratio"))
    graph.add_edge(GraphEdge(source_id="e", target_id="m", relation="ENTITY_HAS_METRIC"))
    assert [node.node_id for node in graph.neighbors("e")] == ["m"]
