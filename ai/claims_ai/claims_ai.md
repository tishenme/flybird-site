# claims_ai

```text

背景：这是一个 clamis ai 项目，我们希望通过ai技术可以快速的把 clamis 中的非结构数据实现结构化
通过 policy number 匹配数据库的数据做出该 clami s是否可以通过不通过需要做出判断

聚焦于整个流程中的input 和output的流程设计
input 是 user 上传一堆 clamis documents 过去
每一个claims case 是一整个 pdf 里面一下6种数据
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

核心需求：

- 多文档类型（6 类）差异化处理
- OCR → NER → Rule Check 三阶段流水线
- Prompt 工程显式管理
- **文档类型粒度 + 全局粒度** 的双重版本控制
- 完整的 Pytest 测试体系
- Azure Function App 可部署架构
- 可扩展性与可维护性优化点

工程结构（含说明）

claims-ai-processor/
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # ← GitHub Actions: pytest + lint
│
├── config/
│   ├── global_versions.yaml           # ← 全局组件版本（OpenAI 模型、ADI 版本等）
│   ├── document_versions.yaml         # ← 每类文档的 prompt/rules 版本 + 必填字段
│   └── settings.py                    # ← 加载 YAML + 环境变量融合
│
├── document_processors/               # ← 【核心】每类文档专属处理逻辑
│   ├── __init__.py
│   ├── base_processor.py              # 抽象基类
│   │
│   ├── claim_form/
│   │   ├── v1/
│   │   │   ├── prompt.py
│   │   │   └── rules.py
│   │   └── v2/
│   │       ├── prompt.py
│   │       └── rules.py
│   │
│   ├── discharge/
│   │   └── v1/
│   │       ├── prompt.py
│   │       └── rules.py
│   │
│   ├── invoice/
│   │   ├── v1/
│   │   │   ├── prompt.py
│   │   │   └── rules.py
│   │   └── v2/
│   │       ├── prompt.py
│   │       └── rules.py
│   │
│   ├── receipt/
│   │   └── v1/
│   │       ├── prompt.py
│   │       └── rules.py
│   │
│   ├── payment_proof/
│   │   └── v1/
│   │       ├── prompt.py
│   │       └── rules.py
│   │
│   └── id_card/
│       └── v1/
│           ├── prompt.py
│           └── rules.py
│
├── ner_extractors/                    # ← NER 阶段：跨文档实体融合
│   ├── __init__.py
│   ├── base_ner.py
│   ├── v1/
│   │   ├── prompts.py
│   │   └── extractor.py               # 诊断标准化、签名验证等
│   └── v2/
│       ├── prompts.py
│       └── extractor.py
│
├── rule_engines/                      # ← 规则引擎：独立版本
│   ├── __init__.py
│   ├── base_rule_engine.py
│   ├── rules_2025_q3_v1.py
│   └── rules_2025_q4_v1.py
│
├── services/                          # ← 流水线调度
│   ├── ocr_service.py                 # 调用 document_processors
│   ├── ner_service.py                 # 调用 ner_extractors
│   └── rule_service.py                # 调用 rule_engines + DB
│
├── handlers/
│   └── claim_processor.py             # 端到端 orchestration
│
├── utils/
│   ├── azure_document_intelligence.py # 封装 ADI 调用
│   ├── openai_client.py               # 封装 OpenAI + prompt 注入
│   ├── db_client.py                   # 数据库连接（policy 查询）
│   └── pdf_utils.py                   # ZIP 解压、PDF 分类（可选）
│
├── schemas/                           # ← Pydantic 模型（用于校验）
│   ├── ocr_output.py
│   ├── ner_output.py
│   ├── rule_output.py
│   └── claim_result.py                # 最终输出模型
│
├── tests/
│   ├── conftest.py                    # 全局 fixture + mock
│   │
│   ├── unit/
│   │   ├── test_ocr_service.py
│   │   ├── test_ner_service.py
│   │   ├── test_rule_service.py
│   │   └── document_processors/       # ← 每类文档独立测试
│   │       ├── test_claim_form_v2.py
│   │       ├── test_invoice_v2.py
│   │       └── ...
│   │
│   └── integration/
│       └── test_end_to_end.py         # 模拟完整 claim 流程
│
├── main.py                            # Azure Function 入口
├── host.json                          # Function App 配置
├── function.json                      # Trigger 配置
├── requirements.txt
├── requirements-test.txt              # ← 测试依赖
└── README.md

现在这个结构没有解决 我是收到一个 azure storage 的目录位置 我需要拿到这个目录下面的每一个 clamins pdf 文件,
需要对一个 pdf 里面的内容进行分类处理 判断出是哪种文档类型 然后按照文档类型进行不同的处理最后输出一个总的 json 交给下一环节 ner 处理
比如 ocr 每个不同文档的处理 需要逻辑不同 而且需要迭代 这里设计简单点 调用不同版本的 ptyhon 代码即可 灵活性高
明确每个环节的 iuput 和 output 类容

```
