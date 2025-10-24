### USER

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

### ASSISTANT
你提出的结构已经非常清晰，现在我们来**聚焦于整个流程中每个环节的 input 和 output**，并补充缺失的「文档类型识别」环节，以实现从 Azure Storage 目录 → 多 PDF → 每个 PDF 内部多页 → 按页/文档类型分类 → 分别处理 → 聚合输出的完整 pipeline。

---

## ✅ 整体流程概览（端到端）

```
[Azure Storage Blob Directory]
        ↓ (1. 下载 ZIP/PDFs)
[Claim Case: 1 ZIP or 1+ PDFs]
        ↓ (2. PDF 分页 + 文档类型识别)
[Pages → Classified as: ClaimForm, Discharge, Invoice, ...]
        ↓ (3. OCR 阶段：按类型调用对应 processor)
[Per-document JSONs → Aggregated OCR Output]
        ↓ (4. NER 阶段：跨文档实体融合 + 标准化)
[NER Output JSON]
        ↓ (5. Rule Check：Policy 匹配 + 规则判断)
[Final Claim Result JSON]
```

---

## 🔍 各阶段 Input / Output 定义（含数据结构）

### 📥 **Stage 0: Input Trigger**
- **Input**:
  - Azure Function 触发器接收一个 **Blob Storage 目录路径**（例如 `claims/case_123/`）
  - 该目录包含 **1 个或多个 PDF 文件**（每个 PDF 可能包含多个文档类型，如一页是发票、一页是出院小结）
- **Output**:
  - 本地临时目录中的 PDF 文件列表（`List[Path]`）

> ✅ **实现位置**: `handlers/claim_processor.py` + `utils/pdf_utils.py`

---

### 📄 **Stage 1: Document Type Classification (新增环节)**

> ⚠️ 你当前结构缺少这一关键步骤：**如何知道 PDF 的某一页属于哪种文档类型？**

#### Input:
- 一个 PDF 文件（`Path`）
- 可选：ADI 的 layout/paragraph 输出（用于分类）

#### Output:
- `List[DocumentPage]`，其中：
  ```python
  class DocumentPage:
      page_number: int
      raw_text: str
      document_type: Literal["claim_form", "discharge", "invoice", "receipt", "payment_proof", "id_card"]
      confidence: float  # 可选
  ```

#### 实现建议：
- 使用 **轻量级分类器**（如基于关键词 + OpenAI prompt）：
  ```python
  classify_page_type(page_text: str) -> str
  ```
- 或者：在 OCR 阶段先用 ADI 提取文本，再分类（更准确但慢）

> ✅ **实现位置**: `utils/pdf_utils.py` 或新增 `document_classifiers/`

---

### 🖨️ **Stage 2: OCR Process**

#### Input:
- `List[DocumentPage]`（来自 Stage 1）
- 全局配置（`config/settings.py`）：决定使用哪个版本的 processor

#### Output:
- **Aggregated OCR JSON**（符合 `schemas/ocr_output.py`）：
  ```json
  {
    "claim_form": { ... },        // 来自 claim_form/v2/processor
    "discharge": { ... },
    "invoice": { ... },
    "receipt": null,              // 可能缺失
    "payment_proof": { ... },
    "id_card": { ... },
    "metadata": {
      "policy_number": "POL-2025-XXXX",
      "claim_id": "CLAIM-123",
      "ocr_version": "v2.1",
      "document_versions": {
        "claim_form": "v2",
        "invoice": "v2",
        ...
      }
    }
  }
  ```

#### 关键逻辑：
- 根据 `document_type` 路由到对应 `document_processors/<type>/vX/`
- 每个 processor 返回 Pydantic 模型（如 `ClaimFormOCR`）
- 聚合为统一结构

> ✅ **实现位置**: `services/ocr_service.py` + `document_processors/`

---

### 🔍 **Stage 3: NER Process**

