# FinEvidence Project Strategy

> 阶段：Phase 1 research strategy
>
> 更新时间：2026-09-13
>
> 状态：P0-H 已完成；B3/B3.1 已完成真实 HSBC CPU visual track 与评估闭环，但 FinRAGBench-V public page-image archive 仍 blocked，B3=`PARTIAL`。

## 一句话定位

**FinEvidence 是面向银行与金融研究场景的、以可验证证据为中心的金融 Multimodal RAG 平台。**

核心交付不是回答更多问题，而是：

~~~text
找到正确金融证据
→ 证明证据足以支持答案
→ 保留 page/block/table-cell/provenance
→ 证据不足时拒答或部分回答
~~~

## P0：先解决三个可测 failure

| 优先级 | Failure | 为什么选它 | 最小交付 |
| --- | --- | --- | --- |
| P0-A | Financial table / visual evidence structure loss | 公开讨论直接展示 row/column 混淆；FinRAGBench-V 能提供视觉引用；金融数字错误风险高 | Document/Page/Block/Table/Cell/Evidence contract；原页+结构化解析；cell/page citation |
| P0-B | Evidence set incomplete | 命中一个相关 chunk 会让跨报告问题看起来答对但不完整；ICBCBench 可覆盖复杂金融问题 | required facts/evidence plan；coverage gate；最多一次受控 retry；insufficient evidence abstention |
| P0-C | Financial hard-negative ranking | 金融指标、年份、实体高度相似；Financial Asset QA System 未证明这一层 | canonical metric/entity/period metadata；hard-negative set；Metric Disambiguation Accuracy |

## P1

- claim-level verification：每个 material claim 指向 Evidence。
- executable numerical reasoning：计算只接受已验证 table cell 输入，保存公式、输入和结果。
- visual retrieval cascade：只对 chart/table/diagram 或 text-first 不足的 query 启用视觉通道。

## P2

- retrieval-time RBAC/ABAC，Unauthorized Retrieval Rate = 0。
- content hash、index generation、promotion gate、rollback。
- lineage/audit/trace、P50/P95、GPU/storage/cost。
- conditional graph retrieval；仅在存在可验证关系型问题时实现。

## 暂不做

- 不重写 RAGFlow 或 RAG-Anything。
- 不先搭 Milvus/OpenSearch/Neo4j/Kubernetes 全套基础设施。
- 不把 LangGraph、GraphRAG、Agent 数量当成果。
- 不将工业、医疗、法律等领域加入当前主范围。
- 不在没有 baseline 和 ablation 时写“提升”“SOTA”或简历数字。

## P0 系统边界

~~~text
Public financial documents
  → source/content hash
  → page-preserving parse
  → Document IR + Table/Cell IR + optional visual page index
  → baseline retrieval
  → Evidence IR
  → evidence coverage gate
  → deterministic table calculation when required
  → answer with page/block/cell citations or abstain
~~~

P0 不承诺完整 GraphRAG、完整多租户平台或线上 K8s。先证明一个窄链路能让错误可见、可复现、可归因。

## Baseline ladder

1. B0 Vanilla dense：固定 manifest、固定 page/chunk 单位、单通道 dense retrieval。
2. B1 Hybrid + rerank：加入 lexical/BM25 与 cross-encoder。
3. B2 FinEvidence P0：B1 + structure-preserving table/cell evidence + coverage gate + citation trace。
4. B3 optional visual：B2 + visual retrieval，仅在 modality classifier 认为需要时路由。

当前候选仓库的最小本地词面探针已经暴露一个可验证起点：`收入和净利润的区别是什么` 与 `什么是可转债的强赎条款` 的 top-1 都落到教材书目信息页，且市盈率查询出现重复来源。该观察只说明候选 baseline 的 evidence precision/去重/粒度存在问题，不代表 B0 dense 或本项目方案的最终指标。

## 成功门槛

