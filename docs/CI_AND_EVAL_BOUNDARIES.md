# CI and evaluation boundaries

FinEvidence separates **code regression** from **historical / extended
experiment reproduction**. This is intentional: a green CI run must not be
obtained by rewriting frozen benchmark hashes or silently fabricating external
assets.

## Core regression gate

The default GitHub Actions job installs only the repository's reproducible CPU
dependencies and runs all unit, API, contract, retrieval, ranking, evidence and
evaluation tests that can be reproduced from the repository checkout.

At the time of the v0.2 consolidation, this means **93 tests pass** in the
repository-only environment before the five asset-bound historical tests below
are excluded from the merge gate.

## Extended tests not used as the merge gate

The following tests are retained but are not part of the default core CI gate:

1. `tests/test_b3_2.py::test_visualstress_audit_selection_is_fixed_and_performance_blind`
   - the stored audit-selection source hash does not match the current
     `questions.jsonl`;
   - the historical hash is not rewritten automatically because doing so would
     alter frozen benchmark provenance.

2. `tests/test_p0_d_runner.py::test_p0_d_runner_emits_public_tables_and_hsbc_readiness_gate`
   - requires the pinned external TAT-QA raw dataset checkout, which is not
     committed to this repository.

3. `tests/test_p0_e_runner.py::test_p0_e_runner_emits_variant_metrics_and_oracle_gap`
4. `tests/test_p0_g_runner.py::test_p0_g_runner_emits_graph_alignment_and_coverage_artifacts`
5. `tests/test_p0_h_runner.py::test_p0_h_runner_emits_required_artifacts`
   - these validate a frozen RealFinance benchmark whose checked-in
     `evidence.jsonl` currently does not match the recorded manifest hash.

## Policy

- Do not update a frozen manifest merely to make CI green.
- Do not replace missing TAT-QA / FinQA source files with synthetic data.
- Historical results remain tied to the commit, manifest and asset set that
  produced them.
- Before publishing new v0.2 retrieval/reranking numbers, reconstruct the
  benchmark from the pinned upstream sources, generate a new versioned
  manifest, and run the evaluation from that new immutable slice.

This separation makes failures diagnosable: core code regressions block merges;
external-data or frozen-artifact reproduction gaps remain visible without being
misrepresented as code failures.