#### Input:
- OCR Output JSON（上一阶段结果）
- NER 版本配置（如 `ner_v2`）

#### Output:
- **NER JSON**（`schemas/ner_output.py`）：
  ```json
  {
    "diagnosis_codes": ["I10", "E11.9"],
    "procedure_codes": ["99213"],
    "patient_name": "John Doe",
    "provider_signature_verified": true,
    "total_claimed_amount": 1250.00,
    "hospital_name": "City General Hospital",
    "ner_version": "v2"
  }
  ```

#### 关键逻辑：
- 跨文档字段融合（如发票金额 + 收据金额一致性检查）
- 标准化诊断（ICD-10）、机构名称归一化
- 签名存在性/有效性判断（基于文本或图像特征）

> ✅ **实现位置**: `services/ner_service.py` + `ner_extractors/v2/extractor.py`

---

### ⚖️ **Stage 4: Rule Check Process**

#### Input:
- NER Output JSON
- Policy Number（从 OCR 或 NER 中提取）
- 数据库连接（通过 `utils/db_client.py` 查询 policy 详情）

#### Output:
- **Rule Check JSON**（`schemas/rule_output.py`）：
  ```json
  {
    "policy_valid": true,
    "coverage_active": true,
    "diagnosis_covered": true,
    "amount_within_limit": false,
    "missing_documents": ["receipt"],
    "final_decision": "REJECTED",
    "rejection_reasons": ["Claim amount exceeds policy limit of $1000"],
    "rule_engine_version": "rules_2025_q4_v1"
  }
  ```

#### 关键逻辑：
- 查询 DB 获取 policy 的 coverage rules, limits, required docs
- 执行规则引擎（如：`if diagnosis in excluded_list → reject`）
- 汇总决策

> ✅ **实现位置**: `services/rule_service.py` + `rule_engines/rules_2025_q4_v1.py`

---

### 🎯 **Final Output: Claim Result**

#### Schema (`schemas/claim_result.py`):
```python
class ClaimResult(BaseModel):
    claim_id: str
    policy_number: str
    ocr: OCROutput
    ner: NEROutput
    rule_check: RuleCheckOutput
    overall_status: Literal["APPROVED", "REJECTED", "PENDING_REVIEW"]
    processing_timestamp: datetime
    pipeline_version: str  # e.g., "v2.1.0"
```

---

## 🧩 补充：版本控制机制

### 1. **全局版本** (`config/global_versions.yaml`)
```yaml
openai_model: "gpt-4o-2025-08-06"
azure_document_intelligence_version: "2024-02-29"
ner_version: "v2"
rule_engine: "rules_2025_q4_v1"
```

### 2. **文档级版本** (`config/document_versions.yaml`)
```yaml
claim_form:
  version: "v2"
  required: true
invoice:
  version: "v2"
  required: true
receipt:
  version: "v1"
  required: false
```

> ✅ 在 `ocr_service.py` 中动态加载对应版本的 processor

---

## 🧪 测试覆盖建议

| 测试层级 | 覆盖内容 |
|--------|--------|
| **Unit** | 每个 processor 的 prompt + rules 逻辑（mock OpenAI） |
| **Integration** | OCR → NER → Rule 的数据流（mock DB + ADI） |
| **E2E** | 上传 ZIP → 输出 ClaimResult（使用真实 PDF fixture） |

---

## 🚀 Azure Function 部署适配

- `main.py` 接收 blob trigger：
  ```python
  def main(blob: func.InputStream):
      claim_dir = blob.name  # e.g., "claims/case_123/"
      result = ClaimProcessor().process(claim_dir)
      upload_to_output_container(result)
  ```
- 使用 `tempfile.TemporaryDirectory()` 处理本地文件
- 所有 secrets 通过 `os.getenv()` 从 Function App 配置读取

---

## ✅ 总结：各阶段 I/O 明确化