- [ ] B0/B1 在同一公开 split 上产生可复现检索结果。
- [ ] 至少一个表格或视觉 hard case 能定位到 page/block/cell。
- [ ] 至少一个跨文档问题能显示 required evidence coverage。
- [ ] 至少一个 unanswerable case 被拒答或返回明确 partial answer。
- [ ] 至少一个 financial hard-negative case 能报告正负 evidence 排序。
- [ ] claim、evidence、source/page/region/cell 关系可序列化并回放。
- [ ] 至少一次组件变化触发 retrieval regression 报告。

## 假设与证伪

| 假设 | 当前状态 | 证伪方式 |
| --- | --- | --- |
| table/cell evidence 会减少 row/column 错配 | Hypothesis | 与 B1 对照，测 cell selection、numeric accuracy、citation cell accuracy |
| coverage gate 会降低 unsupported answer | Hypothesis | answerable/partial/unanswerable 分层，测 false answer rate |
| hard negatives 会降低相似指标混淆 | Hypothesis | 固定 hard-negative pairs，测 top-k ranking |
| visual channel 只对部分 query 有净收益 | Hypothesis | query modality slice + quality/latency/cost |

## 近阶段顺序

1. 锁定 FinRAGBench-V 可用切片和 ICBCBench public manifest。
2. 从 Financial Asset QA System 抽取不依赖线上行情 API 的最小 baseline。
3. 定义 JSON/Pydantic Evidence IR 和 gold evidence record。
4. 跑 B0/B1，先产出 Recall@K/MRR/nDCG 与成本。
5. 加入一个表格 cell hard case 和一个跨文档 evidence-set hard case。
6. 再决定 visual retrieval、claim verification、计算执行器是否进入 P0 结果。

## 证据规则

代码存在 ≠ 默认路径启用。测试通过 ≠ benchmark 质量提升。答案正确 ≠ citation 正确。citation 存在 ≠ citation 支持 claim。相关文档召回 ≠ required evidence set 完整。任何“提升 X%”必须来自固定 baseline、固定样本和可复现实验输出。

## P0 首次可复现实验结果

2026-09-13 在 `finevidence/benchmarks/mini_finance` 的固定 30 题开发切片上运行，排除了 1 条 unanswerable case 的 retrieval 分母；最新运行 commit 为 `80b60f388dc60a6b083c2aecc4a25a4e922d4a63`。

| System | Recall@5 | nDCG@10 | Complete Evidence | HN Error |
| --- | ---: | ---: | ---: | ---: |
| B0 `tfidf_svd_dense` | 0.7586 | 0.6053 | 0.7586 | 0.7000 |
| B1 hybrid + generic reranker | 0.7931 | 0.6202 | 0.7931 | 0.7000 |
| B2 coverage gate | 0.7931 | 0.6202 | 0.7931 | 0.7000 |
| B3 conditional visual | N/A | N/A | N/A | N/A |

这组数字只证明当前 MiniBench 与 CPU baseline 可复现，不证明对公开 benchmark 的提升。B2 当前已实现 coverage 判定和 `answer_eligible`，尚未接入 generation 或 targeted re-retrieval；B3 因没有 visual encoder/真实视觉索引保持 N/A。首轮结果也显示 B1 没有降低 hard-negative error，正好支持 P0-C 继续单独做 financial-aware ranking，而不是把 generic reranker 当作解决方案。

## P0-B/P0-C 结论驱动实验结果

本阶段不再按“增加一个 RAG 功能”推进，而按两个可验证结论推进：

1. **部分证据不应自动获得生成资格。** 在 `EvidenceCompleteness-v1` 的 30 条受控 multi-fact cases 上，Top-K 只要命中任一事实就允许生成时，False Answer Eligibility Rate 为 `0.9000`；加入 fact completeness gate 后为 `0.0000`。bounded targeted retrieval 在最多两轮内将 Initial CER `0.0000` 提升到 Final CER `1.0000`，Partial-to-Complete Recovery 为 `1.0000`。
2. **通用排序器不能解决金融 hard negatives。** 在 `FinanceHardSet-v1` 的 100 条受控 cases 上，Dense HN Error `0.3000`，Hybrid+Generic 仍为 `0.3000`；加入显式 financial facets 后为 `0.0000`，hard-negative-aware adapter 也为 `0.0000`。Recall@5 在四个 variant 均为 `1.0000`，因此本轮真正有区分度的信号是 MRR/nDCG/HN Error，而不是 Recall@5。

