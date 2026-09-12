# Fact-evidence alignment

## ADDED Requirements

### Requirement: Record semantic support type
The alignment MUST record `DIRECT_SUPPORT`, `PARTIAL_SUPPORT`, `DERIVATION_INPUT`, `EXPLANATORY_SUPPORT`, `CONTEXT_ONLY`, or `NO_SUPPORT`, plus score, matched slots, mismatched slots, reuse flag, and reason.

#### Scenario: Numeric evidence cannot explain a cause
- **WHEN** a numeric table is aligned to an explanatory requirement without causal text
- **THEN** the alignment is not `EXPLANATORY_SUPPORT` and cannot satisfy that requirement

### Requirement: Preserve alternative evidence
An alignment MUST accept any valid evidence ID in the requirement's acceptable alternatives.

#### Scenario: Alternative evidence ID
- **WHEN** a requirement accepts E1 or E2 and E2 is selected and aligned
- **THEN** the requirement is eligible without requiring E1
