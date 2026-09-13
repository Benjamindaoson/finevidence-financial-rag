# P0-H — Gold Requirement Validation & HSBC Natural Hard Cases

Date: 2026-09-13  
Formal code commit: `9588559d6c2c8d72f8fdc3156d3a3372153dbcc6`
Formal runs: `artifacts/p0_h_runs/20260913T004424445930Z/` and `artifacts/p0_h_runs/20260913T005105288692Z/`

## 1. Current question

P0-H asks whether a high-stakes financial RAG system can identify the distinct evidence roles required by a question and decide whether every critical role is supported by valid, independent evidence or a legal derivation.

The phase is intentionally not a new retrieval architecture. It tests four boundaries exposed by P0-G:

1. Is a requirement decomposition measurable against a non-fabricated canonical subset?
2. Can a derived answer be represented as dependencies rather than as a direct retrieval target?
3. Does Independent Coverage still reject false completeness when requirements are adjudicated from real finance cases?
4. Does facet-aware ranking survive naturally occurring hard negatives in official HSBC disclosures?

The governing rule is: a relevant chunk is not sufficient for answer eligibility; all critical requirements must be role-correct, independently supported, and traceable.

## 2. RequirementAdjudicated-v1

The source is the frozen `RealFinance-v1` public-source-derived slice: TAT-QA and FinQA records are not modified. A deterministic selection produced 36 cases:

| Question type | Cases |
| --- | ---: |
| factual | 10 |
| comparison | 4 |
| numerical | 18 |
| trend | 3 |
| explanation | 1 |
| multi-document synthesis | 0 |

Each case records question type, typed requirements, role, entity/metric/period/segment/basis/geography/currency/unit slots when available, operation, criticality, dependencies, acceptable evidence IDs, and evidence role. A comparison/numerical/trend result is represented as a `DERIVED_FACT` whose dependencies are retrieved inputs; it is not assigned a direct evidence chunk.

The annotation process is:

- Pass A: source-evidence/gold-answer/program constrained requirement construction.
- Pass B: independent question-type template or valid local-model output; it does not read Pass A.
- Adjudication: source evidence and the frozen answer/program resolve the disagreement.

The provenance is deliberately non-human:

```text
dataset_name       = RequirementAdjudicated-v1
annotation_method  = dual_pass_model_assisted_adjudication
human_verified     = false
```

It must not be called human gold, expert gold, or official TAT-QA/FinQA requirement gold. The annotation manifest hash is `7118b2d64ea3c115bdc40994b01a99a090dca2f19addd6d177556a483518f25f`. Pass-A/Pass-B agreement is:

| Agreement dimension | Rate |
| --- | ---: |
| requirement count | 1.0000 |
| question type | 1.0000 |
| fact type | 0.7222 |
| criticality | 0.7222 |
| role | 0.7222 |
| dependency | 0.7222 |
| evidence mapping | 0.2315 |

The low evidence-mapping agreement is retained as a finding. It shows that identifying an evidence need and identifying its exact supporting block are separate problems.

## 3. D0–D4 requirement understanding

The evaluation uses one-to-one structured matching: a predicted requirement can match at most one adjudicated requirement, and vice versa. Matching combines fact type, role, populated slot compatibility, and description overlap. Empty or unreliable canonical slots are not scored as fabricated accuracy.

| Method | Req Precision | Req Recall | Critical Recall | Type Acc | Role Acc | Dependency Acc | Count Error | Independent CER | Critical Coverage | FAER |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D0 Heuristic | 0.0000 | 0.0000 | 0.0000 | 1.0000 | N/A | N/A | 1.3056 | 0.0000 | 0.0000 | 0.0000 |
| D1 LLM Direct | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| D2 Schema-constrained | 0.2778 | 0.2778 | 0.2778 | 1.0000 | 1.0000 | N/A | 0.0278 | 0.0000 | 0.0000 | 0.0000 |
| D3 Evidence-aware | 0.2778 | 0.2778 | 0.2778 | 1.0000 | 1.0000 | N/A | 0.0278 | 0.0000 | 0.0000 | 0.0000 |
| D4 Requirement Graph | 0.7222 | 0.7222 | 0.7222 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.3704 | 0.3750 | 0.0000 |

Question-type breakdown for requirement recall / Independent CER / Critical Coverage:

| Type | Cases | D0 | D2 | D3 | D4 |
| --- | ---: | --- | --- | --- | --- |
| factual | 10 | 0.0000 / 0.0000 / 0.0000 | 1.0000 / 0.0000 / 0.0000 | 1.0000 / 0.0000 / 0.0000 | 0.0000 / 0.5000 / 0.5000 |
| comparison | 4 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 1.0000 / 0.3333 / 0.3333 |
| numerical | 18 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 1.0000 / 0.3333 / 0.3333 |
| trend | 3 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 1.0000 / 0.2222 / 0.2222 |
| explanation | 1 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 1.0000 / 0.3333 / 0.5000 |