实现与产物：`finevidence/src/finevidence/evidence/coverage.py`、`retrieval/targeted.py`、`ranking/`、`eval/p0_bc.py`；固定数据与 manifest 位于 `finevidence/benchmarks/evidence_completeness_v1/` 和 `finevidence/benchmarks/finance_hardset_v1/`；结果位于 `finevidence/artifacts/p0_bc_runs/20260912T193620598730Z-7739efd4/`，同配置复现实验位于 `finevidence/artifacts/p0_bc_runs/20260912T193744723802Z-f7209d8d/`。

最终 provenance run 为 `finevidence/artifacts/p0_bc_runs/20260912T194238271033Z-32c91647/`，其 config 记录 commit `388b7bf25aba5ec801819380042a8884be24c603`。

加入 per-category HN Error 后的最终复现 run 为 `finevidence/artifacts/p0_bc_runs/20260912T194510302588Z-215a6ab3/` 与 `finevidence/artifacts/p0_bc_runs/20260912T194530353818Z-28ec8d23/`，config 记录最终 commit `27cb86b80f8d42e30852e8b6014ed5d36efef036`，两次 summary tables 一致。

解释边界：两个新 suite 是 development fixtures，不是外部 benchmark 成绩；facet vocabulary 也只是 deterministic v1，不能据此声称解决了真实企业中的所有版本、语言、别名和表格上下文问题。P0 下一步应优先把同样的 trace/eval contract 迁移到一个已获得许可且 query-qrels-evidence 闭环完整的真实金融切片，再决定是否进入 visual/page-preserving ingestion。

## P0-D 外部有效性结果

本阶段已从 mechanism validation 切换为 external validity。新增 `RealFinance-v1`，固定选择 TAT-QA dev 的 50 条 `table-text` questions 和 FinQA dev 的 50 条 answerable records。原始数据不复制进 Git；来源 repo commit、文件 hash、selection rule 和派生文件 hash 均记录在 manifest。

| Public slice condition | Recall@5 | MRR | nDCG@10 | Initial CER | Final CER | Recovery |
|---|---:|---:|---:|---:|---:|---:|
| Dense + gold facts | 0.0900 | 0.1027 | 0.0773 | 0.0300 | 0.8900 | 0.8866 |
| Hybrid + Generic + gold facts | 0.1417 | 0.1895 | 0.1405 | 0.0300 | 0.8900 | 0.8866 |
| Facet-aware / predicted facets | 0.1417 | 0.1912 | 0.1398 | N/A | N/A | N/A |

Required Fact Precision=`0.0100`、Required Fact Recall=`0.0017` 是当前 deterministic decomposer 的真实观测，不能被 predicted-fact self-coverage `0.9200→0.9900` 掩盖。11/100 条 gold-fact cases 在两轮 targeted retrieval 后仍不完整，失败样本已保留。

当前 gate：`HSBC-Stress-v1=N/A`，reason=`LOCAL_PROVENANCE_SOURCE_MISSING`；未用人工候选替代真实 HSBC corpus。P0-D 之后应先提高真实数据上的 fact decomposition/证据映射可信度，并接入一个许可清晰的 HSBC source slice，再考虑 B3 visual。

P0-D 最终 provenance：实验代码提交 `d97557d624b7dbe99ef6bff28acc057401d966a4`；复现 run 为 `finevidence/artifacts/p0_d_runs/20260912T202547160764Z-62a4fd11/` 与 `finevidence/artifacts/p0_d_runs/20260912T202612338140Z-c2f60731/`。两次 run 的 metrics 与 dataset manifest 内容一致，各含 100 条 trace、11 条 failure cases；Top-K FAER=`0.1200`，Coverage Gate/Targeted Retrieval FAER=`0.0000`。

