# Lightweight Evidence Graph

## ADDED Requirements

### Requirement: typed provenance graph
If enabled, the graph SHALL use typed in-memory nodes and provenance-bearing
edges for entity, metric, period, segment, basis, document, and evidence.

#### Scenario: no measured graph gap
- **WHEN** existing retrieval explains the cross-document cases
- **THEN** the graph implementation SHOULD remain unpromoted and the report
  SHALL state that the graph was not justified.