| 阶段 | Input | Output |
|------|------|--------|
| **Trigger** | Blob 目录路径 | PDF 文件列表 |
| **Doc Classification** | PDF 文件 | `List[DocumentPage]`（含类型） |
| **OCR** | `List[DocumentPage]` | `OCROutput`（6 类文档 JSON + metadata） |
| **NER** | `OCROutput` | `NEROutput`（标准化实体） |
| **Rule Check** | `NEROutput` + DB | `RuleCheckOutput`（决策） |
| **Final** | All above | `ClaimResult`（完整结构化结果） |

---

这个设计完全支持：
- **多文档类型差异化处理**（通过路由到不同 processor）
- **版本灵活迭代**（文档级 + 全局）
- **Azure Function 友好**（无状态、临时文件、依赖清晰）
- **可测试 & 可维护**（Pydantic 校验 + 模块解耦）

需要我帮你写 `claim_processor.py` 的核心 orchestration 代码或 `document_classifier` 的示例吗？

### USER
请提供完整的代码结构 解释每个文件作用 尤其是版本迭代的体现 和 input output 的定义

### ASSISTANT
以下是 **claims-ai-processor** 项目的完整代码结构说明，重点突出：

- 每个文件/目录的作用
- **版本迭代如何体现**（文档级 + 全局）
- **各阶段 input / output 的明确定义**（含 Pydantic schema）
- 与 Azure Function App 的集成方式

---

## 📁 项目根目录结构（含详细说明）

```
claims-ai-processor/
│
├── .github/workflows/ci.yml
│   → GitHub Actions：运行 pytest + ruff/black 检查
│
├── config/
│   ├── global_versions.yaml          # ← 全局组件版本（OpenAI 模型、NER 引擎、规则引擎）
│   ├── document_versions.yaml        # ← 每类文档使用的 processor 版本 + 是否必填
│   └── settings.py                   # ← 融合 YAML + 环境变量，提供统一配置访问
│
├── document_processors/              # ← 【核心】按文档类型 + 版本组织
│   ├── __init__.py
│   ├── base_processor.py             # 抽象基类：定义 extract() 接口
│   │
│   ├── claim_form/
│   │   ├── v1/                       # ← 版本 v1
│   │   │   ├── prompt.py             # prompt 模板（字符串或 Jinja2）
│   │   │   └── rules.py              # 后处理规则（如金额校验）
│   │   └── v2/                       # ← 版本 v2（新增字段、改进 prompt）
│   │       ├── prompt.py
│   │       └── rules.py
│   │
│   ├── invoice/                      # 同上，支持多版本并存
│   │   ├── v1/
│   │   └── v2/
│   │
│   └── ... (discharge, receipt, etc.)
│
├── document_classifiers/             # ← 新增：PDF 页分类器
│   ├── __init__.py
│   ├── base_classifier.py
│   └── v1/
│       ├── prompt.py                 # "This page appears to be: [invoice/claim_form/...]"
│       └── classifier.py             # 调用 OpenAI 分类
│
├── ner_extractors/
│   ├── base_ner.py
│   ├── v1/                           # 旧版 NER：简单实体抽取
│   └── v2/                           # 新版 NER：跨文档融合 + 标准化（ICD-10）
│       ├── prompts.py
│       └── extractor.py
│
├── rule_engines/
│   ├── base_rule_engine.py
│   ├── rules_2025_q3_v1.py           # Q3 规则
│   └── rules_2025_q4_v1.py           # Q4 新增：金额上限、诊断排除列表
│
├── services/
│   ├── ocr_service.py                # 调用 document_processors（按类型+版本路由）
│   ├── ner_service.py                # 调用 ner_extractors（按 global_versions.yaml）
│   └── rule_service.py               # 调用 rule_engines + 查询 DB
│
├── handlers/
│   └── claim_processor.py            # 端到端流程编排（主入口）
│
├── utils/
│   ├── azure_document_intelligence.py  # 封装 ADI analyze_document
│   ├── openai_client.py                # 封装 Azure OpenAI + prompt 注入
│   ├── db_client.py                    # 查询 policy 表（policy_number → coverage）
│   └── pdf_utils.py                    # 解压 ZIP、PDF 分页、文本提取
│
├── schemas/                            # ← 所有阶段的输入/输出契约
│   ├── ocr_output.py                   # 定义 OCR 阶段输出结构
│   ├── ner_output.py                   # NER 输出
│   ├── rule_output.py                  # 规则判断结果
│   └── claim_result.py                 # 最终输出
│
├── tests/                              # 完整测试体系
│   ├── conftest.py                     # mock clients, temp dirs
│   ├── unit/
│   └── integration/
│
├── main.py                             # Azure Function 入口
├── host.json                           # Function App 配置（超时、日志等）
├── function.json                       # Blob trigger 配置
├── requirements.txt
└── README.md
```

