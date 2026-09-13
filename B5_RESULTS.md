# B5 Results

## Scope

This is the first B5 increment. It runs B5.1 against the immutable
`RealFinance-v1` manifest: 100 questions, 1,652 evidence records, 50 TAT-QA
and 50 FinQA. It does not rewrite P0-D or any later historical artifact.

## B5.1 retrieval result

| System | R@1 | R@5 | R@10 | MRR | nDCG@10 | Complete Evidence |
|---|---:|---:|---:|---:|---:|---:|
| R1 Current Dense (`tfidf_svd_dense`) | 0.0400 | 0.0900 | 0.1117 | 0.1070 | 0.0863 | 0.0400 |
| R2 Current Hybrid | 0.0950 | 0.1417 | 0.1900 | 0.1969 | 0.1593 | 0.1000 |
| R3 Qwen3 Dense | N/A | N/A | N/A | N/A | N/A | N/A |
| R4 Hybrid + Qwen3 Dense | N/A | N/A | N/A | N/A | N/A | N/A |

`R0 BM25` is `N/A`: the repository has a lexical component inside
`HybridRetriever`, but no separately implemented BM25 backend. It is not
renamed to hide that distinction.

## Model status

The cached Qwen snapshot had tokenizer/config files but no model weights. A
revision-pinned `hf_hub_download` attempt for `model.safetensors` displayed an
expected size of about 1.19 GB and remained at 0 bytes after a bounded 118
second interval while entering `hf_xet`; it was interrupted. The subsequent
local-only load therefore failed and B5.1 neural rows remain `N/A`. Evidence
is recorded in `data/b5_model_attempts.json` and the run's `model_manifest.json`.

## Status

`B5.1 = PARTIAL / MODEL_WEIGHTS_BLOCKED`.

No claim is made that Qwen improves financial hard negatives, because no Qwen
inference was executed.