## P0-E Evidence Requirement Understanding

P0-E 已落地为最小可运行实验：结构化 `FactSlots` 包含 `fact_type/entity/metric/period/segment/basis/operation/unit/role/critical`；D0 是冻结 heuristic，D1 没有授权 provider 时显式 `N/A`，D2 使用 question-type template，D3 只保留 bounded candidate evidence 中存在的 evidence IDs。

最终 run 观察：gold evidence Initial CER=`0.0500`、Final CER=`0.8900`、Recovery=`0.8842`、FAER=`0.0000`；D0 Fact Recall=`0.0017`，D2/D3=`0.0033`，critical/slot accuracy=`N/A`。D3 predicted CER=`1.0000`、Oracle Gap=`-0.1100`，已标记为 predicted facts under-specified/calibration warning，不能当作模型提升。D1=`N/A / LLM_PROVIDER_NOT_CONFIGURED`。

代码提交 `ea7876b4caad8aca9dee22fbb106a60a55bb14e7`；最终复现 run 为 `finevidence/artifacts/p0_e_runs/20260912T205940827353Z-bc0c3c06/` 与 `finevidence/artifacts/p0_e_runs/20260912T210052094393Z-edbc1aa9/`，两次 metrics/manifest 一致。P0-F 只完成官方 HSBC URL manifest 与 opt-in fetcher，未提交 PDF；B3 仍 blocked。

## P0-G Evidence Requirement Graph & Fact–Evidence Alignment

P0-E 的 `D3 Predicted CER=1.0000` 已被定位为 evidence reuse inflation，而不是效果提升：一个 candidate evidence 被 lexical overlap 复用于多个不等价 predicted facts。P0-G 在不修改 RealFinance-v1 的前提下新增 Requirement schema、Python/Pydantic DAG、Fact–Evidence Alignment、保守 `EvidenceReusePolicy`、Derived Fact dependency propagation 和 Critical Fact Gate。`answer_eligible` 现在要求所有 `CRITICAL` requirements 被独立支持；derived fact 由依赖事实合法推导，不要求直接 chunk。

最终两次 P0-G run：`finevidence/artifacts/p0_g_runs/20260912T215237402336Z-d20699d7/` 与 `finevidence/artifacts/p0_g_runs/20260912T215349801181Z-e6d7cba3/`，均记录代码 commit `429058ecbab4335922390d00026d3c4cf77b4e58`；metrics、dataset manifest、graph/alignment/trace/failure artifacts 的 SHA-256 完全一致。Gold Independent CER=`0.9083`。D3 的 Raw Self Coverage=`1.0000` 降为 Independent CER=`0.7283`、Critical Coverage=`0.7400`；Invalid Reuse Rate=`0.4100`、FAER=`0.4100`，证明系统能阻断并暴露 P0-E 的假完美。D4 的 Independent CER=`0.5033`、Critical Coverage=`0.5050`，没有在当前 public slice 上显示真实 requirement-understanding 提升，因此不包装成优化结果。

`RequirementGold-v1` 当前为 `N/A / MANUAL_ANNOTATION_NOT_AVAILABLE`，0 cases；没有伪造 canonical slot、role、criticality gold，所以 Critical Fact Recall 与 Slot Accuracy 保持 `N/A`。D1 仍为 `N/A / LLM_PROVIDER_NOT_CONFIGURED`。HSBC 仍只完成 official URL manifest/opt-in fetcher，未形成本地固定 corpus；B3 继续 blocked。完整 P0-G 结果、failure taxonomy、targeted retrieval 统计和未证明事项见 `finevidence/reports/p0-g-evidence-requirement-graph.md`。

## P0-H Gold Requirement Validation & HSBC Natural Hard Cases

P0-H 已完成从“没有 canonical requirement labels”到可审计的 `RequirementAdjudicated-v1` 的最小闭环。它从冻结的 `RealFinance-v1` 选取 36 cases：factual 10、comparison 4、numerical 18、trend 3、explanation 1。标注采用双 pass + adjudication，但两个 pass 都是模型辅助/规则辅助，`human_verified=false`；因此它不是 `RequirementGold-v1`，也不是人类专家 gold。