---

## 🔑 关键文件详解

---

### 📄 `config/global_versions.yaml`
```yaml
# 全局版本控制：影响整个 pipeline
openai_model: "gpt-4o-2025-08-06"
azure_document_intelligence_api_version: "2024-02-29"
ner_extractor_version: "v2"
rule_engine: "rules_2025_q4_v1"
```

> ✅ **作用**：决定使用哪个 NER 版本、规则引擎版本、AI 模型
> ✅ **迭代体现**：只需改此文件，无需改代码

---

### 📄 `config/document_versions.yaml`
```yaml
# 文档级版本控制：每类文档独立迭代
claim_form:
  version: "v2"
  required: true
invoice:
  version: "v2"
  required: true
discharge:
  version: "v1"
  required: true
receipt:
  version: "v1"
  required: false
payment_proof:
  version: "v1"
  required: false
id_card:
  version: "v1"
  required: true
```

> ✅ **作用**：OCR 阶段动态加载 `document_processors/claim_form/v2/`
> ✅ **迭代体现**：`claim_form` 从 v1 → v2，不影响 `invoice` 的 v1

---

### 📄 `schemas/ocr_output.py`
```python
from pydantic import BaseModel
from typing import Optional

class ClaimFormOCR(BaseModel):
    policy_number: str
    patient_name: str
    claim_amount: float

class InvoiceOCR(BaseModel):
    total_amount: float
    hospital_name: str

# ... 其他文档模型

class OCROutput(BaseModel):
    claim_form: Optional[ClaimFormOCR] = None
    discharge: Optional[DischargeOCR] = None
    invoice: Optional[InvoiceOCR] = None
    receipt: Optional[ReceiptOCR] = None
    payment_proof: Optional[PaymentProofOCR] = None
    id_card: Optional[IDCardOCR] = None
    metadata: OCRMetadata
```

> ✅ **Output of OCR Stage**
> ✅ 所有字段可选（因某些文档可能缺失）

---

### 📄 `schemas/ner_output.py`
```python
class NEROutput(BaseModel):
    policy_number: str
    patient_name: str
    diagnosis_codes: list[str]          # 标准化 ICD-10
    procedure_codes: list[str]
    total_claimed_amount: float
    provider_signature_verified: bool
    ner_version: str                    # e.g., "v2"
```

> ✅ **Input**: `OCROutput`
> ✅ **Output of NER Stage**

---

### 📄 `schemas/rule_output.py`
```python
class RuleCheckOutput(BaseModel):
    policy_valid: bool
    coverage_active: bool
    diagnosis_covered: bool
    amount_within_limit: bool
    missing_documents: list[str]
    final_decision: Literal["APPROVED", "REJECTED", "PENDING_REVIEW"]
    rejection_reasons: list[str]
    rule_engine_version: str            # e.g., "rules_2025_q4_v1"
```

> ✅ **Input**: `NEROutput` + DB policy data
> ✅ **Output of Rule Stage**

