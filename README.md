# FinEvidence P0

Evidence-first, reproducible financial RAG experiments. This is the first P0 implementation slice, not a production API.

## Run

```powershell
cd "D:\01_work\Enterprise Multimodal RAG\finevidence"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m finevidence.eval.run --config configs/mini_cpu.json
```

The runner verifies `benchmarks/mini_finance/manifest.json` and writes a new directory under `artifacts/runs/` containing:

```text
config.json
dataset_manifest.json
predictions.jsonl
metrics.json
failure_cases.jsonl
```

## Interpretation boundary

The checked-in 30-question MiniBench is a development and regression fixture. It is not a FinRAGBench-V or ICBCBench score. B0 uses the explicitly named CPU `tfidf_svd_dense` adapter; it is not a neural embedding result. B3 reports `N/A` until a visual encoder and visual corpus are actually configured. No improvement percentage is written unless the same manifest has been run through comparable baselines.

## P0-B/P0-C experiment sprint

The bounded sprint keeps `MiniBench-v1` unchanged and adds two separate development suites:

- `EvidenceCompleteness-v1`: 30 multi-fact cases with acceptable evidence alternatives. It compares Top-K eligibility, a fact-completeness gate, and deterministic targeted retrieval capped at two rounds.
- `FinanceHardSet-v1`: exactly 100 controlled hard-negative cases across temporal, metric, related-metric, entity, segment, basis, currency, geography, period-type, and table-context confusions.

The sprint writes `ranking_table.json`, `sufficiency_table.json`, `per_query_trace.jsonl`, `predictions.jsonl`, `metrics.json`, `failure_cases.jsonl`, `config.json`, and `dataset_manifest.json` under `artifacts/p0_bc_runs/`. The facet and hard-negative rankers are deterministic development adapters, not claims of neural reranker quality. No B3 visual retrieval, generation, Agent loop, ACL, GraphRAG, FastAPI, or K8s is invoked.

## P0-D real-finance validation

P0-D uses the locally cloned public source repositories `NExTplusplus/tat-qa` and `czyssrs/FinQA`, records their commits and raw-file SHA-256 values in `data/source_manifests/public_finance_sources.json`, and deterministically builds `RealFinance-v1` from 50 TAT-QA table-text questions and 50 answerable FinQA development records. The derived manifest preserves source IDs, tables/paragraphs, `gold_inds`, programs, execution answers, and source provenance.

Run the source audit and fixed slice builder:

```powershell
.\.venv\Scripts\python.exe scripts/audit_public_finance_sources.py
.\.venv\Scripts\python.exe scripts/build_real_finance.py --output benchmarks/real_finance_v1
.\.venv\Scripts\python.exe -m finevidence.eval.p0_d --config configs/p0_d_cpu.json
```

P0-D reports oracle gold-fact coverage separately from the deterministic predicted-fact baseline, and reports facet-aware ranking under predicted facets separately from the gold-facet condition. The gold-facet condition and facet extraction accuracy are `N/A` because TAT-QA and FinQA do not provide canonical entity/metric/period facet labels. `hsbc_readiness.json` remains `N/A` until a licensed, provenance-bearing local HSBC corpus is supplied. The full FinRAGBench-V corpus is not downloaded.

## P0-E evidence requirement understanding

P0-E evaluates the next bottleneck exposed by P0-D: whether the system knows which facts are required before it asks retrieval to find them. It compares D0 Heuristic, D1 LLM Direct, D2 Schema-constrained, and D3 Evidence-aware decomposition. D1 is explicitly `N/A` without an authorized provider; slot and critical-fact metrics are `N/A` when the source has no canonical structured labels.

```powershell
.\.venv\Scripts\python.exe -m finevidence.eval.p0_e --config configs/p0_e_cpu.json
```

The runner writes `metrics.json`, `dataset_manifest.json`, `per_query_trace.jsonl`, and `failure_cases.jsonl` under `artifacts/p0_e_runs/`. It reports fact precision/recall, critical recall, slot accuracy, Initial/Final CER, Recovery, FAER, and Oracle Gap. A negative Oracle Gap is retained as a calibration warning, not a gain claim.

## P0-F HSBC provenance track

The repository contains only official HSBC source URLs and metadata in `data/hsbc_public_sources.json`. Validate without downloading:

