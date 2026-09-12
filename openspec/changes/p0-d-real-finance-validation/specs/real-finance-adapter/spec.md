## ADDED Requirements

### Requirement: Source-derived Evidence IR preserves provenance
The builder SHALL convert selected TAT-QA and FinQA records into Evidence IR without changing source question text, answer annotations, table values, or gold supporting fact strings.

#### Scenario: TAT-QA table-text record is projected
- **WHEN** a TAT-QA record contains a table, paragraphs, and a question with `answer_from` equal to `table-text`
- **THEN** the derived case SHALL reference both a structure-preserving table Evidence item and the annotated related paragraph Evidence items
- **AND** the case SHALL retain the TAT-QA report/question identifiers and answer metadata

#### Scenario: FinQA supporting facts are projected
- **WHEN** a FinQA record contains `qa.gold_inds`, `qa.program`, and `qa.exe_ans`
- **THEN** the derived case SHALL retain those fields as evaluation-only provenance
- **AND** the corresponding table/text Evidence IDs SHALL be recorded or listed as unmatched when an exact mapping is impossible

### Requirement: Derived slice is fixed and hash verified
The builder SHALL create a manifest containing source repository commits, source file hashes, selection rule, selected IDs, derived file hashes, and counts.

#### Scenario: Source changes are detected
- **WHEN** a source file hash or repository commit differs from the manifest
- **THEN** validation SHALL fail before the slice is evaluated
