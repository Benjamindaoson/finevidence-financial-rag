# Production Multimodal RAG 项目总任务

你是这个项目的技术负责人。

不要从“应该使用什么框架、模型或架构”开始。

首先研究：

> **真实生产环境中的 RAG 到底在哪里失败。**

然后设计系统去解决其中最有价值、最困难、最能被客观验证的问题。

技术方案由你自行决定。

---

# 1. 项目的根本目标

我们不是为了证明：

> “我会做 RAG。”

这一点已经没有足够区分度。

我们真正希望证明：

> **当企业文档变得复杂、视觉化、跨页、冲突、过时、权限受限、证据不完整时，这套 RAG 仍然能够找到正确证据、知道自己不知道什么，并给出可验证、可审计的答案。**

最终项目必须能够回答：

```text
普通 RAG 在什么情况下失败？

为什么失败？

现有成熟系统解决到什么程度？

我们具体解决了什么？

解决以后提升了多少？

代价是什么？
```

---

# 2. 先研究真实 Pain，而不是直接开发

请主动搜索：

```text
GitHub issues
Reddit / Hacker News 工程实践
技术博客
企业案例
论文
benchmark
RAGFlow / Haystack / LlamaIndex / LangChain 等真实 issue
AWS / Azure / GCP / Databricks 等生产文档
```

不要只看 marketing README。

建立：

```text
REAL_WORLD_RAG_FAILURES.md
```

每一个 failure 至少记录：

```text
Failure
真实场景
真实来源
用户实际损失
为什么发生
现有方案
现有方案不足
我们是否值得解决
如何验证是否解决
```

---

# 3. 重点研究以下真实 Failure Surfaces

以下不是预设技术方案，而是必须调查的问题。

---

## Failure 1 — Silent Parsing Corruption

最危险的 parser failure 不是：

```text
ERROR
```

而是：

```text
解析成功
索引成功
检索成功
回答成功

但是事实已经被 parser 改坏。
```

例如：

```text
原 PDF：

             2024    2025
Revenue      100     130
Profit        20      18
```

被解析成：

```text
2024 2025 Revenue 100 130 Profit 20 18
```

此时所有系统都显示绿色。

但是：

```text
row
column
header
unit
relationship
```

已经丢失。

必须特别研究：

```text
multi-column PDF
merged cells
rowspan / colspan
borderless table
multi-page table
nested table
rotated page
scanned PDF
header / footer contamination
reading-order corruption
figure-caption separation
formula
footnote
```

我们需要知道：

> ingestion 后的 evidence 是否仍然忠于原文档？

而不仅仅是 parser 有没有报错。

---

# 4. Failure 2 — Table Looks Like Text but Is Not Text

企业中大量关键事实存在：

```text
financial tables
specification tables
maintenance tables
pricing tables
risk tables
Excel
```

传统：

```text
Table
→ flatten
→ embedding
```

可能根本不是正确抽象。

例如：

用户问：

```text
在 2025 年所有型号中，
满足压力 > X 且温度范围包含 Y 的最轻设备是哪一个？
```

这不是：

```text
semantic similarity
```

问题。

这是：

```text
filter
+
comparison
+
relation preservation
+
numeric reasoning
```

需要自行研究：

```text
表格是否应该 visual retrieve？
是否需要结构化 representation？
是否需要 SQL / dataframe execution？
什么时候用 text？
什么时候用 visual？
什么时候用 structured query？
```

不要提前假设答案。

---

# 5. Failure 3 — Correct Evidence Is Visual, OCR Text Is Misleading

例如技术手册：

```text
正文没有答案

答案存在于：

流程图
接线图
爆炸图
曲线
柱状图
机械结构图
页面空间关系
```

甚至 OCR 会得到大量文字，

但真正的问题是：

```text
哪个部件连接哪个部件？
哪根线对应哪个端口？
哪条曲线最高？
哪个区域代表故障位置？
```

这是视觉关系。

必须测试：

```text
text-only retrieval
vs
visual retrieval
vs
hybrid retrieval
```

并验证：

> Visual Retrieval 到底在哪类 query 上真正贡献提升？

而不是为了“Multimodal”这个标签使用 VLM。

---

# 6. Failure 4 — Retrieval Finds Some Evidence, But Not All Evidence

这是非常重要的一类失败。

例如问题：

```text
根据手册中的规格表和后面的安全说明，
这个设备是否允许在温度 X 下以压力 Y 工作？
```

可能需要：

```text
Page 37 → operating range
Page 94 → exception
Page 126 → safety warning
```

Retriever 找到了 Page 37。

LLM 根据 Page 37 合理推理。

答案看起来完全正常。

但是它是错的。

真正的问题不是：

```text
Recall@5 有没有找到一个 relevant chunk
```

而是：

