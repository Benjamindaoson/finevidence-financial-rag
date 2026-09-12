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
