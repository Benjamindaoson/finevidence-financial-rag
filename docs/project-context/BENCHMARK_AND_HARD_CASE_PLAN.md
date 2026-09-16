# Benchmark and Hard-Case Plan

> 更新时间：2026-09-13
>
> 当前状态：HSBC FY2025 本地 provenance 与 72-DPI page images 已固定并完成 B3/B3.1 stress/routing evaluation；FinRAGBench-V full corpus 未下载，其 pinned PDF archive page-image track 仍为 `N/A`。

## Benchmark roles

| Benchmark | 用途 | 当前已获得 | 不能直接推断 |
| --- | --- | --- | --- |
| ICBCBench | 金融 deep research / objective + subjective report / source quality | Git repository；objective 80 条、subjective 40 条；中英双语字段存在 | 不直接提供 page/block/cell visual citation；无 judged result 不能运行最终 metrics |
| FinRAGBench-V | 金融视觉检索、生成和 page/block visual citation | Git repository、retrieval/generation/eval 代码；README 描述中英金融页和 7 类 QA | Git clone 不含完整 corpus；citation evaluator 依赖外部 VLM |
| ViDoRe V3 Industrial/Finance | 企业视觉文档页级 retrieval 对照 | 已验证 benchmark 介绍和 collection 链接 | page retrieval 分数不等于 financial answer/cell citation/ACL/abstention |
| HSBC public corpus | supplementary real-world source | 用户纲要指定 Annual Report、Pillar 3、Data Pack、XLSX/XBRL | 未锁定版本、未核验页码不能当 gold evidence |

## Data acquisition gates

### Gate D0：manifest first

~~~text
dataset_name
source_url
source_revision_or_commit
download_timestamp_utc
local_path
sha256
license
page/document count
query count
~~~

未通过 D0 的数据不得进入正式 baseline。

### Gate D1：schema audit

- question/query id 唯一。
- qrels 与 corpus id 可解析。
- 页面图片、OCR/HTML/JSON 的 document/page id 一致。
- bbox 坐标在页面边界内。
- gold answer、required evidence、citation label 能区分。
- 缺字段不填默认真值，标为 missing。

### Gate D2：baseline reproducibility

- 固定 corpus/query/qrels manifest。
- 固定 retrieval unit。
- 固定模型、参数、device、seed 和 top-k。
- 保存 run file、metrics JSON、stderr、环境摘要和 git commit。

## Metrics

~~~text
Retrieval: Recall@1/@5/@10, MRR, nDCG@10
Evidence: Evidence Set Recall, Evidence Coverage, Missing-Fact Detection, Cross-page Coverage
Financial/table: Metric Disambiguation Accuracy, HardNegativeErrorRate, Cell Selection Accuracy, Formula Accuracy, Numerical Accuracy
Trust: Claim Support Rate, Unsupported Claim Rate, Page/Block/Cell Citation Accuracy, Visual Citation IoU, Abstention Precision/Recall, False Answer Rate, Unauthorized Retrieval Rate
System: P50/P95 latency, pages/sec, GPU time/query, storage/page, cost/query, failure rate
~~~

## Hard-case suite

这些用例是测试协议，不是实验结果。每条用例必须绑定 query_id、failure_type、gold_answer、required_facts、gold_documents、gold_pages、gold_blocks；涉及计算时还要绑定 calculation_program。

