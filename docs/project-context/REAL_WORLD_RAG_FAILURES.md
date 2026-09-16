# Real-World RAG Failure Taxonomy

> 阶段：Phase 1 research
>
> 更新时间：2026-09-13
>
> 状态：第一版证据库。Observed 是来源或代码直接支持的观察；Inference 是工程推断；Open 尚未完成验证。

## 结论先行

生产 RAG 的高风险故障不是模型 API 报错，而是系统在“看起来成功”的情况下返回了错误、过时、不完整、不可审计或未授权的证据。当前最值得做的窄问题是：

1. 保留金融表格、图表和页面布局关系，避免 silent parsing corruption。
2. 判断问题所需的 evidence set 是否完整，并在不完整时拒答或明确部分回答。
3. 用金融指标、年份、实体和版本构造 hard negatives，验证排序而不是只验证“有相似内容”。

## Failure register

| ID | Failure | 真实来源/观察 | 用户损失 | 现有方案 | 当前缺口 | 验证方式 |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | Silent OCR/layout corruption | RAG-Anything failure checklist 直接列出错误数字、混列、OCR 把 l/1 混淆 | 错误事实进入索引，后续链路可能全部显示成功 | MinerU/Docling、人工抽查 Markdown/content list | 没有统一 ingestion integrity gate 证明解析仍忠于原页 | 页完整性、表格结构、bbox、数值关系检查 |
| F2 | Table row/column mixing | RAG-Anything Discussion #174 的用户报告部分 row 正确、部分 row 取错列、混合不同 row，并曾出现表外幻觉值；RAGFlow #15962 还显示显式 parser_config 可能使 CSV/Excel table chunking 在提取后失败 | 财务/规格数值错误，可直接导致错误决策；失败若只显示空泛错误也难定位 | OCR/Markdown 表格 + LLM、table parser | flatten text 不保证 row、column、unit、footnote 身份；解析失败也可能缺少可诊断错误 | cell-level gold；测 row/column/cell accuracy；记录 parser integrity 和可诊断失败 |
| F3 | Visual evidence ignored | RAG-Anything 将“答案需要图或表但 text chunks 排名更高”列为故障模式 | 图表趋势、连接关系、部件位置无法从 OCR 恢复 | 文字检索、图像处理、VLM/ColPali | 没有按 query modality 的对照实验 | text-only vs visual-only vs hybrid |
| F4 | Evidence incomplete across pages/documents | 项目总任务与 ICBCBench 都指向多源金融问题；现有工具把答案、检索和引用分开评估 | 模型根据部分证据作出看似合理但不完整的结论 | Top-K、多查询、agentic search | “命中一段相关文本”不等于 required evidence set 完整 | required facts、coverage、missing-fact detection、retry recovery |
| F5 | Wrong version/freshness | 项目总任务提出新旧披露冲突；Azure 官方文档明确指出权限元数据存在 freshness/reindex 限制 | 使用过时指标、政策或限制值 | metadata filter、时间字段、人工规则 | 需要 effective date、superseded lineage 和可复现实验 | 多版本同指标 corpus；测 stale-hit rate |
| F6 | Citation exists but does not support claim | FinRAGBench-V 提供 page/block visual citation；本地 evaluator 用外部 VLM 检查页面/bbox/crop 是否覆盖答案 | “有引用”增加错误答案的可信度，但无法审计 | page-level citation、视觉 crop/bbox | 需要 claim → evidence → page → region/cell 映射 | claim support、page/block/cell accuracy、bbox IoU |
| F7 | Permission leakage/post-filtering | Azure 官方文档要求 permission metadata 在索引中并在 query time enforce；RAGFlow #14768 报告 owner_ids 未验证造成跨租户聊天元数据泄漏，#15456 报告跨租户 agent IDOR | 未授权内容进入候选集、上下文或排序侧信道；跨租户配置/元数据泄漏 | ACL/security filter | 本项目尚未实现或验证；“检索后再过滤”已经太晚 | 同 query/不同 identity；Unauthorized Retrieval Rate = 0；候选集与最终 context 都做授权断言 |
| F8 | Abstention failure | 项目总任务要求 answerable/partial/ambiguous/conflicting/unanswerable 分层 | 相关但无答案的上下文被拼成自信答案 | confidence threshold、拒答 prompt | 相关性分数不能证明证据充足 | abstention precision/recall、false answer rate |
| F9 | Retrieval regression is silent | 项目总任务要求 parser/OCR/embedding/chunk/reranker 变化后 regression；候选 benchmark 有评估入口 | 线上质量悄悄下降，直到用户发现 | 离线 benchmark、人工 spot check | 缺少固定 manifest、promotion gate 和失败归因 | 同 manifest 比较 retrieval/answer/citation/latency delta |
| F10 | Multimodal cost/latency explosion | Microsoft ColPali 仓库明确声明 accelerator/demo、不是 production-ready，架构包含 GPU、队列、对象存储和 Qdrant | 全量视觉处理增加索引、存储、GPU、查询成本 | page image + late-interaction embedding | 缺少 query-class cascade/cost gate | pages/sec、GPU time、storage、P50/P95、cost/query |

## 证据边界

- F1–F3 有公开项目文档或讨论直接支持。
- F4、F8、F9 是由项目目标和 benchmark 能力支持的设计风险，尚不是本项目实验结果。
- F5 的“旧版本相似度更高”目前是待验证假设，不能写成已发生的生产事故。
- F7 的 query-time enforcement 是官方平台建议；本项目尚未证明候选仓库满足它。
- F10 是官方 accelerator 自己声明的部署边界，不能据此推导具体性能数字。

## 来源

- https://github.com/HKUDS/RAG-Anything/blob/main/docs/multimodal_rag_failure_modes.md
- https://github.com/HKUDS/RAG-Anything/discussions/174
- https://github.com/infiniflow/ragflow/issues/15962
- https://github.com/infiniflow/ragflow/issues/14768
- https://github.com/infiniflow/ragflow/issues/15456
- https://github.com/microsoft/multi-modal-rag-with-colpali
- https://learn.microsoft.com/en-us/azure/search/search-query-access-control-rbac-enforcement
- https://learn.microsoft.com/en-us/azure/search/search-security-best-practices
- https://docs.aws.amazon.com/prescriptive-guidance/latest/retrieval-augmented-generation-options/what-is-rag.html
- https://github.com/DeepFin-Intelligence/ICBCBench
- https://github.com/zhaosuifeng/FinRAGBench-V
- https://huggingface.co/blog/QuentinJG/introducing-vidore-v3
