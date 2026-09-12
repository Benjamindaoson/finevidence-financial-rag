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
