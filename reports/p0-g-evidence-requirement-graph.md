# P0-G Evidence Requirement Graph & Fact–Evidence Alignment

日期：2026-09-13
实验代码 commit：`429058ecbab4335922390d00026d3c4cf77b4e58`

## 1. 研究问题与边界

P0-E 已经证明，D3 的 `Predicted CER=1.0000` 不能代表真实完整性：同一 candidate evidence 被重复映射到多个语义不同的 predicted facts。P0-G 因此只解决一条主线：

> RAG 只有在所有 critical evidence requirements 都由角色正确、语义匹配、可独立验证的 evidence 或合法 derivation 满足时，才获得回答资格。

本轮没有修改 TAT-QA、FinQA 或 RealFinance-v1，没有引入 GraphRAG、Neo4j、Agent、VLM、ACL、FastAPI、Kubernetes 或新的通用 RAG framework。Targeted retrieval 仍是 deterministic，最多两轮。

## 2. 实现

### Requirement schema

新增 `Requirement`、`RequirementEdge`、`RequirementGraph`、`FactEvidenceAlignment`、`EvidenceReuseEvent` 和 `IndependentCoverageResult` Pydantic contracts。

`Requirement` 支持：

```text
requirement_id / description / fact_type / role
entity / metric / period / segment / basis / geography
currency / unit / operation / criticality
depends_on[] / acceptable_evidence_ids[]
```

`fact_type` 为 `RETRIEVED_FACT`、`DERIVED_FACT`、`EXPLANATORY_FACT`、`CONTEXT_FACT`；`criticality` 为 `CRITICAL`、`SUPPORTING`、`OPTIONAL`。Graph 校验 duplicate ID、unknown endpoint、self-edge、`depends_on` unknown ID 和 cycle。

### Graph example

```text
R1 current input value      RETRIEVED_FACT  CRITICAL
R2 prior input value        RETRIEVED_FACT  CRITICAL
R3 change                   DERIVED_FACT    CRITICAL
   depends_on = [R1, R2]
   operation  = change(R1, R2)

R3 is satisfied by independent coverage of R1 and R2;
R3 does not require a document chunk that literally states "change".
```

Explanation templates additionally separate observed outcome, supporting driver and management explanation; different roles cannot be covered by lexical overlap alone.

### Fact–evidence alignment and reuse

`align_requirement_to_evidence` emits support type, alignment score, matched slots, mismatched slots, reuse flag and reason. The explicit `EvidenceReusePolicy` only treats reuse as compatible when configured role/period/metric/entity slots are equal. Incompatible reuse is emitted as `EvidenceReuseEvent`, excluded from independent coverage, and surfaced as `EVIDENCE_REUSE_INFLATION`.

Derived requirements are propagated only after all `depends_on` requirements are independently covered. `CRITICAL_REQUIREMENT_MISSING` blocks `answer_eligible`; missing `SUPPORTING` requirements alone does not.

## 3. Data and annotation boundary