最终 clean-commit run 为 `finevidence/artifacts/p0_h_runs/20260913T004424445930Z/` 与 `finevidence/artifacts/p0_h_runs/20260913T005105288692Z/`，代码 commit `95885590e2b5d49fb61a8c448e4df4ae46142004`，所有正式产物逐文件 SHA-256 一致。D1 使用本机缓存的 `HuggingFaceTB/SmolLM2-135M-Instruct`、Transformers CPU、temperature 0、64 max new tokens，真实生成但 36/36 不能通过 JSON schema，正式记为 `N/A / MALFORMED_LLM_JSON`。

| Method | Req Precision | Req Recall | Critical Recall | Type Acc | Role Acc | Dependency Acc | Count Error | Independent CER | Critical Coverage | FAER |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D0 Heuristic | 0.0000 | 0.0000 | 0.0000 | 1.0000 | N/A | N/A | 1.3056 | 0.0000 | 0.0000 | 0.0000 |
| D1 LLM Direct | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| D2 Schema-constrained | 0.2778 | 0.2778 | 0.2778 | 1.0000 | 1.0000 | N/A | 0.0278 | 0.0000 | 0.0000 | 0.0000 |
| D3 Evidence-aware | 0.2778 | 0.2778 | 0.2778 | 1.0000 | 1.0000 | N/A | 0.0278 | 0.0000 | 0.0000 | 0.0000 |
| D4 Requirement Graph | 0.7222 | 0.7222 | 0.7222 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.3704 | 0.3750 | 0.0000 |

D4 在这个 annotation policy 上优于 D0/D2 的 requirement recall，但不能把它当作完全独立 human-gold 提升：adjudicated derived graph 使用了与 D4 相同的 question-type templates，这是已记录的上限/偏差。D4 的 Raw Self Coverage=`0.5185` 高于 Independent CER=`0.3704`，Invalid Reuse Rate=`0.5000`；Gold/adjudicated evidence coverage 只有 Independent CER=`0.2593`、Critical Coverage=`0.2593`。

HSBC provenance track 已固定官方 FY2025 Annual Report（372 pages，SHA `94aab2f5c83d1060ee95d344f1915833869fe4502dc635e4ab9ca84f496ee94b`）与 FY2025 Pillar 3（122 pages，SHA `eb64c8f0fcd32648512979886bceddba7128558761c07948b50f6ecfa83a32f7`），本地 PDF 在 ignored `finevidence/artifacts/hsbc_local_sources/`。从真实解析 page blocks 产生 `HSBCNaturalHard-v1` 59 cases；这是 project-created stress benchmark，不是 HSBC official benchmark。Dense/Hybrid+Generic HN Error=`0.3898`，facet-aware variants HN Error=`0.0339`，Ranking Oracle Gap=`0.0000`。

P0-H B3 gate 为 `READY`，因为 requirement adjudication、Independent Coverage validation、HSBC provenance 和 >=50 natural hard cases 均满足；D1 是否可用、D4 是否优于 baseline 仍作为独立报告项，不被 gate 静默吞掉。下一阶段可以进入 B3 设计，但本轮没有实现 Visual Retrieval。正式报告见 `finevidence/reports/p0-h-gold-requirement-hsbc-natural-hardcases.md`。

## B3.2 Benchmark Integrity & Public Closure（2026-09-14）

B3.2 保留全部 B3.1 结果，并新增 performance-blind 的 `HSBCVisualStress-v1` 构造审计与独立的 `HSBCNaturalMultimodal-v1` 80-case real-page control。审计确认 stress set 存在 construction bias：60 cases 只有 10 个固定关键词模板，positive page 由关键词命中选择；T0 Recall@10=`0/60` 可复现，但 @50=`7/60`，不能当作自然文本检索估计。固定 20-case attribution 为 `TABLE_STRUCTURE_LOSS=8`、`CHART_VISUAL_ONLY=8`、`PAGE_FRAGMENTATION=2`、`LAYOUT_DEPENDENCY=2`，均为 deterministic audit inference。

