# Existing System Gap Analysis

> 更新时间：2026-09-13
>
> 审计方式：公开仓库源码、README、仓库内测试/报告和最小命令检查。
>
> 候选仓库是研究对象，不是本项目依赖；仓库 README 或历史报告中的“已完成”不等于本次验证结果。

## Checkout manifest

| Repository | Local path | Branch | Verified HEAD | License metadata |
| --- | --- | --- | --- | --- |
| RAGFlow | research/repos/ragflow | main | 1f5d33333a3ff67fda2aa302c843699e994453e3 | Apache-2.0 |
| RAG-Anything | research/repos/RAG-Anything | main | 0ef67b4d476b66407a03a39e5b17e756fc0aef29 | MIT |
| Microsoft ColPali accelerator | research/repos/multi-modal-rag-with-colpali | main | 4e05aa3878c9e157e78210b2453b7e0de4164fd3 | MIT |
| AIEduRAG / StuckToShip | research/repos/AIEduRAG | main | bb913bf73d980e644b868f31d26ff8940d086ee5 | 未声明 |
| Financial Asset QA System | research/repos/Financial_Asset_QA_System | master | 433eb2a9c51104fb00f43f238fd359a91b55ed4b | MIT |
| SalesBoost | research/repos/SalesBoost | main | 40cb7450490b5145c470720e935a267f533d851a | MIT |
| ICBCBench | research/repos/ICBCBench | main | 4bca06f4201f0d4b2a57da2bbba49eb9d85c4699 | MIT |
| FinRAGBench-V | research/repos/FinRAGBench-V | main | 4de6374bb97aaca1ceff5e0463934860778ae557 | Apache-2.0 |

HEAD、分支和工作树状态由 git rev-parse HEAD、git branch --show-current、git status --porcelain 独立读取。CodeGraph 索引按仓库建立；.codegraph 是本次审计工具产物，不属于候选系统功能。

## 对照表

| 系统 | 已有能力（源码证据） | 已发现边界 | 对 FinEvidence 的价值 |
| --- | --- | --- | --- |
| RAGFlow | 文档解析、keyword/vector retrieval、rerank、metadata filter、citation、agent retrieval、MCP/API、多租户相关代码 | 规模和复杂度很高；存在大量开放 issue；必须按具体 failure 做最小复现 | 借鉴检索参数、chunk/page metadata 和 API 形状，不直接 fork 全平台 |
| RAG-Anything | PDF/Office/图片/表格/公式处理、multimodal query；仓库维护 OCR/layout/table/image-caption/retrieval-bias/slow-stuck 检查表 | 文档承认 flattened table 可能丢结构、图像路径跨机器失效、视觉阶段可能未运行；Discussion #174 仍展示表格行列混淆 | 借鉴解析适配和失败分类；保留原页与结构化结果 |
| Microsoft ColPali | Blob → Event Grid → Service Bus → processor → page image → ColQwen/vLLM → Qdrant → agent API/UI | README 明确是 accelerator/demo 且非 production-ready | 作为视觉检索通道候选和部署边界参考 |
| AIEduRAG | direct/multi-query/decomposition/retry；rerank、retrieval gate、retry、synthesis；测试包含 ACL、prompt injection、abstain、retrieval metrics | 面向课程/代码资料，不是金融/多模态；没有项目级 table cell、bbox、版本 lineage contract | 借鉴 gate、retry、拒答、trace 和测试组织 |
| Financial Asset QA System | Chroma vector、可选 BM25/RRF、BGE reranker、citation validator、grounded pipeline、规则 QueryRouter | 仓库内代码审查明确：BM25 需显式 build，默认退化为纯向量+rereanker；ResponseGuard 实际只要求至少一个数字与工具数字集合相交 | 作为金融文本 baseline 与反例，必须重新定义 Evidence IR |
| SalesBoost | tenant middleware、RAG 3.0 测试、small-to-big、BGE-M3 dense+sparse、HyDE、Self-RAG、RAGAS、integration/performance tests | 功能面很宽，未证明金融文档、视觉证据、cell citation 或严格 grounding | 借鉴 tenant 隔离及质量/延迟测试，避免把 agent framework 当亮点 |
| ICBCBench | objective accuracy/calibration；subjective FACT citation/source authority/time decay；公开 80 objective + 40 subjective questions | metrics 依赖 judged result；不直接提供 page/block/cell visual evidence coverage | 用于金融 end-to-end 和 source quality；补充 evidence trace |
| FinRAGBench-V | RGenCite baseline、retrieval/generation/eval 代码；README 描述金融页级视觉检索和 page/block citation | Git clone 不含完整 corpus；citation evaluator 使用外部 GPT-4o，API 是占位 | 用于视觉 retrieval + citation 主 benchmark |

