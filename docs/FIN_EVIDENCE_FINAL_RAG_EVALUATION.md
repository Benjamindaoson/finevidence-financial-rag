# FinEvidence Final RAG Evaluation

Status: **P0-J PARTIAL / BLOCKED_FOR_HUMAN_VERIFICATION**

## 1. What this phase verifies

The remaining evaluation question is not whether retrieval can return a relevant
page. It is whether a high-stakes answer can be audited at three final trust
boundaries: each claim is supported by the cited evidence; a recovered
financial table preserves the semantics of its cells, headers, units and
footnotes; and the system distinguishes answerable, partially evidenced and
unanswerable questions before it answers.

`src/finevidence/eval/final_rag.py` is a pure scoring contract. It returns
`N/A` rather than zero when the required gold is not human verified.

## 2. Annotation integrity

No repository annotation currently has `human_verified=true`. Existing
`RequirementAdjudicated-v1`, `HSBCNaturalHard-v1`, `HSBCVisualStress-v1` and
`HSBCNaturalMultimodal-v1` remain model-assisted or project-created datasets,
not human gold.

This phase creates `FinalRAGEvalCandidate-v0`, not Gold:

| Track | Candidate rows | Source | Status |
|---|---:|---|---|
| Claim citation | 50 | frozen `RealFinance-v1` | candidate-only |
| Table semantics | 24 regions | B4.1 HSBC `TableIR` | candidate-only |
| Answerability | 60 | frozen `RealFinance-v1` | blocked; 60 answerable, 0 partial, 0 unanswerable |

The review package and its local workbench are documented in
`docs/FIN_EVIDENCE_HUMAN_VERIFIED_FINAL_RESULTS.md`. A second candidate queue,
`FinancialAnswerabilityCandidate-v1`, contains 20/20/20 proposed
answerable/partial/unanswerable cases. Its partial and unanswerable labels are
scoped evidence-availability constructions and still require human correction
or confirmation; they are not gold.

`ClaimCitationCandidate-v1` additionally preserves the real P0-D initial
Top-K@5 prediction IDs beside the source-projected supporting-evidence
candidates. The reviewer can therefore distinguish what the historical
retriever returned from what the source record suggests should support the
claim.

The queues contain source hashes, annotation status, zero annotators and an
explicit review requirement. They do not contain invented labels. A real
reviewer must promote rows and add claim, page/block/cell, table-semantic or
answerability labels.

## 3. Evaluation contracts

### Claim-level citation

`citation_metrics()` scores case records using evidence-id set intersection.
It reports citation precision/recall/F1, claim support rate and unsupported
citation rate. Page accuracy is available when both gold page and predicted
pages are supplied. Block and cell accuracy stay `N/A` when their gold
locations are absent. A page hit is not treated as claim entailment.

### Table semantic gold

`table_semantic_metrics()` keeps structural recoverability separate from
semantic correctness. It can score cell value, row/column mapping, header path,
unit, period, entity, merged semantics and footnote association, ignoring
explicitly missing fields. Existing B4.1 structural invariants are not
relabelled as semantic accuracy.

### Answerability and abstention

`answerability_metrics()` uses this action contract:

| Gold status | Safe expected action |
|---|---|
| `ANSWERABLE` | `ANSWER` |
| `PARTIAL_EVIDENCE` | `RETRIEVE_MORE` |
| `UNANSWERABLE` | `ABSTAIN` |

It reports action accuracy, strict abstention precision/recall/F1 for
unanswerable cases, false-answer rate on non-answerable cases,
false-abstention rate on answerable cases and partial-evidence detection rate.

## 4. Formal result

There is no valid final score in this run:

```text
claim citation:  N/A  (HUMAN_VERIFICATION_REQUIRED)
table semantics: N/A  (HUMAN_VERIFICATION_REQUIRED)
answerability:   N/A  (MISSING_PARTIAL_UNANSWERABLE_VERIFIED_SET)
```

This is a blocked measurement, not a failed model result. Reporting zero would
conflate missing ground truth with system failure.

## 5. Reusable historical evidence

The following numbers are unchanged:

| Dataset / phase | Result |
|---|---|
| RealFinance-v1 dense / hybrid Recall@5 | 0.0900 / 0.1417 |
| RealFinance-v1 dense / hybrid complete evidence rate | 0.0300 / 0.0500 |
| Gold-fact targeted retrieval final CER | 0.8900; FAER 0.0000 |
| P0-G D3 raw self-coverage vs independent CER | 1.0000 vs 0.7283 |
| P0-G D3 invalid evidence reuse rate | 0.4100 |
| P0-H D4 requirement recall on model-assisted adjudicated set | 0.7222; not human gold |
| HSBCNaturalHard facet-aware HN Error | 0.0339; deterministic scorer |
| B4.1 structural TableIR recoverability | 0.7418; semantic fields N/A |

These historical metrics do not substitute for claim support, semantic table
gold or abstention quality.

## 6. Reproducible artifacts

Candidate queues and the blocked run are under:

```text
artifacts/final_rag_eval/candidates/
artifacts/final_rag_eval/run_20260913T210959Z/
artifacts/final_rag_eval/run_20260913T211940Z/
artifacts/final_rag_eval/run_20260913T211959198877Z/
artifacts/final_rag_eval/run_20260913T211959607027Z/
artifacts/final_rag_eval/run_20260913T214749913820Z/
artifacts/final_rag_eval/run_20260913T214750236965Z/
```

Each valid run contains `config.json`, `dataset_manifest.json`,
`annotation_manifest.json`, candidate JSONL files, `predictions.jsonl`,
`metrics.json`, `failure_cases.jsonl` and `run_manifest.json`.

The two post-fix runs at `211959198877Z` and `211959607027Z` used the same
code commit and produced byte-identical metrics, manifests, candidate queues,
blocked rows and placeholder prediction records. The earlier `211940Z` run
is retained as the run that exposed the same-second directory collision before
the microsecond run-id fix.

The two post-workbench runs at `214749913820Z` and `214750236965Z` used commit
`143f52074457f7bf0b660b15e68bd5ca22d336b9` and were also byte-identical for
metrics, manifests, all three queues, blocked rows and placeholder predictions.
They include the balanced 20/20/20 answerability candidate queue.

The OpenSpec change is `openspec/changes/p0-j-final-rag-evaluation/`.

To open the review workbench locally:

```powershell
& .venv\Scripts\python.exe -m uvicorn finevidence.api.app:app --host 127.0.0.1 --port 8765
```

## 7. Next admissible action

The next action is annotation, not another retrieval feature: a real reviewer
must inspect the 50 claim candidates, 24 table regions and a deliberately
balanced answerability queue, record reviewer identity/protocol and promote
only verified rows. Until then, final citation, table semantic and abstention
claims remain unmeasured.
