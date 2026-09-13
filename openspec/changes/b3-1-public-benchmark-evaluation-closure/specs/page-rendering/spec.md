# Page rendering

## ADDED Requirements

### Requirement: preserve render provenance
The evaluator SHALL preserve source PDF hashes, render hashes, page dimensions, DPI, and render version.

#### Scenario: rerendering the same page
- **WHEN** the same source page is rendered with the frozen DPI
- **THEN** the image hash and manifest identity remain stable