---

### 📄 `schemas/claim_result.py`
```python
class ClaimResult(BaseModel):
    claim_id: str
    policy_number: str
    ocr: OCROutput
    ner: NEROutput
    rule_check: RuleCheckOutput
    overall_status: Literal["APPROVED", "REJECTED", "PENDING_REVIEW"]
    processing_timestamp: datetime
    pipeline_version: str  # 由 settings.py 生成，如 "v2.1.0"
```

> ✅ **Final Output** → 可存入 DB 或返回给前端

---

### 📄 `document_processors/base_processor.py`
```python
from abc import ABC, abstractmethod
from schemas.ocr_output import *

class BaseDocumentProcessor(ABC):
    @abstractmethod
    def extract(self, page_texts: list[str]) -> BaseModel:
        """返回对应文档类型的 Pydantic 模型"""
        pass
```

> ✅ 所有 `v1/prompt.py + rules.py` 组合成一个 processor 实现此接口

---

### 📄 `document_processors/claim_form/v2/prompt.py`
```python
CLAIM_FORM_V2_PROMPT = """
You are an expert insurance claims processor.
Extract the following fields from the claim form:
- policy_number
- patient_name
- claim_amount

Text:
{page_text}

Output JSON only.
"""
```

> ✅ **版本迭代体现**：v2 可能比 v1 多提取 `claim_currency` 字段

---

### 📄 `services/ocr_service.py`
```python
from config.settings import get_document_version
from document_processors import load_processor

def process_ocr(document_pages: List[DocumentPage]) -> OCROutput:
    result = {}
    for doc_type in DOCUMENT_TYPES:
        pages = [p for p in document_pages if p.document_type == doc_type]
        if not pages and is_required(doc_type):
            raise MissingDocumentError(doc_type)

        version = get_document_version(doc_type)  # ← 从 document_versions.yaml 读取
        processor = load_processor(doc_type, version)  # ← 动态加载 v1/v2
        extracted = processor.extract([p.raw_text for p in pages])
        result[doc_type] = extracted

    return OCROutput(**result, metadata=build_metadata())
```

> ✅ **核心逻辑**：按类型 + 版本路由 → 实现灵活迭代

---

### 📄 `handlers/claim_processor.py`
```python
class ClaimProcessor:
    def process(self, blob_directory: str) -> ClaimResult:
        # Stage 0: Download PDFs
        pdf_paths = download_from_blob(blob_directory)

        # Stage 1: Classify pages
        all_pages = []
        for pdf in pdf_paths:
            pages = split_pdf_to_pages(pdf)
            texts = [extract_text(p) for p in pages]
            classified = [classify_page(text) for text in texts]  # ← document_classifiers
            all_pages.extend(classified)

        # Stage 2: OCR
        ocr_result = ocr_service.process_ocr(all_pages)

        # Stage 3: NER
        ner_result = ner_service.process(ocr_result)

        # Stage 4: Rule Check
        rule_result = rule_service.check(ner_result)

        return ClaimResult(
            claim_id=extract_claim_id(blob_directory),
            policy_number=ner_result.policy_number,
            ocr=ocr_result,
            ner=ner_result,
            rule_check=rule_result,
            overall_status=rule_result.final_decision,
            processing_timestamp=datetime.utcnow(),
            pipeline_version=get_pipeline_version()
        )
```

> ✅ **端到端编排**，清晰划分四阶段

---

### 📄 `main.py`（Azure Function 入口）
```python
import azure.functions as func
from handlers.claim_processor import ClaimProcessor

def main(blob: func.InputStream):
    claim_dir = blob.name  # e.g., "claims/case_123/"
    result = ClaimProcessor().process(claim_dir)

    # Upload result JSON to output container
    upload_to_blob(f"results/{result.claim_id}.json", result.json(indent=2))
```

> ✅ 无状态、临时文件处理、依赖注入友好