> **完成这个问题所需的 Evidence Set 是否完整？**

因此需要研究：

```text
multi-hop retrieval
cross-page retrieval
cross-document retrieval
evidence coverage
iterative retrieval
query decomposition
missing-evidence detection
```

---

# 7. Failure 5 — Similarity Can Retrieve the Wrong Version

真实企业环境不是一个：

```text
document.pdf
```

而可能是：

```text
Safety_Manual_2023.pdf
Safety_Manual_2024.pdf
Safety_Manual_FINAL.pdf
Safety_Manual_FINAL_v2.pdf
Safety_Manual_revised.pdf
```

用户问：

```text
当前允许的最大压力是多少？
```

旧版写：

```text
80 PSI
```

新版写：

```text
55 PSI
```

旧版本文字与用户 query 的 embedding 可能反而更相似。

单纯 vector similarity：

```text
Old: 0.91
New: 0.87
```

然后系统自信回答：

```text
80 PSI
```

这是生产事故。

需要研究：

```text
document identity
version
effective date
superseded version
freshness
source lineage
update
delete
re-index
rollback
citation reproducibility
```

最终必须能够测试：

> **语义更相似但已经过期的文档，是否会击败当前有效文档？**

---

# 8. Failure 6 — Citation Exists but the Citation Is Wrong

“有 citation”不能算成功。

必须区分：

```text
答案正确？
文档正确？
页码正确？
证据块正确？
Bounding Box 正确？
引用区域真的支持这个 claim？
```

可能出现：

```text
正确 document
错误 page

正确 page
错误 table row

正确 row
错误 column

正确 answer
错误 evidence
```

这些全部应该算 failure。

最终应该能够做到：

```text
Answer
↓
Claim
↓
Evidence
↓
Document Version
↓
Page
↓
Region / Bounding Box
```

并且真正验证。

---

# 9. Failure 7 — Correct Answer Requires Resolving Conflicting Evidence

企业数据经常互相冲突。

例如：

```text
Manual A：55 PSI
Old FAQ：80 PSI
Sales PPT：60 PSI
Revised bulletin：55 PSI
```

传统 Top-K RAG 可能把四段全部塞给 LLM：

```text
Context 1
Context 2
Context 3
Context 4
```

然后让模型自行判断。

这不是可靠系统。

需要研究：

```text
authority
freshness
version
document type
source priority
conflict detection
conflict resolution
```

系统至少应该知道：

> Evidence 之间发生了冲突。

而不是偷偷选择一个答案。

---

# 10. Failure 8 — User Can Retrieve Evidence They Should Never See

例如公司知识库：

```text
普通员工
经理
HR
Finance
Legal
Executive
```

使用的是同一个 Vector DB。

如果：

```text
retrieve
→ Top K
→ 再检查权限
```

很可能已经产生：

```text
information leakage
ranking distortion
side-channel
```

需要研究真正的：

```text
tenant
document ACL
group ACL
security metadata
query-time authorization
permission propagation
permission update
```

必须设计一个测试：

```text
User A 问同一个问题
User B 问同一个问题
```

由于 ACL 不同：

```text
retrieved EvidenceSet 必须不同
```

Unauthorized evidence leakage：

```text
必须 = 0
```

---

# 11. Failure 9 — The Correct Answer Is “There Is Not Enough Evidence”

这是 RAG 最容易被忽略的问题。

给系统一个：

```text
90% related
但没有答案
```

的上下文。

LLM 很容易补出答案。

因此测试集必须包含：

```text
answerable
partially answerable
ambiguous
conflicting
unanswerable
```

系统不能只优化：

```text
Answer Accuracy
```

还必须优化：

```text
Abstention Accuracy
Evidence Sufficiency
False Answer Rate
```

我们希望系统拥有：

> **有证据才回答。**

而不是：

> **只要检索到相关内容就回答。**

---

# 12. Failure 10 — Long Document + Distractors

不要只测：

```text
10 页 PDF
问题答案就在明显标题下面
```

必须测试：

```text
100+
甚至数百页文档
```

其中存在很多近似内容：

```text
same component name
same metric
different year
different model
different revision
different region
different operating condition
```

Retriever 必须区分这些 hard negatives。

---

# 13. Failure 11 — One Query Requires Multiple Modalities

构造或寻找真实问题：

```text
文字定义术语
+
表格给数值
+
图片给部件位置
+
脚注给例外情况
```

最终问题只有综合四者才能回答。

例如：

```text
根据型号 X 的规格表、安装图和安全说明，
如果环境温度为 Y，
应该使用哪个接口，
最大允许压力是多少，
并指出接口在图中的位置。
```

这个问题同时需要：

```text
Text
Table
Image
Cross-page reasoning
Evidence grounding
```

---

# 14. Failure 12 — Retrieval Quality Regresses Silently

更换：

