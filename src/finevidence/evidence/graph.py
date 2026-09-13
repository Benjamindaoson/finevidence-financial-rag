from __future__ import annotations

from finevidence.contracts.b5 import GraphEdge, GraphNode


class EvidenceGraph:
    """Small typed in-memory graph for measured cross-document lookups."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise KeyError("graph edge endpoint is not registered")
        self.edges.append(edge)

    def neighbors(self, node_id: str, relation: str | None = None) -> list[GraphNode]:
        target_ids = [edge.target_id for edge in self.edges if edge.source_id == node_id and (relation is None or edge.relation == relation)]
        return [self.nodes[target_id] for target_id in target_ids]
