# Visual evidence IR

## ADDED Requirements

### Requirement: retain visual provenance
Visual evidence SHALL retain page image identity, render hash, image path, and optional region geometry.

#### Scenario: page-level evidence
- **WHEN** a page has no verified region gold
- **THEN** the evidence retains page identity and leaves region geometry null
