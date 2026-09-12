## Context

TAT-QA is a public table-text financial QA dataset. Its raw records contain report-level paragraphs, a table, and question annotations including `answer_from`, `rel_paragraphs`, answer, derivation, and scale. FinQA records contain report text, tables, `qa.gold_inds`, `qa.program`, and `qa.exe_ans`. These source annotations are sufficient to create evidence retrieval and fact-completeness tasks without inventing answers.

## Goals / Non-Goals

**Goals:**

- Reproduce a fixed 100-record real-finance slice from local, hash-verified source files: 50 TAT-QA table-text cases and 50 FinQA cases.
- Preserve source provenance and distinguish `gold_facts` from `predicted_facts`.
- Measure the existing retrieval stack on source-derived Evidence IR, not only on hand-written fixture text.
- Make facet extraction a separately measurable upstream task.
- Make HSBC stress-set readiness an explicit gate rather than a synthetic fallback.

**Non-Goals:**

- This phase does not claim public benchmark leaderboard performance.
- This phase does not implement an LLM decomposer or neural facet extractor.
- This phase does not expose private or unlicensed HSBC material.

## Decisions

### 1. Source acquisition and provenance

The source repositories are cloned outside the implementation package under `research/repos/`. The builder records repository URL, source commit, source relative path, byte size, and SHA-256 in the derived manifest. Raw public data is treated as immutable input; generated slice files are checked in only if compact and sufficient for reruns.

### 2. TAT-QA projection

Each report table becomes one structure-preserving `table` Evidence item whose text is a deterministic row/column serialization. Each paragraph becomes a `text` Evidence item. For a question, table support is represented by the table evidence when `answer_from` includes `table`; paragraph support is represented by the `rel_paragraphs` evidence IDs. A fact requirement is created per required evidence unit, retaining source annotation in the case metadata.

### 3. FinQA projection

Each table row becomes a `table` Evidence item, and each pre/post text sentence becomes a `text` Evidence item. `qa.gold_inds` is mapped to those evidence IDs using the source's table/text keys and retained verbatim in case provenance. The program and `exe_ans` are retained as evaluation-only fields and never passed to retrieval.

### 4. Predicted fact baseline

The predicted decomposer is intentionally deterministic and transparent: it emits one fact for each explicit evidence-bearing cue detected in the question and one fallback question fact when no cue is detected. Gold facts remain an oracle upper-bound condition. Required Fact Recall is reported separately, with omitted facts treated as failures.

### 5. Facet evaluation

Facet extraction returns a `FinancialFacets` record plus extraction confidence/coverage. Exact-match facet accuracy is evaluated against source-derived labels where available and is `N/A` for fields not annotated. Ranking is run in two conditions: gold facets and predicted facets. No ranking result may be attributed to facet-aware ranking without reporting the upstream facet condition.

### 6. HSBC stress gate

The builder searches only for a user-provided/local HSBC source corpus with provenance metadata. If no source is available, `HSBC-Stress-v1` remains `N/A`; no hand-authored candidates are accepted as naturally occurring hard negatives.

## Risks / Trade-offs

- Source-specific annotation formats require adapters → keep source parsing isolated and preserve raw keys.
- TAT-QA table rows do not always expose a canonical row annotation → use structure-preserving table evidence and mark row-level precision as unavailable rather than guessing.
- FinQA's gold supporting facts are flattened strings → retain exact strings and map by normalized content with an explicit unmatched list.
- A 100-record slice is not a leaderboard benchmark → call it `RealFinance-v1` fixed validation slice and report source/split/counts.
- Deterministic decomposition has a low ceiling → its purpose is to expose the gap between oracle facts and predicted facts, not to simulate an LLM.