D4 is better than D0/D2 on this adjudication policy, but the result is not an independent human-gold gain: the adjudicated derived graphs use the same question-type graph templates as D4. This is an explicit annotation ceiling and must be addressed by a future independently reviewed gold set.

## 4. D1 local LLM result

D1 used the locally cached `HuggingFaceTB/SmolLM2-135M-Instruct` snapshot with Transformers on CPU, greedy decoding (`temperature=0`, `do_sample=false`), prompt version `p0-h-d1-v1`, and `max_new_tokens=64`. The snapshot hash is recorded in each run config as:

```text
11ff5ece45b8301e23960285fb31779d5ee0d92db5f27509f4bf35e806d49049
```

The real model loaded and generated output, but all 36 cases failed JSON schema parsing after the bounded strict retry:

```text
D1 = N/A
reason = MALFORMED_LLM_JSON
cases = 36/36
```

The output was repetitive prompt text rather than a decomposition object. It is retained in `requirement_predictions.jsonl` and is not replaced by heuristic requirements.

## 5. Evidence coverage and reuse

The adjudicated evidence condition reached only:

```text
Independent CER       = 0.2593
Critical Coverage     = 0.2593
```

This is the evidence/retrieval ceiling on the 36-case subset, not an answer accuracy claim.

D4 produced:

```text
Raw Self Coverage     = 0.5185
Independent CER        = 0.3704
Critical Coverage      = 0.3750
Eligible Rate          = 0.1944
Evidence Reuse Rate    = 0.4150
Invalid Reuse Rate     = 0.5000
FAER                   = 0.0000
```

The raw-to-independent drop and 0.5000 invalid reuse rate show that a candidate evidence can look relevant to multiple requirements while failing the stricter role/slot policy. The recurring D4 reuse cases include `finqa:AAPL/2014/page_38.pdf-3`, `finqa:AES/2002/page_46.pdf-4`, `finqa:AOS/2004/page_11.pdf-2`, and `finqa:C/2010/page_223.pdf-3`. In the first case, the same table retrieval is not enough to independently establish both numeric inputs and the derived result.

The failure trace contains these label occurrences across method traces:

| Failure label | Occurrences |
| --- | ---: |
| EVIDENCE_MAPPING_FAILURE | 137 |
| MISSING_REQUIREMENT | 98 |
| OVER_SPECIFIED_REQUIREMENT | 98 |
| EVIDENCE_REUSE_INFLATION | 18 |

These are trace-level occurrences, not a claim that there are 137 unique source questions.

## 6. HSBC official corpus

