## Why

The current P0-B/P0-C results are mechanism results on controlled fixtures. They cannot establish that fact coverage, targeted retrieval, or financial facets survive real financial language and table-text evidence. The next phase must measure external validity on public datasets without tuning the system to make the existing 0/1 results look better.

## What Changes

- Add a provenance-only acquisition contract for public TAT-QA and FinQA source repositories and raw split hashes; do not copy the full source corpora into the implementation Git repository.
- Add a deterministic builder that projects fixed TAT-QA and FinQA records into the existing Evidence IR while preserving source IDs, table/text provenance, gold supporting facts, programs, and execution answers.
- Add `RealFinance-v1` as a fixed, manifest-verified derived slice with separately reported TAT-QA and FinQA subsets.
- Add required-fact decomposition with an explicit gold-facts oracle mode and a deterministic predicted-facts baseline; report Required Fact Precision/Recall and oracle-versus-predicted completeness separately.
- Split P0-C reporting into facet extraction accuracy and facet-aware ranking under gold facets versus predicted facets.
- Add HSBC naturally-occurring hard-negative extraction only when a local, licensed HSBC source corpus is present; otherwise write an auditable `N/A` readiness record and do not synthesize HSBC stress results.
- Run Top-K, Coverage Gate, Targeted Retrieval, facet extraction, and ranking metrics on the fixed real-finance slice; keep controlled fixture results separate.

## Non-Goals

- Do not download FinRAGBench-V's full corpus.
- Do not enter B3 visual retrieval, GraphRAG, Agent loops, ACL, FastAPI, Kubernetes, or generation scoring in this change.
- Do not edit MiniBench-v1, FinanceHardSet-v1, or EvidenceCompleteness-v1.
- Do not manually rewrite public questions, answers, tables, or gold programs to improve scores.