| ID | 场景 | 要证明的能力 | 最小判定 |
| --- | --- | --- | --- |
| H1 | 三页连续表格，表头在第一页、目标 row 在第三页，有 merged cells 和单位 | 跨页结构恢复 | 正确 row/column/unit/cell 被定位 |
| H2 | 答案只在图中，OCR 文本不能直接回答 | native visual retrieval | visual channel 找到正确页/region |
| H3 | 同一 metric 出现 20 次，只有一个匹配 year/model/region | hard-negative ranking | 正确指标进入 top-k |
| H4 | 旧版与新版冲突，旧版相似度更高 | version/freshness | 当前有效版本胜出或明确冲突 |
| H5 | 三个页面共同支持一个答案 | evidence completeness | coverage gate 不因单页命中而生成 |
| H6 | 正文 general rule，脚注 exception | footnote linkage | 输出 exception，不能只引用正文 |
| H7 | table 给数值、figure 给类别、正文给定义 | cross-modality planning | 三种 evidence 都在 trace |
| H8 | 问题合理但 corpus 没有答案 | abstention | 不产生 unsupported factual answer |
| H9 | 两个 source 冲突 | conflict detection | 冲突可见，不静默择一 |
| H10 | page 正确但 row/figure/bbox 错 | fine-grained citation | page 对但 region 错仍失败 |
| H11 | 同一 query 给两个 ACL 不同用户 | retrieval-time authorization | unauthorized evidence = 0 |
| H12 | parser/re-ingestion 变化导致召回下降 | regression gate | 同 manifest 输出 delta 并阻止 promotion |

## First executable slice

1. ICBCBench public objective questions：完成 schema/count audit。
2. FinRAGBench-V：下载一个可用语言/任务切片，核对 corpus-query-qrels/images 闭环。
3. HSBC：选一份版本固定的 Annual Report + 一份 Data Pack，人工标注 3–5 个跨页/跨文档问题。
4. B0：只用 text/dense 或现有轻量 baseline，生成 run file。
5. B1：加入 lexical/BM25 + rerank，生成对照 run file。
6. 先测 retrieval/evidence，再接 generation；不要先用 LLM judge 掩盖召回问题。

## Current blockers

- FinRAGBench-V 完整 corpus 不在 Git clone 中。2026-09-13 对 Hugging Face dataset tree manifest 的只读统计为 43 个文件、约 188.31 GB：corpus 约 181.70 GB，`pdfs_for_QA` 约 6.56 GB，citation labels 约 49 MB；不能在未确认磁盘、数据许可证和可用切片前下载全量。当前 manifest 还只列出 `qrels_ch.tsv`，queries/英文 qrels 的闭环需进一步核对数据分发方式。
- ICBCBench metrics.py 默认直接读取 judged-results 目录；需要准备预测/判分产物或单独调用纯函数。
- 当前工作区没有统一 .venv 或项目代码；候选仓库各自依赖不可混装。
- 视觉模型、外部 judge 和金融数据下载可能产生费用或大量资源消耗；正式 API execution 不由本阶段静态审计隐式授权。

## First MiniBench run

已建立并运行 30 题固定开发切片，包含 19 条 evidence、text factual、financial hard negative、table、visual-caption、cross-page/multi-evidence、cross-modality 和 1 条 unanswerable case。最新 run 目录由 CLI 自动生成，包含 5 类产物；B0/B1/B2 有实际检索与 coverage 数值，B3 为 `N/A`。

该切片用于代码回归和 failure debugging，不替代 FinRAGBench-V 或 ICBCBench。下一步只有在 real slice 的数据许可、文件闭环和 gold evidence 经过 D0/D1 后，才可把结果写成公开 benchmark 结果。

## P0-B/P0-C development suites

为验证“证据集合完整性”和“金融 hard-negative 排序”两个结论，新增两个独立、带 hash manifest 的 development suite：

- `EvidenceCompleteness-v1`：30 条 multi-fact cases；每个 fact 有 `fact_id`、描述和 acceptable evidence IDs，runner 保存每轮 targeted query、retrieved IDs、covered/missing facts 与最终 coverage。
- `FinanceHardSet-v1`：100 条 cases，十类混淆各 10 条。它是受控开发夹具，不是公开金融 benchmark；它用于验证 evaluator、排序 adapter 和 regression artifact 是否能把 temporal/metric/entity 等错误显式测出来。