---

## 🔄 版本迭代如何工作？（关键！）

| 场景 | 操作 | 影响范围 |
|------|------|--------|
| **改进 claim_form 提取逻辑** | 新增 `claim_form/v3/`，改 `document_versions.yaml` 中 `claim_form.version = "v3"` | 仅 claim_form 处理升级 |
| **升级 NER 引擎** | 开发 `ner_extractors/v3/`，改 `global_versions.yaml` 中 `ner_extractor_version: "v3"` | 所有 claim 的 NER 升级 |
| **Q4 新规上线** | 新增 `rule_engines/rules_2025_q4_v2.py`，改 `global_versions.yaml` | 所有 claim 规则更新 |

> ✅ **零代码修改即可切换版本**
> ✅ **历史 claim 可复现**（记录 pipeline_version）

---

## 🧪 测试示例：`tests/unit/document_processors/test_claim_form_v2.py`

```python
def test_claim_form_v2_extraction(mock_openai):
    mock_openai.return_value = '{"policy_number": "POL-2025", "patient_name": "Alice", "claim_amount": 1200.0}'

    from document_processors.claim_form.v2.processor import ClaimFormV2Processor
    processor = ClaimFormV2Processor()
    result = processor.extract(["... claim form text ..."])

    assert result.policy_number == "POL-2025"
    assert result.claim_amount == 1200.0
```

---

## ✅ 总结：设计优势

| 需求 | 实现方式 |
|------|--------|
| **多文档类型差异化处理** | `document_processors/<type>/vX/` + 动态路由 |
| **OCR → NER → Rule 三阶段** | `services/` 分层 + Pydantic schema 契约 |
| **Prompt 工程显式管理** | 每个版本独立 `prompt.py` |
| **双重版本控制** | `global_versions.yaml` + `document_versions.yaml` |
| **Azure Function 可部署** | 无状态、`main.py` 入口、临时文件处理 |
| **可扩展性** | 新增文档类型？只需加目录；新规则？加 rule_engines 文件 |

---

如需，我可以提供以下任一完整代码模板：
- `claim_processor.py` 完整实现
- `document_classifiers/v1/classifier.py`
- `function.json` + `host.json` 配置
- `pytest` fixture 示例（mock ADI/OpenAI/DB）

请告诉我你最需要哪一部分。

### USER
全局配置没有体现 document_classifiers/             # ← 新增：PDF 页分类器

### ASSISTANT
你说得非常对！在当前的 **全局配置设计**（`config/global_versions.yaml`）中，确实**遗漏了对 `document_classifiers` 的版本控制**。这是一个关键组件，因为它决定了 PDF 页面如何被分类为 6 种文档类型，直接影响后续 OCR 路由的准确性。

---

## ✅ 正确做法：在 `global_versions.yaml` 中显式加入 `document_classifier_version`

### 🔧 更新后的 `config/global_versions.yaml`
```yaml
# 全局组件版本控制（影响整个 pipeline）
openai_model: "gpt-4o-2025-08-06"
azure_document_intelligence_api_version: "2024-02-29"

# 新增：文档分类器版本
document_classifier_version: "v1"

# NER 与规则引擎
ner_extractor_version: "v2"
rule_engine: "rules_2025_q4_v1"
```

> ✅ **作用**：决定在 Stage 1（文档分类）时加载 `document_classifiers/v1/` 还是 `v2/`
> ✅ **迭代体现**：未来可升级为 `v2`（例如引入多模态图像+文本分类）

---

## 📂 对应的 `document_classifiers/` 目录结构（支持版本）

```
document_classifiers/
├── __init__.py
├── base_classifier.py
├── v1/
│   ├── prompt.py          # 分类 prompt 模板
│   └── classifier.py      # 实现 classify_page(text: str) -> str
└── v2/                    # ← 未来扩展（如支持 layout + text 联合分类）
    ├── prompt.py
    └── classifier.py
```