自然控制集按语料页 hash 在读取 T0/V0 之前冻结，且排除 stress candidate pages。其 @10 Recall：T0=`0.5375`、T1 Parsed Page Text=`0.5875`、V0=`0.0750`、M1=`0.5625`；因此当前证据不支持“视觉普遍优于文本”。Verified Structured Table IR 仍为 `N/A`。

FinRAGBench-V 仍固定为 revision `d0d65255c94e687caa81ac9da7758ed25ff046a5` 的 100-query slice。B3.2 通过 WSL Ubuntu 对官方 URL 做了带断点的第二种传输尝试，响应确认 revision/长度/Range identity，但 2.38GB 文件在可接受边界内无法完成；完整日志与 blocker summary 已保存，未从 partial file 运行评估。B3 状态保持 `PARTIAL`，B4 production hardening 不解锁。报告：`finevidence/reports/b3-2-benchmark-integrity-public-closure.md`。

## B4 Structure-Preserving Evidence IR & Failure-Aware Escalation (2026-09-14)

B4 is complete for the scoped experimental phase. It adds `TableIR`/`TableCell` over frozen TAT-QA source arrays and preserves raw-value round-trip, stable cell identity, and row/column relations on 15 unique tables. HSBC's existing parser remains page-text-only, so verified structured Table IR on HSBC is explicitly `N/A`.

E0 oracle routing and E1 predicted routing were evaluated on unchanged `HSBCVisualStress-v1`. E1 route accuracy is `0.5000`; visual invocation falls to `0.5000`, but table cases cannot use the unavailable HSBC Table IR. Predicted-router page Recall@10 is `0.0833`; no production cost saving is claimed. FinRAGBench-V remains a separate B3 blocker after a pinned corpus-layout investigation found 14 multi-gigabyte compressed English shards rather than individually addressable page images. B3 stays `PARTIAL`; B4 does not unlock production hardening. Formal code commit: `251b7a895c03a34e182a97058450ae436d21aab6`. Report: `finevidence/reports/b4-structure-preserving-evidence-ir-failure-aware-escalation.md`.

## B4.1 Real Financial Table Recovery & Executable Structured Retrieval（2026-09-14）

B4.1 在不重做 B3/B4 历史实验的前提下，使用真实 HSBC FY2025 Annual Report 页面 1–26 建立 geometry-assisted PDF-to-TableIR extractor。共接受 24 个真实 table-like regions、覆盖 13 页；TableIR 的 cell identity 与 row/column relation invariants 均为 1.0000，bbox 可恢复率为 0.7418、header path population 为 0.7278。语义 cell accuracy、unit accuracy、merged-cell accuracy 没有 verified human gold，全部保持 N/A。

新增 `T2 Real Structured Table IR` deterministic cell executor，并与 T0 Text Only、T1 Parsed Page Text、V0 Visual Only、T2+Text RRF 及 diagnostic Oracle Table Executor 比较。冻结 `HSBCVisualStress-v1` 60-case 全集上，T2 Page Recall@1/@5/@10=`0.0167/0.0833/0.0833`，相对 T1 在四类 table failures 上 @10 恢复 5 个页面、critical qualification 恢复 4 个，未观察到 table-category regression；但 V0 @10=`0.1000`，所以不能宣称结构化 executor 已胜过视觉或已证明语义恢复。

正式代码 commit 为 `16137e652215edc83f01d044f5826e9787a7c15e`；两次 run 为 `finevidence/artifacts/b4_1_runs/20260914T013358/` 与 `20260914T013551/`，结构/排名产物一致，CPU timing 随负载变化。B4.1 在 scoped experiment 内完成；B3 仍因 FinRAGBench-V public page-image track 外部 blocker 保持 `PARTIAL`。报告：`finevidence/reports/b4-1-real-financial-table-recovery.md`。
## B3 — Multimodal Evidence Retrieval & Visual Grounding (2026-09-13)

