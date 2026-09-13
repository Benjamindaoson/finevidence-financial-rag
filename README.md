# FinEvidence — Evidence Backend v1 + Reproducible Experiments

Evidence-first, reproducible financial RAG experiments plus a thin local Evidence Backend v1. The backend exposes retrieval, evidence qualification, table lookup, verification, and citation without embedding an Agent loop or changing the historical experiment harness.

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

## Evidence Backend v1

Run the callable local API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn finevidence.api.app:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/health`. The default service loads ignored local
HSBC page evidence when those artifacts exist; otherwise it reports an honest
empty catalog. The versioned routes are documented in
[docs/FIN_EVIDENCE_API_SPEC.md](docs/FIN_EVIDENCE_API_SPEC.md), with the
Agent boundary in [docs/AI_RESEARCH_AGENT_INTEGRATION.md](docs/AI_RESEARCH_AGENT_INTEGRATION.md)
and the release boundary in [docs/FIN_EVIDENCE_V1_RELEASE.md](docs/FIN_EVIDENCE_V1_RELEASE.md).

The Docker package is local-only and intentionally excludes ignored PDFs and
model weights:

```powershell
docker compose up --build
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

The final clean-commit reproducibility pair is `artifacts/p0_h_runs/20260913T004424445930Z/` and `artifacts/p0_h_runs/20260913T005105288692Z/`. Both use commit `95885590e2b5d49fb61a8c448e4df4ae46142004`, the same local `SmolLM2-135M-Instruct` snapshot hash, and byte-identical formal artifacts. D1 is a real Transformers CPU attempt but remains `N/A / MALFORMED_LLM_JSON` for all 36 cases; no heuristic output is substituted.

On the 36-case slice, D4 reaches requirement precision/recall `0.7222/0.7222`, dependency accuracy `1.0000`, Independent CER `0.3704`, Critical Coverage `0.3750`, and eligible rate `0.1944`. D4 still has Raw Self Coverage `0.5185` versus Independent CER `0.3704`, with Invalid Reuse Rate `0.5000`. The adjudicated evidence coverage ceiling is only Independent CER `0.2593`, so the current lightweight alignment/retrieval stack still misses real evidence.

The HSBC corpus contains 372 Annual Report pages and 122 Pillar 3 pages, with SHA-256 and page counts in `artifacts/hsbc_local_sources/hsbc_corpus_manifest.json`; PDFs remain ignored and are not committed. Mining produced 59 valid natural cases from real page blocks. Dense and Hybrid+Generic HN Error are `0.3898`; predicted-facet, adjudicated-facet, and financial-aware deterministic ranking each reach `0.0339` HN Error, `0.9661` Recall@5, and `0.6441` Top-1 positive rate. Ranking Oracle Gap is `0.0000`.

The full report is `reports/p0-h-gold-requirement-hsbc-natural-hardcases.md`. P0-H marks B3 `READY` under the explicit gate, but does not implement visual retrieval. The non-human adjudication, limited facet vocabulary, page-only parser, and template overlap with D4 remain scientific limitations.

The final report is `reports/p0-g-evidence-requirement-graph.md`. This public slice result is not a leaderboard score, and the deterministic alignment is not a neural verifier.

## B3 multimodal evidence retrieval

B3 adds deterministic 72-DPI page rendering, image-backed Evidence IR, a real OpenAI CLIP RN50 image/text retrieval adapter, normalized RRF/weighted fusion, coverage-aware routing, page citation metrics, and reproducible latency/recovery traces. The executable track is `HSBCVisualStress-v1`, a 60-case project-created stress set mined from the official FY2025 Annual Report and Pillar 3 pages; it is not an HSBC-official benchmark and has `human_verified=false`.

```powershell
& .venv\Scripts\python.exe scripts\render_pdf_pages.py --dpi 72
& .venv\Scripts\python.exe scripts\build_hsbc_visual_stress.py --limit 60
& .venv\Scripts\python.exe -m finevidence.eval.b3 --config configs/b3_cpu.json
```

T1 is intentionally named `T1 Parsed Page Text`: it is not a verified structured-table IR. Cell identity, row/column relations, multi-level headers, unit edges, footnote edges, and table geometry remain `N/A`.

## B3.1 public benchmark and evaluation closure

B3.1 keeps `HSBCVisualStress-v1` unchanged and adds `HSBCMultimodalRouting-v1`, a balanced 30-case real-page routing workload with 10 `TEXT_SUFFICIENT`, 10 `TABLE_PARSED_SUFFICIENT`, and 10 `VISUAL_NEEDED` cases. Gold modality is evaluation-only; the router receives observed question/coverage signals.

Recovery is now reported at `@1`, `@5`, and `@10`. On the unchanged 60-case HSBC stress track, M1 recovery is `0.0167`, `0.0167`, and `0.0500`, with zero regression at all three cutoffs. On the 30-case routing track, visual invocation is `0.7667`, routing precision is `0.4348`, recall is `1.0000`, and unnecessary invocation is `0.6500`; this workload does not prove cost saving.

