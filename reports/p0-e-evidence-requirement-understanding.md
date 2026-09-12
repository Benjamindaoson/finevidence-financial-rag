# P0-E Evidence Requirement Understanding Report

## Material passport

- ID: `P0-E-20260913`
- Type: code experiment / evidence-requirement validation
- Status: `VERIFIED` for the fixed RealFinance-v1 public slice; D1 and structured slot metrics are `N/A` by design
- Code commit: `ea7876b4caad8aca9dee22fbb106a60a55bb14e7`
- Primary command: `python -m finevidence.eval.p0_e --config configs/p0_e_cpu.json`
- Final reproducibility runs: `artifacts/p0_e_runs/20260912T205940827353Z-bc0c3c06/` and `artifacts/p0_e_runs/20260912T210052094393Z-edbc1aa9/`

## Research question

Can a financial RAG system identify the facts required by a question and keep the resulting fact-to-evidence mapping bounded, observable, and measurable?

## Variants

- D0 Heuristic: the frozen deterministic splitter from P0-D.
- D1 LLM Direct: provider boundary only; no authorized provider was configured, so the result is explicitly `N/A`.
- D2 Schema-constrained: fixed question-type templates with financial slots.
- D3 Evidence-aware: D2 facts are retained only with IDs from the bounded candidate evidence list; unresolved facts keep `__unresolved__`.

## Dataset

The runner uses the fixed `RealFinance-v1` slice: 50 TAT-QA table-text cases and 50 answerable FinQA cases. Public source commits, raw hashes, and derived hashes remain in `benchmarks/real_finance_v1/manifest.json`; no controlled fixture rows are merged into this result.

## Required fact understanding

| Method | Fact Precision | Fact Recall | Critical Fact Recall | Slot Accuracy |
|---|---:|---:|---:|---:|
| D0 Heuristic | 0.0100 | 0.0017 | N/A | N/A |
| D1 LLM Direct | N/A | N/A | N/A | N/A |
| D2 Schema-constrained | 0.0033 | 0.0033 | N/A | N/A |
| D3 Evidence-aware | 0.0033 | 0.0033 | N/A | N/A |

The public slice has free-text supporting evidence but no canonical structured gold labels for entity, metric, period, segment, basis, role, or criticality. Therefore critical-fact recall and slot accuracy are `N/A`; the lexical fact scores are diagnostics, not semantic ground truth.

## Evidence completion and Oracle Gap

| Facts / method | Initial CER | Final CER | Recovery | FAER | Oracle Gap |
|---|---:|---:|---:|---:|---:|
| Gold required facts | 0.0500 | 0.8900 | 0.8842 | 0.0000 | — |
| D0 Heuristic | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.8900 |
| D1 LLM Direct | N/A | N/A | N/A | N/A | N/A |
| D2 Schema-constrained | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.8900 |
| D3 Evidence-aware | 1.0000 | 1.0000 | N/A | 0.0000 | -0.1100 |

Oracle Gap is `gold_final_cer - predicted_final_cer`. D3's negative gap is deliberately retained as a calibration warning: the simple evidence-aware adapter reused one candidate evidence item across multiple template facts, so its predicted fact set is under-specified. It is not evidence that D3 is better than the gold condition.

The two layers are now separated: P0-D's gold-fact targeted retrieval reaches `0.89` final CER, while P0-E shows that a decomposer can still fail to define or map the required facts correctly. This is the current understanding/evidence-mapping bottleneck.

## HSBC provenance track

`data/hsbc_public_sources.json` records two official FY2025 HSBC sources: Annual Report and Pillar 3 Disclosures. `scripts/fetch_hsbc_public_sources.py` validates URLs by default and downloads only with explicit `--download` into ignored local storage. No HSBC PDF or extracted content is committed, and no naturally-occurring hard-negative score is claimed in this report.

## Verification and boundaries

- Two final runs recorded identical metrics and dataset manifest content.
- Each final run contains 400 traces: 100 cases across four variants.
- Each final run contains 200 retained failure traces from D0/D2 unresolved mappings; D1 is `N/A` and is not counted as a failure.
- Full FinRAGBench-V was not downloaded.
- No generation, visual retrieval, citation bbox, ACL, Agent, GraphRAG, FastAPI, or Kubernetes result is claimed.
- B3 remains blocked until fact decomposition/mapping is improved on a held-out real split and P0-F obtains a licensed local source corpus.
