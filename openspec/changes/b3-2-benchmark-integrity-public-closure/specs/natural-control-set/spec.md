# Natural control set

## ADDED Requirements

### Requirement: Corpus-only selection
The natural control set MUST contain 60–100 real HSBC cases selected before T0/V0 results are available and MUST be reported separately from VisualStress.

#### Scenario: Frozen control selection
- **WHEN** eligible corpus pages are selected
- **THEN** selection is determined by corpus identity/hash ordering and excludes stress candidate pages without inspecting performance.