The official Hugging Face client was upgraded to `huggingface_hub==0.34.4` plus `hf_xet==1.6.0`, and the existing 100-query FinRAGBench-V slice was pinned to revision `d0d65255c94e687caa81ac9da7758ed25ff046a5`. The 2.38GB PDF archive still produced a zero-byte Xet/HTTP transfer under the local cache configuration; traceback and cache evidence are retained under `data/finragbench_v_source/`. Therefore public page-image metrics remain `N/A` and **B3 remains `PARTIAL`**. The final report is `reports/b3-1-public-benchmark-evaluation-closure.md`.

## B3.2 benchmark integrity and public closure

B3.2 did not rerun or rewrite B3.1. It froze a 20-case performance-blind audit sample for `HSBCVisualStress-v1` (two per category) and found a construction bias: all 60 cases use only ten fixed keyword templates and positive pages were selected by keyword occurrence. T0 page Recall is reproducibly `0/60` at @10 but `7/60` at @50, so the @10 result is real under the stress workload but is not an unbiased natural-text estimate. Per-case source/ranking evidence is retained in `artifacts/b3_2_runs/visualstress_audit/`.

The separate `HSBCNaturalMultimodal-v1` control contains 80 real HSBC pages selected by corpus hash before T0/V0 inspection, with stress candidate pages excluded. On its 80 cases, T0/T1/M1 Recall@10 are `0.5375/0.5875/0.5625`; V0 is `0.0750`. This control reverses the stress narrative and prevents a general “vision wins” claim. The exact B3.2 report is `reports/b3-2-benchmark-integrity-public-closure.md`.

B3.2 made a second official, revision-pinned FinRAGBench-V transfer attempt from WSL Ubuntu. Hugging Face returned the frozen commit and expected archive identity, but the 2.38GB transfer remained operationally blocked; the partial file is not used and public page-image metrics stay `N/A`. B3 therefore remains `PARTIAL`; B4 production hardening is not justified yet.

## B4 structure-preserving evidence IR and failure-aware escalation

B4 adds a real source-array `TableIR`/`TableCell` contract and compares evaluation-only E0 oracle routing with a performance-blind E1 predicted failure router on unchanged `HSBCVisualStress-v1`. The TAT-QA source-table slice preserves raw values, stable cell identity, and row/column relations at `1.0000`; HSBC's current page parser has no verified cell-level table IR, so structured HSBC recovery remains `N/A` rather than being represented by Parsed Page Text.

On the HSBC stress workload, E1 route accuracy is `0.5000`, visual invocation falls to `0.5000`, and predicted-router page recovery is `0.0167/0.0333/0.0833` at @1/@5/@10. The result supports failure-aware escalation as a direction, but not a solved router or a production cost claim. FinRAGBench-V remains a separate public blocker: its frozen `corpus/en` tree exposes multi-gigabyte compressed shards rather than individually retrievable pages. The formal report is `reports/b4-structure-preserving-evidence-ir-failure-aware-escalation.md`; formal runs are under `artifacts/b4_runs/`. B4 is complete for this experimental scope; B3 remains `PARTIAL`.
# B4.1 — real financial table recovery

B4.1 adds a bounded geometry-assisted PDF-to-TableIR extractor over the existing public HSBC FY2025 Annual Report artifact and a deterministic cell-level `StructuredTableRetriever`. T2 preserves table/row/column/bbox provenance and is evaluated through the existing Evidence Qualification and Independent Coverage gates; it is not a renamed page-text retriever and it is not a neural reranker.

The formal report is [reports/b4-1-real-financial-table-recovery.md](reports/b4-1-real-financial-table-recovery.md). On the frozen 60-case HSBC stress workload, T2 reached Page Recall@1/5/10 of `0.0167/0.0833/0.0833` and recovered 5 table-category page misses by @10 relative to T1. Semantic cell accuracy, unit accuracy, and merged-cell accuracy remain `N/A` without verified human TableIR gold. B3's FinRAGBench-V external blocker remains unchanged.

# P0-J — final RAG evaluation contracts

P0-J adds executable, provenance-aware evaluators for claim-level citation
support, financial table semantics and answerability/abstention. The first run
created candidate-only queues from frozen evidence (50 claim cases, 24 HSBC
TableIR regions and a 20/20/20 answerability candidate queue). Because no repository row is
`human_verified=true`, formal P0-J quality metrics remain `N/A`; the candidates
are not human gold. See [docs/FIN_EVIDENCE_FINAL_RAG_EVALUATION.md](docs/FIN_EVIDENCE_FINAL_RAG_EVALUATION.md),
[docs/FINAL_RESUME_METRICS.md](docs/FINAL_RESUME_METRICS.md) and
`artifacts/final_rag_eval/`.
