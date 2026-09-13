# P0-J — Final RAG Evaluation Closure

## Intent

Close the three remaining high-risk evaluation gaps without expanding the product architecture:

1. claim-level citation support;
2. human-verified financial table semantic correctness;
3. answerability and abstention quality.

Historical P0/B3/B4/B4.1 benchmarks and metrics remain frozen.

## Scientific boundary

This change provides reusable evaluation contracts, candidate annotation exports, and metric computation. Candidate annotations are not promoted to gold without real human verification. In the current automated run, human verification is unavailable, so final quality metrics remain N/A/BLOCKED.

## Acceptance criteria

- Citation, table semantic, and answerability metric functions have explicit contracts and unit tests.
- Candidate annotation artifacts point to existing real evidence and preserve provenance.
- Human verification metadata is explicit and cannot be inferred from model-generated labels.
- Final report separates verified observations, candidate-only artifacts, N/A metrics, and blockers.
- No historical benchmark or result is rewritten.

