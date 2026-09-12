# P0-D Real-Finance Validation Report

## Material Passport

- ID: `P0-D-20260913`
- Type: code experiment / external-validity validation
- Status: `VERIFIED` for the fixed public-source-derived slice; HSBC stress set `N/A`
- Code commit: recorded in the final run's `config.json`
- Primary command: `python -m finevidence.eval.p0_d --config configs/p0_d_cpu.json`
- Source data: local TAT-QA and FinQA clones, pinned by repository commit and raw-file SHA-256

## Research question

Do the P0-B evidence-completeness and P0-C financial-ranking mechanisms survive public real-finance data, or were the earlier results only consequences of controlled fixture construction?

## Source provenance

The source repositories were cloned read-only under `D:\01_work\Enterprise Multimodal RAG\research\repos`.

| Source | Repository commit | Split used | Raw SHA-256 |
|---|---|---|---|
| TAT-QA | `870accc41953dcde885aabeb963d94aabdc0fbc3` | `dataset_raw/tatqa_dataset_dev.json` | `6c3660345bf155b44bb3b55e63a4355716521028f291263d47c66667335f0144` |
| FinQA | `0f16e2867befa6840783e58be38c9efb9229d742` | `dataset/dev.json` | `27cc6c57487bbaba73041f93dba831a39b1cabe999c2ec0ddebc6f1200ff85bd` |

TAT-QA's [official repository](https://github.com/NExTplusplus/tat-qa) describes 16,552 questions associated with 2,757 hybrid table/text contexts and publishes the dataset under CC BY 4.0. FinQA's [official repository](https://github.com/czyssrs/FinQA) defines `gold_inds`, `program`, and `exe_ans` in each annotated record and documents a historical row-formatting label-leakage bug that inflated retrieval results before correction. The full FinRAGBench-V corpus remains outside this phase; its [dataset card](https://huggingface.co/datasets/zhaosuifeng/FinRAGBench-V) lists a 202 GB dataset with separate queries, qrels, corpus, PDFs, and citation labels.

## Derived benchmark

`RealFinance-v1` contains exactly 100 answerable cases:

- 50 TAT-QA `table-text` cases selected in deterministic dev order.
- 50 answerable FinQA dev cases selected in deterministic order.
- 1,652 projected Evidence IR items.
- TAT-QA table evidence preserves the complete table serialization and related paragraph evidence.
- FinQA projects table rows and pre/post sentences and retains exact `gold_inds`, `program`, and `exe_ans` as evaluation-only provenance.

Derived hashes are recorded in `benchmarks/real_finance_v1/manifest.json`. The raw public corpora are not copied into this repository.

## Observed results

| System | Recall@5 | MRR | nDCG@10 | Complete Evidence |
|---|---:|---:|---:|---:|
| Dense | 0.0900 | 0.1027 | 0.0773 | 0.0300 |
| Hybrid + Generic | 0.1417 | 0.1895 | 0.1405 | 0.0500 |
| Facet-aware / predicted facets | 0.1417 | 0.1912 | 0.1398 | 0.0500 |
| Facet-aware / gold facets | N/A | N/A | N/A | N/A |

| Fact condition | Initial CER | Final CER | Partial→Complete Recovery |
|---|---:|---:|---:|
| Gold required facts, targeted retrieval | 0.0300 | 0.8900 | 0.8866 |
| Predicted required facts, lexical self-coverage | 0.9200 | 0.9900 | 0.8750 |

Required Fact Precision was `0.0100` and Required Fact Recall was `0.0017` for the deterministic decomposer. The predicted-fact coverage row is therefore not a claim that the decomposer recovered the gold facts; it measures whether the evidence selected appears to satisfy the decomposer's own under-specified fact set. Gold-fact recall is the controlling safety signal.

The run produced 100 query traces and 61 failures before the TAT-QA fact-description projection was corrected. After using source evidence text as the TAT-QA fact description, the final run produced 100 traces and 11 incomplete gold-fact cases. The remaining failures are retained in `failure_cases.jsonl`.

## HSBC stress readiness

`hsbc_readiness.json` is `N/A` with reason `LOCAL_PROVENANCE_SOURCE_MISSING`. No naturally-occurring HSBC hard-negative score is reported. Creating one requires a licensed local HSBC source corpus and a reproducible candidate extraction rule; controlled FinanceHardSet-v1 is not substituted.

## Verification and boundaries

- This report covers a fixed public-source-derived dev slice, not a leaderboard submission.
- No generation accuracy, executable-program accuracy, citation bbox accuracy, or visual retrieval result is claimed.
- No FinRAGBench-V full corpus was downloaded.
- Results are descriptive observations from the pinned slice; the next gate is a larger/held-out source split and then a licensed HSBC stress set.