B3 is implemented as an executable partial phase. It renders the fixed official HSBC FY2025 corpus into 494 deterministic 72-DPI page images, indexes real image evidence with OpenAI CLIP RN50 on CPU, compares text, structured-text adapter, visual, RRF/weighted fusion, and coverage-aware conditional paths, and sends visual candidates through the existing FactEvidenceAlignment and IndependentCoverage gate. The 60-case `HSBCVisualStress-v1` result is intentionally weak: Visual Only Page Recall@5 is 0.0500, M1 Conditional is 0.0167, text failure recovery is 0.0500, regression is 0.0000, and visual invocation is 1.0000 because all cases initially lacked qualified critical coverage. This does not prove a production visual win or a cost win.

`FinRAGBench-V-Slice-v1` fixes 100 English queries/qrels, but its required 2.378GB English PDF archive timed out from Hugging Face; all public page-image metrics are `N/A`. Therefore B3 is `PARTIAL`, not `COMPLETE`. The next gate requires fixing that public slice and adding verified table geometry before production hardening.
### B3.1 evaluation closure (2026-09-13)

B3.1 did not rerun P0-H or expand scope. HSBCVisualStress-v1 remains 60 cases; T1 is honestly `T1 Parsed Page Text`, with verified Structured Table IR=`N/A`. Recovery is explicit at @1/@5/@10. A separate real-page HSBCMultimodalRouting-v1 has 30 balanced cases (10 text-sufficient, 10 parsed-table-sufficient, 10 visual-needed). Final code commit is `52554ea096fdd846cde7981f269a2c245b2a1732`; ranking/metrics/failure artifacts are byte-identical across the final pair, while CPU timing is naturally variable.

The official Hugging Face client was upgraded to `huggingface_hub==0.34.4` plus `hf_xet==1.6.0`; the frozen slice is pinned to revision `d0d65255c94e687caa81ac9da7758ed25ff046a5`. The 2.38GB PDF archive still failed through project-local Xet and HTTP fallback with retained traceback/zero-byte cache evidence, so FinRAGBench-V page-image metrics remain `N/A`. B3 remains `PARTIAL`; no production hardening follows from this result. See `finevidence/reports/b3-1-public-benchmark-evaluation-closure.md`.
## Evidence Backend v1（2026-09-14）

在不改变 P0–B4 历史实验的前提下，`finevidence` 新增薄型 Evidence Backend v1：版本化 `EvidenceObject`、证据搜索、Requirement/Independent Coverage、table evidence query、claim verify 和 citation projection。FastAPI 仅作为 HTTP/JSON adapter；Agent、生成、PDF parser、ACL enforcement、持久化和 production serving 仍不在本阶段范围内。安全过滤没有 authorizer 时 fail closed。架构、API、Agent integration 与 ADR 见 `finevidence/docs/`。

## B5 Neural Retrieval & Controlled Agentic Search（2026-09-14）

B5 先建立现代检索的可审计边界，而不是默认堆叠模型。首个 B5.1 增量新增真实可选的 `QwenEmbeddingRetriever` adapter、bounded typed search controller、typed in-memory evidence graph 和 frozen `RealFinance-v1` runner。当前机器 Python 3.12、PyTorch 2.8.0+cpu、无 CUDA；Qwen3 Embedding 缓存只含 tokenizer/config，没有权重，HF/Xet 权重获取在 bounded attempt 内为 0 bytes，因此 Qwen R@1/R@5/R@10/MRR/nDCG/CER 全部保持 N/A。当前 dense/hybrid 的新基线结果写入独立 `artifacts/b5_1_runs/`，不覆盖 P0–P0-J 历史结果。

B5.1 当前状态为 `PARTIAL / MODEL_WEIGHTS_BLOCKED`。不能据此声称 Qwen、neural reranker、ColBERT、ColQwen、GraphRAG 或 Agentic Search 已经改善金融检索。后续只有在真实模型执行、冻结消融、Evidence Qualification 和成本/失败归因同时存在时，才允许 `PROMOTE`。