The experiment is a `public_benchmark_slice`: frozen `RealFinance-v1`, 100 cases (`50 TAT-QA + 50 FinQA`) and 1,652 Evidence IR items. The source repositories are [TAT-QA](https://github.com/NExTplusplus/tat-qa) and [FinQA](https://github.com/czyssrs/FinQA); this report uses the already committed source manifest, not a new benchmark claim.

`RequirementGold-v1` is intentionally:

```text
status     = N/A
case_count = 0
reason     = MANUAL_ANNOTATION_NOT_AVAILABLE
```

No automatically inferred entity/metric/period/role/criticality labels were promoted to canonical gold. Therefore `Critical Fact Recall` and `Slot Accuracy` remain `N/A`, rather than fabricated.

## 4. Results

Gold Independent CER is computed using the legacy gold required-evidence mapping adapted into a requirement graph. Predicted rows evaluate each method's own graph; they must not be read as canonical requirement understanding accuracy. `Oracle Gap = Gold Independent CER - Predicted Independent CER`.

| Method | Fact Precision | Fact Recall | Critical Fact Recall | Count Error | Raw Self Coverage | Independent CER | Critical Coverage | Reuse Rate | Invalid Reuse Rate | Eligible Rate | FAER | Oracle Gap | Critical Gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gold evidence condition | N/A | N/A | N/A | N/A | N/A | 0.9083 | 0.9083 | N/A | N/A | N/A | 0.0000 | N/A | N/A |
| D0 Heuristic | 0.0100 | 0.0017 | N/A | 0.73 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.9083 | 0.9083 |
| D1 LLM Direct | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| D2 Schema-constrained | 0.0033 | 0.0033 | N/A | 1.01 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.9083 | 0.9083 |
| D3 Evidence-aware | 0.0033 | 0.0033 | N/A | 1.01 | 1.0000 | 0.7283 | 0.7400 | 0.4100 | 0.4100 | 0.5900 | 0.4100 | 0.1800 | 0.1683 |
| D4 Requirement-Graph-Constrained | 0.0000 | 0.0000 | N/A | 1.02 | 0.6133 | 0.5033 | 0.5050 | 0.2957 | 0.3600 | 0.3800 | 0.0000 | 0.4050 | 0.4033 |

The Gold Independent CER is `0.9083` on this run's graph-based bounded retrieval condition. D3 is the key P0-G acceptance result: `Raw Self Coverage=1.0000` falls to `Independent CER=0.7283`, `Critical Coverage=0.7400`, with `Invalid Reuse Rate=0.4100` and `FAER=0.4100`. This is not a quality improvement claim; it is evidence that the new gate can expose and block P0-E's false-completeness mechanism.

D4 does not improve requirement understanding on this public slice. Its deterministic templates have `Independent CER=0.5033` and `Critical Coverage=0.5050`; this negative result is retained. Without `RequirementGold-v1`, D4's structured role/type/slot accuracy cannot be scientifically claimed.

## 5. Failure taxonomy and targeted retrieval

The 372 retained failure rows expand to the following emitted categories:

| Failure type | Count |
| --- | ---: |
| `CRITICAL_FACT_MISSING` | 303 |
| `EVIDENCE_MAPPING_FAILURE` | 303 |
| `EVIDENCE_REUSE_INFLATION` | 77 |
| `PREDICTED_REQUIREMENTS_UNDER_SPECIFIED` | 186 |

Counts are event/category counts, so one trace can contribute more than one category. The deterministic bounded loop was used only to retrieve missing critical requirements and re-align evidence; targeted retrieval was attempted for D0 `100/100`, D2 `100/100`, D3 `41/100`, and D4 `69/100` traces. It is not an Agent loop.

Every formal trace contains question type, gold/predicted graph, initial/final evidence, alignments, invalid reuse events, missing critical requirements, targeted queries, coverage fields, eligibility and warnings. The run contains 500 trace rows (100 each for D0–D4; D1 remains explicit `N/A` rows), 500 graph rows, 500 alignment rows and 372 failure rows.

## 6. Reproducibility

Both runs used `configs/p0_g_cpu.json` and recorded the implementation commit above:

```text
finevidence/artifacts/p0_g_runs/20260912T215237402336Z-d20699d7/
finevidence/artifacts/p0_g_runs/20260912T215349801181Z-e6d7cba3/
```

The following SHA-256 values were byte-identical between runs:

```text
metrics.json              0BC79D38B9DBDC448BF87311077CFBBFD5EC526B4AA6D87CB1AA5BA89DAA4A61
dataset_manifest.json     47922310CEF62E54786E32FA286555564A939462FAB94F4FDCEB7A850D8D4240
per_query_trace.jsonl     4BC0026C2B455B07BACDC34E9294D07782A0CC8F9969E6A689B9075A8C70EB44
requirement_graphs.jsonl  3313A9C3B04A7322A5A300006F067FABD327D24C68551113A8C787E44FD309A7
alignment_results.jsonl   B28CDA78CB7DB504F73280907AFED972F72ADFD72E284DBB3E3E397F0CAEE56D
failure_cases.jsonl       DA3D6A3E19BC97F2FB29332F9A34C8F96848462B6329205841603333BC403BB7
```

The alignment hash above is the exact hash from both runs; the report artifact remains a summary and does not replace the run files.

## 7. HSBC provenance track and B3 gate

HSBC remains a URL-only/opt-in local fetch track. The official HSBC results page is the source entry point for FY2025 Annual Report and Pillar 3 disclosures ([HSBC Annual Report and Accounts](https://www.hsbc.com/investors/results-and-announcements/annual-report)); no PDF was added to this commit, and the local HSBC metric/stress set remains `N/A` until download, hash, page count and local provenance are closed.

B3 remains blocked. `RequirementGold-v1` is not yet available, D4 has not shown a real requirement-understanding improvement, and the HSBC local corpus is not fixed. Independent Coverage now exists and blocks D3 reuse inflation, but that alone is not a license to enter visual retrieval or claim multimodal gains.

## 8. What remains unproven

- Canonical requirement type, role, slot and criticality accuracy on manually annotated cases.
- Neural or VLM fact verification; the current alignment is deterministic lexical/slot logic.
- Generalization to long multi-page tables, visual-only evidence, citation bounding boxes, version conflicts, ACLs and multimodal cross-page questions.
- Production latency, storage, GPU cost and million-page scaling.

The P0-G answer is deliberately narrow: a related evidence item is not enough; independent critical requirement coverage is the admission test, and the current system can now expose when that test fails.