The official source page is [HSBC Annual Report and Accounts](https://www.hsbc.com/investors/results-and-announcements/annual-report). The fixed local manifest is `artifacts/hsbc_local_sources/hsbc_corpus_manifest.json`; downloaded PDFs are ignored and are not committed.

| Document | Type | Period | Pages | Size | SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| `hsbc-fy2025-annual-report` | Annual Report | FY2025 | 372 | 10,110,145 | `94aab2f5c83d1060ee95d344f1915833869fe4502dc635e4ab9ca84f496ee94b` |
| `hsbc-fy2025-pillar-3` | Pillar 3 | FY2025 | 122 | 985,845 | `eb64c8f0fcd32648512979886bceddba7128558761c07948b50f6ecfa83a32f7` |

The minimal parser creates 492 page-level text Evidence IR records with document ID, page, source URI, block ID, modality, content hash, and extracted facet fields. This is a provenance/evidence-pool step, not a visual retrieval implementation.

## 7. HSBCNaturalHard-v1

`HSBCNaturalHard-v1` contains 59 valid project-created cases mined from real parsed HSBC page blocks. Each case has one positive and at least one high lexical-overlap candidate whose real document evidence conflicts on a financial facet or source. Candidates retain evidence ID, source hash, document, page/block provenance. Each kept case records `verification_pass_a=PASS`, `verification_pass_b=PASS`, and `adjudication_status=KEEP`; these are deterministic/model-assisted checks, not human review. The dataset records `human_verified=false` and is not an HSBC-official benchmark.

Category distribution:

| Category | Cases |
| --- | ---: |
| BASIS | 10 |
| CURRENCY | 10 |
| DOCUMENT_SOURCE | 10 |
| RELATED_METRIC | 9 |
| ENTITY | 6 |
| SEGMENT | 4 |
| TEMPORAL | 3 |
| METRIC | 3 |
| PERIOD_TYPE | 3 |
| GEOGRAPHY | 1 |

The miner retained 59 rather than the requested 60 because one candidate did not pass the hard-case quality gate. No fake candidate text was added to reach the target.

## 8. HSBC ranking

| System | Recall@5 | MRR | nDCG@10 | HN Error ↓ | Top-1 Positive |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dense | 0.1864 | 0.1312 | 0.1290 | 0.3898 | 0.0847 |
| Hybrid + Generic | 0.2881 | 0.2322 | 0.3364 | 0.3898 | 0.0847 |
| + Predicted Facets | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |
| + Adjudicated Facets | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |
| + Financial-aware deterministic reranker | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |

Per-category HN Error:

| Category | Dense | Hybrid | Facets / deterministic |
| --- | ---: | ---: | ---: |
| BASIS | 0.3000 | 0.3000 | 0.1000 |
| CURRENCY | 0.1000 | 0.1000 | 0.0000 |
| DOCUMENT_SOURCE | 0.6000 | 0.6000 | 0.1000 |
| ENTITY | 0.3333 | 0.3333 | 0.0000 |
| GEOGRAPHY | 1.0000 | 1.0000 | 0.0000 |
| METRIC | 0.0000 | 0.0000 | 0.0000 |
| PERIOD_TYPE | 0.3333 | 0.3333 | 0.0000 |
| RELATED_METRIC | 0.7778 | 0.7778 | 0.0000 |
| SEGMENT | 0.2500 | 0.2500 | 0.0000 |
| TEMPORAL | 0.3333 | 0.3333 | 0.0000 |

The ranking oracle gap is:

```text
HN Error(predicted facets) - HN Error(adjudicated facets) = 0.0000
```

Facet accuracy is `1.0000` for entity, metric, period, basis, and geography. Currency, segment, and period type are `N/A` because this set does not contain reliable adjudicated positive values for those slots. The zero oracle gap means this stress set does not demonstrate a predicted-facet extraction bottleneck; it demonstrates the value of the current deterministic facet signal on this slice. It does not demonstrate neural reranker quality.

## 9. Failure analysis

### Requirement failures

- `MISSING_REQUIREMENT` and `OVER_SPECIFIED_REQUIREMENT` dominate D0/D2/D3 because flat heuristics do not express the correct number of independently matchable roles.
- D4 fixes the representation of comparison/numerical/trend dependencies, but its coverage remains low because retrieval and alignment do not reliably locate every input.
- `EVIDENCE_MAPPING_FAILURE` remains common even when the graph shape is correct; evidence IDs and lexical relevance are not equivalent to entailment.
- `EVIDENCE_REUSE_INFLATION` persists in 18 D4 traces. Independent Coverage blocks those invalid reuses instead of allowing Raw Self Coverage to grant eligibility.
- No reliable canonical slot gold exists for broad entity/metric/period scoring beyond the subset’s structured annotations, so unsupported slot metrics remain `N/A`.

### HSBC ranking failures

The worst unassisted categories are GEOGRAPHY (`1.0000` HN Error), RELATED_METRIC (`0.7778`), DOCUMENT_SOURCE (`0.6000`), and BASIS (`0.3000`). Facet-aware deterministic ranking reduces these on the present set, but the result has a likely selection effect: queries were generated from positive facet-bearing pages and the current vocabulary covers the mined cases. This is evidence for a useful signal, not proof of enterprise-wide robustness.

## 10. B3 decision

```json
{
  "status": "READY",
  "requirement_adjudicated_v1": true,
  "d1_real_model_attempted": true,
  "d4_requirement_improvement": true,
  "independent_coverage_validated": true,
  "requirement_failure_localization": true,
  "hsbc_provenance_fixed": true,
  "hsbc_natural_hard_cases_at_least_50": true,
  "facet_evaluation_available": true
}
```

B3 is `READY` only under the explicitly frozen gate: adjudicated requirements exist, Independent Coverage is operationally validated, the HSBC corpus is fixed by provenance, and at least 50 valid natural hard cases exist. D1 availability and D4 improvement are reported independently; neither is silently substituted into the gate. This phase only unlocks the next-stage decision. It does not implement Visual Retrieval, ColPali, VLM generation, or the full multimodal corpus.

## 11. Reproducibility

Both formal runs used:

```text
code commit      = 9588559d6c2c8d72f8fdc3156d3a3372153dbcc6
config           = configs/p0_h_cpu.json
seed/temperature = deterministic / 0.0
model revision   = local-cache snapshot 12fd25f77366fa6b3b4b768ec3050bf629380bac
```

All required formal files were byte-identical between the two runs, including `requirement_predictions.jsonl`, raw D1 outputs, traces, rankings, failure cases, manifests, metrics, and `b3_gate.json`.

## 12. Scientific limits

This report does not prove:

- human-verified requirement annotation quality;
- a general LLM decomposition capability, because the available 135M model failed the output contract;
- neural reranker quality;
- visual/page-region retrieval, table structure fidelity, bbox citation correctness, cross-modal evidence, ACL behavior, version conflict resolution, unanswerable abstention, or parser regression;
- that the HSBC facet vocabulary covers all entities, segments, currencies, geographies, basis variants, or document types;
- that the current deterministic alignment is entailment verification.

The defensible conclusion is narrower: a typed requirement graph plus independent evidence coverage can expose the difference between self-coverage and answer-qualified coverage on a real finance slice; and a small official HSBC corpus can be fixed with auditable provenance and used to reveal financial hard-negative ranking behavior. The next stage may investigate multimodal retrieval, but it must retain these requirement, evidence, provenance, and failure-trace gates.
