## 1. Project and contracts

- [ ] 1.1 Add the Python package layout, pinned minimal dependencies, and pytest configuration.
- [ ] 1.2 Add the frozen Evidence IR with content-hash validation and round-trip tests.
- [ ] 1.3 Add typed MiniCase, RequiredEvidenceRef, RetrievedEvidence, and run-result models with validation tests.

## 2. MiniBench

- [ ] 2.1 Add a checked-in financial fixture with text, table, visual-caption, hard-negative, multi-evidence, and unanswerable cases.
- [ ] 2.2 Implement JSONL loading and manifest hash/count verification.
- [ ] 2.3 Test unchanged, changed, invalid, and unanswerable benchmark inputs.

## 3. Retrieval baselines

- [ ] 3.1 Implement deterministic CPU `tfidf_svd_dense` retrieval with traceable and stable top-k results.
- [ ] 3.2 Implement B1 dense-plus-lexical fusion and generic reranking without changing Evidence identity.
- [ ] 3.3 Implement the conditional visual adapter with explicit `N/A` output when visual inputs or encoder are unavailable.
- [ ] 3.4 Test B0/B1 ordering, traceability, score recording, and B3 unavailability behavior.

## 4. Evidence evaluation

- [ ] 4.1 Implement evidence-set coverage and answer-eligibility decisions for B2.
- [ ] 4.2 Implement Recall@K, MRR, nDCG, complete evidence rate, unsupported answer rate, and missing-fact detection.
- [ ] 4.3 Implement Hard-Negative Error Rate with temporal, metric, and entity negative cases.
- [ ] 4.4 Test partial/full coverage, ranking errors, and `N/A` for missing annotations.

## 5. Reproducible runner

- [ ] 5.1 Implement the CLI that runs B0/B1/B2/B3 against the same verified MiniBench.
- [ ] 5.2 Save config, dataset manifest, predictions, metrics, and failure cases under a unique non-overwriting run directory.
- [ ] 5.3 Add the CPU config and README with exact run commands and interpretation boundaries.
- [ ] 5.4 Run unit tests and execute the CLI twice; record only observed metrics and blockers.
