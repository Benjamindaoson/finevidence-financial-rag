# Requirement graph

## ADDED Requirements

### Requirement: Validate the graph as a DAG
The graph MUST reject duplicate nodes, unknown edge endpoints, self-edges, and cycles.

#### Scenario: Cyclic dependency
- **WHEN** F1 depends on F2 and F2 depends on F1
- **THEN** graph validation fails before retrieval or coverage evaluation

### Requirement: Support typed dependency edges
The graph MUST preserve `DEPENDS_ON`, `DERIVED_FROM`, `EXPLAINS`, and `COMPARED_WITH` edges in trace artifacts.

#### Scenario: Explanation graph
- **WHEN** an observed change is explained by a management commentary requirement
- **THEN** the graph stores an `EXPLAINS` edge and the explanation remains distinct from numeric evidence