最新稳定 run：`finevidence/artifacts/p0_bc_runs/20260912T193620598730Z-7739efd4/`；同配置复现 run：`finevidence/artifacts/p0_bc_runs/20260912T193744723802Z-f7209d8d/`。两次的 ranking/sufficiency tables 相同，run IDs 不同。MiniBench-v1 evidence/questions/manifest hash 仍分别为 `a297eff5...`、`19c1b546...`、`60d281b2...`，未被新 suite 改写。

## Sources

- https://github.com/DeepFin-Intelligence/ICBCBench/blob/main/README.md
- https://github.com/zhaosuifeng/FinRAGBench-V/blob/main/README.md
- https://huggingface.co/datasets/zhaosuifeng/FinRAGBench-V
- https://huggingface.co/blog/QuentinJG/introducing-vidore-v3
- https://arxiv.org/abs/2601.08620
- https://www.hsbc.com/investors/results-and-announcements/annual-report

## P0-D RealFinance-v1

已完成从 controlled fixture 到 public real-finance derived slice 的切换。来源仓库为 [TAT-QA](https://github.com/NExTplusplus/tat-qa) 和 [FinQA](https://github.com/czyssrs/FinQA)；TAT-QA 官方仓库说明其数据包含真实财报的 table/text hybrid questions，FinQA 官方仓库保留 `gold_inds`、`program`、`exe_ans`，并记录过 table row formatting label-leakage 修复。

当前派生切片固定为 50 条 TAT-QA `table-text` dev cases + 50 条 FinQA answerable dev cases，共 100 cases、1,652 Evidence IR items。manifest 保存：

- TAT-QA commit `870accc41953dcde885aabeb963d94aabdc0fbc3`，dev raw SHA-256 `6c3660345bf155b44bb3b55e63a4355716521028f291263d47c66667335f0144`。
- FinQA commit `0f16e2867befa6840783e58be38c9efb9229d742`，dev raw SHA-256 `27cc6c57487bbaba73041f93dba831a39b1cabe999c2ec0ddebc6f1200ff85bd`。

首个真实切片结果不是漂亮的 0/1：Dense/Hybrid Recall@5=`0.0900/0.1417`，gold-fact Initial CER=`0.0300`，两轮 targeted retrieval 后 Final CER=`0.8900`，Recovery=`0.8866`，仍有 11 条 failure cases。Required Fact Recall=`0.0017`，证明 question→required facts 是当前更大的瓶颈；facet extraction 与 gold-facet ranking 因数据缺少 canonical labels 保持 `N/A`。

HSBC naturally-occurring hard-negative gate 仍为 `N/A`，原因 `LOCAL_PROVENANCE_SOURCE_MISSING`。在获得许可的 HSBC corpus 前，不创建人工伪装的 HSBC-Stress-v1，也不进入 FinRAGBench-V 全量下载或 B3。

P0-D 最终 provenance：实验代码提交 `d97557d624b7dbe99ef6bff28acc057401d966a4`；两个最终复现 run 为 `finevidence/artifacts/p0_d_runs/20260912T202547160764Z-62a4fd11/` 与 `finevidence/artifacts/p0_d_runs/20260912T202612338140Z-c2f60731/`。两次 run 的 metrics 与 dataset manifest 内容一致，各含 100 条 trace、11 条 failure cases；Top-K FAER=`0.1200`，Coverage Gate/Targeted Retrieval FAER=`0.0000`。

## P0-E Required Fact Understanding

P0-E 在 RealFinance-v1 上比较 D0 Heuristic、D1 LLM Direct、D2 Schema-constrained、D3 Evidence-aware，并将 fact detection、critical recall、slot accuracy、CER、Recovery、FAER、Oracle Gap 分开保存。Gold evidence condition 为 Initial CER=`0.0500`、Final CER=`0.8900`、Recovery=`0.8842`、FAER=`0.0000`；D0 Fact Recall=`0.0017`，D2/D3=`0.0033`。由于公开源没有 canonical structured gold slots，Critical Fact Recall 和 Slot Accuracy 为 `N/A`。

D3 predicted CER=`1.0000` 高于 gold CER，造成 Oracle Gap=`-0.1100`；runner 已将其标记为 predicted fact set 未校准，不能写成效果提升。D1 因没有授权 LLM provider 为 `N/A`。最终 run 为 `finevidence/artifacts/p0_e_runs/20260912T205940827353Z-bc0c3c06/` 与 `finevidence/artifacts/p0_e_runs/20260912T210052094393Z-edbc1aa9/`，代码提交 `ea7876b4caad8aca9dee22fbb106a60a55bb14e7`，两次 metrics/manifest 一致。

P0-F 只建立官方 HSBC FY2025 Annual Report/Pillar 3 manifest 和本地 opt-in fetcher，不在仓库重新发布 PDF；当前没有本地 corpus，因此 naturally-occurring HSBC stress metric 仍为 `N/A`。B3 visual 继续保持 gate blocked。

## P0-G Evidence Requirement Graph & Fact–Evidence Alignment

P0-G 将“搜到一个相关 evidence”与“已经满足回答所需 evidence set”严格分开。新增 `Requirement` schema、依赖 DAG、Fact–Evidence Alignment、独立复用策略和 Critical Fact Gate；derived fact 通过 dependencies 合法推导，explanatory fact 不接受纯数值 evidence 冒充。`Independent CER` 要求所有 critical requirements 由有效、角色正确且独立的 evidence 或 derivation 支持。

在冻结的 RealFinance-v1 public benchmark slice（100 cases，50 TAT-QA + 50 FinQA）上，Gold Independent CER=`0.9083`。D3 的 Raw Self Coverage=`1.0000`，但 Independent CER=`0.7283`、Critical Coverage=`0.7400`、Invalid Reuse Rate=`0.4100`、FAER=`0.4100`；这验证了 P0-G 能阻断 P0-E 暴露的 reuse inflation。D4 当前 Independent CER=`0.5033`、Critical Coverage=`0.5050`，未证明 requirement understanding 提升。

`RequirementGold-v1` 因没有人工标注闭环保持 `N/A`，0 cases；因此 canonical Slot Accuracy/Critical Fact Recall 不填伪值。P0-G 的 H1/H2 等视觉 hard cases、citation bbox、ACL、版本冲突和多模态跨页验证仍未执行，B3 继续 blocked。正式结果与两次逐文件 SHA-256 一致的复现记录见 `finevidence/reports/p0-g-evidence-requirement-graph.md`。

## P0-H：RequirementAdjudicated-v1 与 HSBCNaturalHard-v1

P0-H 在不修改 `RealFinance-v1` 的前提下建立了 36-case `RequirementAdjudicated-v1`：factual 10、comparison 4、numerical 18、trend 3、explanation 1。它使用 source evidence/gold answer/program 约束的双 pass model-assisted adjudication，记录 A/B agreement、one-to-one matching、fact type/role/criticality/dependency 和 evidence mapping。`human_verified=false`，所以不能称为 human gold；它不是 TAT-QA/FinQA 官方 canonical requirement set。

最终正式 run 为 `finevidence/artifacts/p0_h_runs/20260913T004424445930Z/` 和 `finevidence/artifacts/p0_h_runs/20260913T005105288692Z/`，commit `95885590e2b5d49fb61a8c448e4df4ae46142004`，所有核心 JSON/JSONL 产物 byte-identical。D1 真实本地 Transformers 尝试 36/36 `MALFORMED_LLM_JSON`，保留为 N/A；D4 Req Precision/Recall=`0.7222/0.7222`，Independent CER=`0.3704`，Critical Coverage=`0.3750`，Invalid Reuse Rate=`0.5000`；Raw Self Coverage=`0.5185`，reuse inflation 仍可观测。该 D4 数字受到 annotation template overlap 限制，不宣称 human-gold 泛化。

HSBC provenance 已从 URL-only 变为两个官方 FY2025 PDF 的本地固定 manifest：Annual Report 372 pages / SHA `94aab2f5c83d1060ee95d344f1915833869fe4502dc635e4ab9ca84f496ee94b`；Pillar 3 122 pages / SHA `eb64c8f0fcd32648512979886bceddba7128558761c07948b50f6ecfa83a32f7`。PDF 仍被 `.gitignore` 排除。页面解析产生 492 page evidence items，挖取后通过真实 block provenance、positive/negative facet conflict、双 pass adjudication 形成 59-case `HSBCNaturalHard-v1`；这是 project-created stress set，不是 HSBC official benchmark。

| System | Recall@5 | MRR | nDCG@10 | HN Error | Top-1 Positive |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dense | 0.1864 | 0.1312 | 0.1290 | 0.3898 | 0.0847 |
| Hybrid + Generic | 0.2881 | 0.2322 | 0.3364 | 0.3898 | 0.0847 |
| + Predicted Facets | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |
| + Adjudicated Facets | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |
| + Financial-aware deterministic reranker | 0.9661 | 0.7759 | 0.8313 | 0.0339 | 0.6441 |

Facet accuracy（当前真实存在的 slots）为 entity/metric/period/basis/geography=`1.0000`，currency/segment/period_type 因本 set 无可评估 gold slots 为 `N/A`；Ranking Oracle Gap=`0.0000`。P0-H B3 gate=`READY`：RequirementAdjudicated-v1、Independent Coverage validation、固定 HSBC provenance、59 个有效自然 hard cases 和 failure localization 均满足。B3 本轮只解除为 READY，仍未实施 Visual Retrieval；H1–H12 中的视觉、bbox、ACL、版本冲突、unanswerable 和 regression 仍需后续独立实验。
## B3 visual evidence track

`HSBCVisualStress-v1` contains 60 cases mined from actual pages of the official FY2025 Annual Report and Pillar 3 corpus, across ten visual/layout failure categories. Render provenance is in `finevidence/artifacts/hsbc_page_images/page_render_manifest.json`; case provenance is in `finevidence/benchmarks/hsbc_visual_stress_v1/manifest.json`. It is a project-created stress benchmark, not an HSBC-official benchmark, and is not human verified.

`FinRAGBench-V-Slice-v1` contains 100 fixed English query/qrels records. The page-image archive was not obtainable during B3, so no public benchmark score is claimed. The formal B3 report keeps this as a blocker and separates it from the executable HSBC result.
### B3.1 public benchmark and routing closure (2026-09-13)

The existing 100-query `FinRAGBench-V-Slice-v1` is pinned to revision `d0d65255c94e687caa81ac9da7758ed25ff046a5`. The official `huggingface_hub`/`hf_xet` single-file download was attempted with project-local cache and retained a zero-byte incomplete object after Xet and HTTP fallback attempts; page-image metrics remain `N/A`, and the full corpus was not downloaded.

HSBCVisualStress-v1 remains 60 real-page cases. `HSBCMultimodalRouting-v1` adds 30 balanced real-page cases. T1 is `Parsed Page Text`, not verified structured Table IR. Recovery is reported at @1/@5/@10; final B3 status remains `PARTIAL`. The detailed closure report is `finevidence/reports/b3-1-public-benchmark-evaluation-closure.md`.

### B3.2 Benchmark Integrity & Public Closure (2026-09-14)

B3.2 保留 B3.1 的 stress/routing 数据与结果。对 `HSBCVisualStress-v1` 固定抽取每类原始顺序前两条（20 cases），在读取 T0/V0 之前完成 selection manifest；逐例保存 gold page、source block、T0 @1/@5/@10/@50、overlap、mapping 和 query provenance。审计发现 60 cases 只有 10 个固定模板，positive page 由关键词命中选择；T0 @10=`0/60` 是可复现观察值，但不能当作无偏自然文本基线。固定 sample attribution 为 TABLE_STRUCTURE_LOSS 8、CHART_VISUAL_ONLY 8、PAGE_FRAGMENTATION 2、LAYOUT_DEPENDENCY 2。

新建独立 `HSBCNaturalMultimodal-v1`：80 条真实 HSBC 页面（Annual Report/Pillar 3 各 40），按语料页 hash 选择、排除 stress candidates，并在性能结果前冻结。Natural @10 Recall 为 T0=`0.5375`、T1 Parsed Page Text=`0.5875`、V0=`0.0750`、M1=`0.5625`。Verified Structured Table IR 仍为 `N/A`。

FinRAGBench-V revision/query/qrel/slice 全部冻结；B3.2 追加 WSL Ubuntu 官方 URL 断点传输尝试并保存响应头、进度与 blocker summary。2.38GB archive 未完成，未解压 partial file，也未运行 public page-image evaluator；public metrics 继续 `N/A`，B3=`PARTIAL`。详见 `finevidence/reports/b3-2-benchmark-integrity-public-closure.md`。

### B4 Structure-Preserving Evidence IR & Failure-Aware Escalation

B4 使用不改变的 `HSBCVisualStress-v1` 验证“先诊断 failure，再选择恢复路径”。E0 使用 gold failure category 仅作 oracle 上界；E1 只使用 question、初始 coverage 和 parser capability。新增 `TableIR`/`TableCell` 在 15 个真实 TAT-QA source tables 上达到 1.0000 raw round-trip、cell identity 和 row/column relation；caption、footnote、bbox 仍为 N/A。HSBC parser 没有 verified cell-level IR，不能把 Parsed Page Text 代称为结构化表格。

E1 route accuracy=`0.5000`，visual invocation=`0.5000`，Recall@10=`0.0833`；表格、图表、分页、layout 的逐类结果与 bad cases 保存在 `finevidence/artifacts/b4_runs/` 和 B4 report。FinRAGBench-V 的独立 corpus-layout 检查确认冻结 `corpus/en` 是 14 个大 gzip shard，仍未运行 public page-image score。B4 完成实验闭环，但不代表 B3 public closure 或 production readiness 已完成。

### B4.1 table-recovery track（2026-09-14）

B4.1 将真实 HSBC Annual Report PDF 页面 1–26 送入 geometry-assisted `pdfplumber` word/table-region extractor，并生成带 `document/page/table/row/column/bbox` provenance 的 TableIR。24 个 table-like regions（13 页）被接受；structure recoverable rate=`0.7418`，header path population=`0.7278`。这些是可审计的 IR/invariant 结果，不是 semantic table accuracy；没有 verified human TableIR gold 的字段继续记为 N/A。

T2 deterministic TableIR cell executor 在冻结 60-case `HSBCVisualStress-v1` 上与 T0/T1/V0/T2+Text 比较。T2 R@1/@5/@10=`0.0167/0.0833/0.0833`；在四类 table failure 的 @10 相对 T1 恢复 5/24 页面，critical qualification 恢复 4/24，regression=`0`。V0 @10=`0.1000`，T2+Text @10=`0.0833`，因此 benchmark 不支持“结构化或融合必然胜出”。表格语义、unit、merged header、cross-page 连续性仍未被证明。正式报告：`finevidence/reports/b4-1-real-financial-table-recovery.md`。
## Evidence Backend v1 boundary（2026-09-14）

实验 benchmark 与 backend API 保持分离。Backend 复用现有 Evidence IR、retrieval、alignment 和 coverage 语义，不新增 benchmark、不修改冻结数据集；`EvidenceObject` 的 document/page/hash/table identity 是外部 Agent 可消费的 provenance contract。完整 HTTP contract 见 `finevidence/docs/FIN_EVIDENCE_API_SPEC.md`。任何没有实际数据或 verified structure 的字段继续返回空值或 N/A，不以 API 可调用性替代实验结论。