```text
OCR
Parser
Embedding
Chunking
Reranker
Vector DB
```

以后：

```text
系统仍然运行正常
```

但 Recall 可能下降。

因此任何核心组件改变都必须有：

```text
Regression Eval
```

不能：

```text
“感觉答案不错”
```

作为判断标准。

---

# 15. Failure 13 — Multimodal RAG Can Become Too Expensive

不要默认：

```text
所有页面
→ VLM
→ visual embedding
→ reranker
→ VLM generation
```

就是生产方案。

必须测：

```text
index cost
GPU memory
pages/sec
query latency
rerank latency
generation latency
storage
```

并研究：

```text
是否所有 query 都需要 visual retrieval？
是否所有 page 都需要 VLM？
是否可以 cascade？
是否可以 cheap retrieval → expensive verification？
```

生产系统最终要同时考虑：

```text
Quality
Latency
Cost
```

---

# 16. 我们真正希望形成的项目亮点

不要预先写：

```text
“实现了 ColQwen”
“使用了 RRF”
“使用了 Milvus”
```

这些不是亮点。

每一个亮点必须遵循：

```text
REAL FAILURE
      ↓
WHY EXISTING PIPELINE FAILS
      ↓
OUR DESIGN
      ↓
CONTROLLED EXPERIMENT
      ↓
MEASURED IMPROVEMENT
```

例如最终可能形成：

```text
Pain:
multi-page table 被 flatten 后数值关系错误

Solution:
XXX

Evidence:
Table QA accuracy
A → B
```

或者：

```text
Pain:
visual-only evidence 无法被 text retriever 找到

Solution:
XXX

Evidence:
Visual query Recall@5
A → B
```

但具体 Solution 由你研究以后决定。

---

# 17. 必须挑战系统的 Hard Cases

最终系统不能只展示简单 query。

请建立：

```text
HARD_CASE_SUITE
```

至少覆盖以下类型：

```text
H1
三页连续表格。
header 位于第一页，
目标 row 位于第三页，
存在 merged cells 和单位。

H2
答案只存在于图中。
OCR 文本不能直接回答。

H3
同一 metric 在文档中出现 20 次，
但只有一个满足正确 year + model + region。

H4
旧版文档与新版文档冲突，
旧版 embedding similarity 更高。

H5
答案需要三个不同页面共同支持。

H6
正文给 general rule，
footnote 给 exception。
只取正文会答错。

H7
Table 给数值，
Figure 给类别，
正文给定义。
缺任一 modality 都无法回答。

H8
问题看起来合理，
但 corpus 中实际上不存在答案。

H9
两个 sources 相互冲突。
系统必须检测冲突。

H10
citation page 正确，
但要求进一步定位到正确 row / figure / bbox。

H11
同一 query 给两个权限不同的用户，
EvidenceSet 必须不同。

H12
更换 parser 或重新 ingestion 后，
系统必须检测 retrieval regression。
```

尽量使用真实文档构造，而不是 synthetic toy examples。

---

# 18. Benchmark

主 Benchmark 保持两个领域：

```text
ViDoRe V3 Industrial
ViDoRe V3 Finance
```

目标是证明：

> **同一个核心 retrieval/evidence system，而不是两个领域特化系统，可以在完全不同的复杂文档领域工作。**

重点评估：

```text
Industrial
→ diagram
→ specification
→ maintenance
→ technical table
→ complex layout

Finance
→ annual report
→ financial table
→ chart
→ numerical evidence
→ long document
```

可以自行寻找额外 benchmark。

例如如果需要验证：

```text
cross-page
multi-hop
unanswerable
```

可以研究：

```text
MMLongBench-Doc / corrected variants
BRIDGE
其他当前 benchmark
```

但不要机械加入。

先明确：

> 它解决哪一个现有 benchmark 没覆盖的问题。

---

# 19. Evaluation 不只是一个 Recall

建立多层 Eval。

```text
Layer 0 — Ingestion Integrity

document completeness
page completeness
table structure preservation
layout preservation
bbox validity


Layer 1 — Retrieval

Recall@K
NDCG@K
MAP
MRR


Layer 2 — Evidence

Evidence Recall
Evidence Precision
Evidence Completeness
Cross-page Coverage


Layer 3 — Answer

Exact Match / F1 / Judge
Numerical Accuracy
Answer Groundedness


Layer 4 — Trust

Citation Accuracy
Page Accuracy
BBox / Region Accuracy
Abstention Accuracy
Conflict Detection Accuracy
Freshness / Version Accuracy
Unauthorized Evidence Leakage


Layer 5 — System

Index Throughput
Query Latency
GPU Memory
Storage
Cost
Failure Rate
```

最终不能出现：

```text
Answer Accuracy 很高
```

就宣布成功。

---

# 20. Failure Attribution