## 最小验证结果

### AIEduRAG

命令：

~~~powershell
cd research/repos/AIEduRAG
python -m pytest test -q
~~~

结果：146 passed, 7 warnings，约 75 秒。证明当前本地测试集可运行，不证明金融、多模态或真实生产效果。

### Financial Asset QA System

完整测试收集失败，首要缺失依赖包括 fredapi、sse_starlette、jieba。局部命令：

~~~powershell
cd research/repos/Financial_Asset_QA_System/backend
python -m pytest tests/test_citation_validator.py tests/test_bm25_tokenizer.py tests/test_rag_chunking.py -q -o addopts=
~~~

结果：10 passed, 2 failed。两个失败来自 jieba 缺失后的 simple tokenization 退化，中文词和英文 ticker 未按测试预期保留。没有修复候选仓库。

### RAG-Anything / ColPali / FinRAGBench-V

- RAG-Anything 和 Microsoft ColPali accelerator 通过 python -m compileall -q .。
- FinRAGBench-V 源码通过 compileall；代码仓库未包含完整 benchmark corpus，未声称跑出检索或生成指标。
- ICBCBench 的 metrics.py --help 并非纯 help 入口，当前没有 judged result，因此以 FileNotFoundError 结束。这是工具前置状态，不是 benchmark 分数。

### Financial Asset QA System：最小本地检索基线

命令：

~~~powershell
cd research/repos/Financial_Asset_QA_System/backend
..\\.venv\\Scripts\\python.exe run_rag_audit.py
~~~

使用候选仓库随附的本地金融 Markdown/HTML/JSON 材料，不调用外部行情 API 或 LLM。三条探针均返回 3 个结果：

- `什么是市盈率`：top-1 是 `valuation_metrics.md`，但 top-1/top-2 为同一来源的重复内容。
- `收入和净利润的区别是什么`：top-1 是 2019 年教材的版权/书目信息页，而不是定义内容。
- `什么是可转债的强赎条款`：top-1 同样是该教材的书目信息页；更接近主题的章节只排到后面。

这是本项目当前真正跑出的候选基线观察，不是公开 benchmark 分数：文件级本地词面检索在重复文档、前置元数据和细粒度证据定位上存在明显 precision 风险；因此后续必须保留 page/block/cell 身份并报告去重、证据定位和 hard-negative 排序，而不能只报告“返回了结果”。

### 新增生产 issue 证据

- RAGFlow #15962：显式 `parser_config` 的 `None` 默认值与 table parser 的合并逻辑组合后，CSV/Excel table chunking 可在提取记录后失败；这是“解析链路没有给出可诊断错误”的可复现缺口，不是模型能力问题。
- RAGFlow #14768 / #15456：报告了跨租户参数或 agent id 校验不足导致元数据/agent 配置访问风险。它们说明 ACL 必须在候选集和对象加载入口处执行，不能把 post-filter 当成完整边界。
- RAG-Anything Discussion #174：表格问答仍有行列混淆、跨行拼接和表外数值幻觉报告；仓库自己的 failure checklist 也承认 flattened table 不保证精确结构。

## 结论

没有一个候选仓库可以直接作为 FinEvidence 的完整答案。RAGFlow/RAG-Anything 解决了通用基础设施和多模态路径；AIEduRAG 的 gate/retry/trace 测试最适合作为控制流参考；Financial Asset QA System 最适合作为金融文本 baseline 与“声明超过实现”的反例；ColPali accelerator 是视觉检索通道候选，不是银行级治理方案；ICBCBench 与 FinRAGBench-V 互补，不能混成一个指标。