---

## 🧩 如何在代码中使用这个配置？

### 1. 在 `config/settings.py` 中加载
```python
# config/settings.py
import yaml
from pathlib import Path

def load_global_config():
    with open(Path(__file__).parent / "global_versions.yaml") as f:
        return yaml.safe_load(f)

GLOBAL_CONFIG = load_global_config()

# 提供便捷访问
DOCUMENT_CLASSIFIER_VERSION = GLOBAL_CONFIG["document_classifier_version"]
NER_VERSION = GLOBAL_CONFIG["ner_extractor_version"]
RULE_ENGINE = GLOBAL_CONFIG["rule_engine"]
```

---

### 2. 在 `utils/pdf_utils.py` 或专用分类服务中调用

```python
# utils/document_classifier_loader.py
from config.settings import DOCUMENT_CLASSIFIER_VERSION

def load_document_classifier():
    if DOCUMENT_CLASSIFIER_VERSION == "v1":
        from document_classifiers.v1.classifier import DocumentClassifierV1
        return DocumentClassifierV1()
    elif DOCUMENT_CLASSIFIER_VERSION == "v2":
        from document_classifiers.v2.classifier import DocumentClassifierV2
        return DocumentClassifierV2()
    else:
        raise ValueError(f"Unsupported classifier version: {DOCUMENT_CLASSIFIER_VERSION}")
```

---

### 3. 在主流程中使用（`handlers/claim_processor.py`）

```python
from utils.document_classifier_loader import load_document_classifier

class ClaimProcessor:
    def __init__(self):
        self.classifier = load_document_classifier()  # ← 按全局版本加载

    def _classify_pages(self, page_texts: List[str]) -> List[DocumentPage]:
        return [
            DocumentPage(
                page_number=i,
                raw_text=text,
                document_type=self.classifier.classify(text),
                confidence=0.95  # 可选
            )
            for i, text in enumerate(page_texts)
        ]
```

---

## 🧪 测试覆盖建议

```python
# tests/unit/test_document_classifier_v1.py
def test_classifier_v1_invoice():
    from document_classifiers.v1.classifier import DocumentClassifierV1
    text = "Invoice No: INV-2025\nTotal Amount: $1,200"
    assert DocumentClassifierV1().classify(text) == "invoice"

def test_classifier_v1_claim_form():
    text = "Insurance Claim Form\nPolicy Number: POL-2025"
    assert DocumentClassifierV1().classify(text) == "claim_form"
```

---

## ✅ 为什么必须全局控制 `document_classifier`？

- **它是一个 pipeline 前置依赖**：分类错误会导致后续所有处理错位（如把发票当出院小结）
- **分类逻辑会演进**：
  - v1：纯文本关键词 + 简单 prompt
  - v2：结合 ADI 的 layout 信息（表格/标题位置）
  - v3：多模态（图像 + 文本）
- **需要与 NER/Rule 版本解耦**：分类器可独立升级，不影响规则引擎

---

## 📌 最终建议：`global_versions.yaml` 完整字段

```yaml
# config/global_versions.yaml
openai_model: "gpt-4o-2025-08-06"
azure_document_intelligence_api_version: "2024-02-29"

# 核心 pipeline 组件版本
document_classifier_version: "v1"   # ← 显式加入！
ner_extractor_version: "v2"
rule_engine: "rules_2025_q4_v1"
```

这样，你的 **双重版本控制体系**就完整了：

| 控制粒度 | 配置文件 | 控制内容 |
|--------|--------|--------|
| **全局** | `global_versions.yaml` | AI 模型、分类器、NER、规则引擎 |
| **文档级** | `document_versions.yaml` | 每类文档的 OCR processor 版本 |

---

如果你希望，我也可以提供 `document_classifiers/v1/classifier.py` 的完整实现示例（基于 OpenAI prompt 分类）。是否需要？