```powershell
.\.venv\Scripts\python.exe scripts/fetch_hsbc_public_sources.py
```

Use `--download` only when local HSBC analysis is authorized; downloaded files go to ignored `artifacts/hsbc_local_sources/` and are never committed.

## P0-G evidence requirement graph

P0-G addresses the P0-E false-completeness failure. It adds typed evidence requirements, a Pydantic DAG for retrieved/derived/explanatory/context facts, explicit fact–evidence alignment, conservative independent evidence reuse, and a critical requirement gate. A derived fact is satisfied through independently covered dependencies; it does not need a chunk that literally states the derived result.

Run the frozen RealFinance-v1 public slice:

```powershell
.\.venv\Scripts\python.exe -m finevidence.eval.p0_g --config configs/p0_g_cpu.json
```

The runner writes `config.json`, `dataset_manifest.json`, `predictions.jsonl`, `metrics.json`, `requirement_graphs.jsonl`, `alignment_results.jsonl`, `per_query_trace.jsonl`, and `failure_cases.jsonl` under ignored `artifacts/p0_g_runs/`. P0-G reports Raw Self Coverage, Independent CER, Critical Coverage, Evidence Reuse Rate, Invalid Reuse Rate, FAER and Gold-vs-Predicted gaps. D1 is `N/A` without a local LLM provider. `RequirementGold-v1` is currently `N/A` with zero manually annotated cases; no inferred labels are promoted to gold.

## P0-H gold requirement validation and HSBC natural hard cases

P0-H tests whether the system can separate “relevant evidence was retrieved” from “every critical evidence requirement is satisfied”. It adds a bounded `RequirementAdjudicated-v1` subset of 36 frozen `RealFinance-v1` cases (10 factual, 4 comparison, 18 numerical, 3 trend, 1 explanation), one-to-one requirement matching, real local D1 inference, and a `HSBCNaturalHard-v1` stress set mined only from parsed blocks in the official FY2025 Annual Report and Pillar 3 PDFs. These are model-assisted adjudicated artifacts, not human/expert gold or HSBC-official benchmarks: both record `human_verified=false`.

Run it with:

```powershell
.\.venv\Scripts\python.exe -m finevidence.eval.p0_h --config configs/p0_h_cpu.json
```

The final clean-commit reproducibility pair is `artifacts/p0_h_runs/20260913T004424445930Z/` and `artifacts/p0_h_runs/20260913T005105288692Z/`. Both use commit `9588559d6c2c8d72f8fdc3156d3a3372153dbcc6`, the same local `SmolLM2-135M-Instruct` snapshot hash, and byte-identical formal artifacts. D1 is a real Transformers CPU attempt but remains `N/A / MALFORMED_LLM_JSON` for all 36 cases; no heuristic output is substituted.

On the 36-case slice, D4 reaches requirement precision/recall `0.7222/0.7222`, dependency accuracy `1.0000`, Independent CER `0.3704`, Critical Coverage `0.3750`, and eligible rate `0.1944`. D4 still has Raw Self Coverage `0.5185` versus Independent CER `0.3704`, with Invalid Reuse Rate `0.5000`. The adjudicated evidence coverage ceiling is only Independent CER `0.2593`, so the current lightweight alignment/retrieval stack still misses real evidence.

The HSBC corpus contains 372 Annual Report pages and 122 Pillar 3 pages, with SHA-256 and page counts in `artifacts/hsbc_local_sources/hsbc_corpus_manifest.json`; PDFs remain ignored and are not committed. Mining produced 59 valid natural cases from real page blocks. Dense and Hybrid+Generic HN Error are `0.3898`; predicted-facet, adjudicated-facet, and financial-aware deterministic ranking each reach `0.0339` HN Error, `0.9661` Recall@5, and `0.6441` Top-1 positive rate. Ranking Oracle Gap is `0.0000`.

The full report is `reports/p0-h-gold-requirement-hsbc-natural-hardcases.md`. P0-H marks B3 `READY` under the explicit gate, but does not implement visual retrieval. The non-human adjudication, limited facet vocabulary, page-only parser, and template overlap with D4 remain scientific limitations.

The final report is `reports/p0-g-evidence-requirement-graph.md`. This public slice result is not a leaderboard score, and the deterministic alignment is not a neural verifier.
