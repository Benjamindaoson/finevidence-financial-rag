# Evaluation closure

## ADDED Requirements

### Requirement: report closure metrics
The evaluator SHALL report T0, T1, V0, M0, and M1 page retrieval, recovery and regression at @1/@5/@10, separate routing results, and component P50/P95 latency.

#### Scenario: public archive unavailable
- **WHEN** the revision-pinned PDF archive cannot be downloaded
- **THEN** public page-image metrics are reported as blocked/N/A with the client traceback
