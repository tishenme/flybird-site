# claims_ai

```text

背景：这是一个 clamis ai 项目，我们希望通过ai技术可以快速的把 clamis 中的非结构数据实现结构化
通过 policy number 匹配数据库的数据做出该 clami s是否可以通过不通过需要做出判断

聚焦于整个流程中的input 和output的流程设计
input 是 user 上传一堆 clamis documents 过去
每一个claims case 是一个 pdf 里面一下6种数据
claims form, Discharge document, Invoice / Bill, Receipt, Payment Proof, ID Card

我们设计有3个output的环节按顺序来
1 OCR Process (通过 azure document intelligence 和 open ai 把每种数据都抽取单独的json出来最终输出一个总的j5.00）
2 NPR Process（需要对oCR 的结果中做一些复杂的识别比如诊断结果签名识别 具体来说增加一个json对象表述 NER的结果）
3 Rule Check Process(需要对NER的结果通过 policy number 匹配数据库的数据和一些规则判断该claima是否可以通过县体来说增加一个json对象表述 Rule Check 的结果）

使用的技术如下
1. Azure Storage
2. Azure Document Intelligence
3. Azure Open AI
4. Azure function app

现在我们需要设计一个 python 工程 这个python 代码后续可以快速搬到 function app 上

```

```text

十三、可扩展点
1.
多语言/多模型：NER 环节可再调一个 HuggingFace 模型，对比 OpenAI 置信度取高。
2.
人工复核：RuleResult.final_status=PENDING 时自动写队列，触发 Durable 外部事件，人工审核后把结果 push 回 Orchestrator。
3.
并行提速：一个 case 6 个 PDF，可在 OCR 环节用  yield context.task_all([...])  并行。
4.
灰度/AB：在 Rule Check 里加 Feature Flag，根据 policy_no 尾号切换新旧规则。
5.
计费与审计：中间 JSON 全部写 blob 带 SAS，前端可直接下载，作为审计凭证。
十四、下一步
1.
把 policy DB 的查询换成存储过程，减少往返。
2.
把 NER 提示词做成版本化模板存 blob，热更新。
3.
加 App Insights 自定义维度（case_id、policy_no），方便出报表。
4.
写 ARM/Bicep 一次性把 Function App、Storage、Doc Intel、VNets、私有终结点、Managed Identity、Key Vault 全拉起，做到“代码–基础设施”同库同源。
至此，一个可直接搬迁到 Azure Function App 的 Python 工程骨架就完成了。祝项目顺利上线！

```