当一条问题失败时，必须知道：

```text
Parser 错？

Chunk 错？

Retriever 没召回？

Fusion 丢掉了？

Reranker 排错？

Evidence 不完整？

LLM 推理错？

Citation 错？

Version 错？

Permission 错？
```

系统必须保留足够 trace。

最终形成：

```text
FAILURE_TAXONOMY.md
```

这本身就是项目的重要技术成果。

---

# 21. 研究现有系统到底哪里不足

完整研究：

```text
RAGFlow
RAG-Anything
Microsoft multimodal-rag-with-colpali

AIEduRAG
Financial_Asset_QA_System
SalesBoost
```

完整 clone。

不要只读 README。

同时继续自行寻找：

```text
新的开源项目
论文实现
retrieval system
document parser
visual retriever
table RAG
evaluation framework
```

你的任务不是证明我们列出的仓库很好。

而是判断：

```text
What already works?

What actually fails?

What can be reused?

What should not be reused?

What still needs to be solved?
```

---

# 22. 不允许“为了不同而不同”

如果 RAGFlow 已经完美解决某个问题：

```text
直接使用。
```

如果某个开源库已经有最好的 parser：

```text
直接适配。
```

没有必要为了体现技术能力重新实现。

技术能力应该体现在：

> **发现真正未解决的问题，并解决它。**

而不是：

> **重复实现别人已经解决的问题。**

---

# 23. 技术路线由你决定

你可以：

```text
新建
Fork
重构内部项目
组合多个项目
做 adapter
抽取模块
重写部分核心
```

都可以。

不要因为之前讨论过某个方案就默认它正确。

请根据：

```text
真实 failure
benchmark
代码质量
license
复杂度
维护成本
performance
开发成本
面试价值
```

自己判断。

---

# 24. 面试价值

这个项目最终必须让我能够回答高级 RAG 面试问题。

例如：

```text
为什么你的 parser pipeline 这样设计？

如何验证 parser 没有悄悄破坏 table？

Visual Retrieval 在哪些 query 上有收益？

为什么不是所有 query 都走 VLM？

如何处理跨页 table？

怎么判断 retrieval evidence 已经足够？

如何处理新旧文档冲突？

删除一份文档以后如何保证旧 chunk 不再召回？

document ACL 在哪个阶段执行？

为什么 post-filter 权限可能有问题？

citation 怎样证明真的支持 claim？

如果模型答对但 evidence 错了算不算成功？

如何判断一次 regression 来自 retrieval 还是 generation？

100 万页怎么扩展？

GPU 花在哪里？

如何减少 multimodal retrieval cost？
```

如果做完项目仍然回答不了这些问题，

说明项目不够深入。

---

# 25. 第一阶段任务

先不要大规模写代码。

完成：

```text
1. 完整 clone 所有指定 repository

2. 搜索真实 production RAG pain points

3. 阅读相关 GitHub issues

4. 阅读近期 multimodal RAG / enterprise RAG benchmark

5. 下载并理解核心 benchmark

6. 对候选系统跑最小 baseline

7. 建立 Failure Taxonomy

8. 判断最值得解决的 3–5 个核心 failure
```

输出：

```text
REAL_WORLD_RAG_FAILURES.md

EXISTING_SYSTEM_GAP_ANALYSIS.md

PROJECT_STRATEGY.md

BENCHMARK_AND_HARD_CASE_PLAN.md
```

然后自行选择技术方案并开始开发。

不要让我替你决定：

```text
应该 Fork 谁
应该用什么 Vector DB
应该用什么 Retriever
应该用什么 Parser
```

这些属于你的工程研究任务。

---

# 26. 最终项目必须讲出一个简单的故事

最终 README 不应该只是：

```text
Supports:
✓ Hybrid RAG
✓ Multimodal
✓ Reranker
✓ GraphRAG
✓ Agent
```

这是 feature list。

我们最终真正需要的是：

> **普通 RAG 在复杂企业文档上会因为结构破坏、视觉证据遗漏、证据不完整、版本冲突和错误 grounding 而产生“看起来可信但实际上错误”的答案。这个系统专门针对这些 failure surfaces 设计，并通过真实工业与金融文档 benchmark、hard-case stress tests 和完整 evidence tracing 验证。**

最后必须用真实实验数据证明。

---

# 27. 最重要的开发原则

不要追逐技术名词。

永远按照：

```text
PAIN
↓
FAILURE
↓
ROOT CAUSE
↓
DESIGN
↓
EXPERIMENT
↓
EVIDENCE
```

工作。

没有明确 Pain 的 Feature：

```text
不要做。
```

没有 Baseline 的“优化”：

```text
不算优化。
```

没有真实测量的“提升”：

```text
不允许写进 README。
```

没有正确 Evidence 的答案：

```text
不算正确答案。
```