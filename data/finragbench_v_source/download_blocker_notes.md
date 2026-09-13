# FinRAGBench-V PDF archive blocker evidence

- Dataset: `zhaosuifeng/FinRAGBench-V`
- Pinned revision: `d0d65255c94e687caa81ac9da7758ed25ff046a5`
- File: `pdfs_for_QA/pdf_en.tar.gz`
- Expected size: approximately 2.38 GB
- Client: `huggingface_hub==0.34.4`, `hf_xet==1.6.0`

## Attempt 1

`hf_hub_download(..., revision=d0d65255c94e687caa81ac9da7758ed25ff046a5, cache_dir=artifacts/hf_cache, local_dir=artifacts/finragbench_v_source/downloads)` reached the Xet downloader but failed because the host's inherited Xet log directory `E:\AIResearch\hf-cache\xet\logs` did not exist. The complete Python traceback is in `download_blocker.json`.

## Attempt 2

After setting `HF_HOME`, `HF_HUB_CACHE`, and `HF_XET_CACHE` to project-local directories, the same official `hf_hub_download` call entered Xet transfer but remained at a zero-byte incomplete object for more than three minutes with no progress or response. The process was stopped to avoid an unbounded wait; the incomplete cache object and lock were retained. A short official HTTP fallback with `HF_HUB_DISABLE_XET=1` also remained at zero bytes for more than 90 seconds and was stopped. No PDF was extracted or used.

This is an operational network/Xet transport blocker, not a successful download. Therefore FinRAGBench-V page-image metrics remain `N/A` and B3.1 remains `PARTIAL` unless the archive becomes available.
