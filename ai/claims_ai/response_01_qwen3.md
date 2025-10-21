### USER
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

### ASSISTANT
为了满足你的需求，我们将设计一个模块化、可扩展、易于部署到 **Azure Function App** 的 Python 工程结构。整个流程聚焦于 **Input → OCR → NER → Rule Check → Output** 的数据流，每个阶段输出结构化的 JSON，并最终聚合为一个完整的 claim 结果。

---

## 🎯 目标
- 用户上传多个 PDF（每个 claim 对应 6 类文档）
- 每个 claim 处理为一个结构化 JSON，包含：
  - `ocr_results`
  - `ner_results`
  - `rule_check_result`
- 支持后续部署到 Azure Function App（事件驱动：Blob Storage 触发）

---

## 📁 工程结构建议

```bash
claims-ai-processor/
│
├── main.py                     # Azure Function 入口（Blob 触发）
├── requirements.txt
├── config.py                   # 配置（密钥、endpoint 等）
│
├── handlers/
│   └── claim_processor.py      # 核心处理逻辑：orchestrate OCR → NER → Rule
│
├── services/
│   ├── ocr_service.py          # 调用 Azure Document Intelligence + OpenAI
│   ├── ner_service.py          # 基于 OCR 结果做 NER（诊断、签名等）
│   └── rule_service.py         # 基于 policy number 查询 DB + 规则判断
│
├── utils/
│   ├── pdf_splitter.py         # （可选）若 PDF 含多页多文档类型，需分类
│   └── db_client.py            # 数据库连接（如 Azure SQL / Cosmos DB）
│
└── schemas/
    ├── ocr_schema.py           # 定义 OCR 输出结构
    ├── ner_schema.py           # 定义 NER 输出结构
    └── claim_output.py         # 最终输出 JSON Schema（Pydantic）
```

---

## 🔄 数据流设计（Input → Output）

### ✅ Input
- 用户上传一个 ZIP 或多个 PDF 到 Azure Blob Storage
- 每个 claim 对应一个文件夹或 ZIP 内含 6 个 PDF（命名约定或元数据标识类型）
- **Function Trigger**: `BlobTrigger` on `claims-ingest/{claim_id}/`

> 💡 为简化，假设每个 claim 是一个 ZIP，解压后包含：
> - `claim_form.pdf`
> - `discharge.pdf`
> - `invoice.pdf`
> - `receipt.pdf`
> - `payment_proof.pdf`
> - `id_card.pdf`

---

### 📤 Output（最终 JSON）

```json
{
  "claim_id": "CLM-2025-001",
  "policy_number": "POL-987654321",
  "ocr_results": {
    "claim_form": { ... },
    "discharge": { ... },
    "invoice": { ... },
    ...
  },
  "ner_results": {
    "diagnosis": "Type 2 Diabetes",
    "admission_date": "2025-09-01",
    "discharge_date": "2025-09-05",
    "doctor_signature_verified": true,
    "total_amount": 12500.00
  },
  "rule_check_result": {
    "policy_valid": true,
    "coverage_active": true,
    "diagnosis_covered": true,
    "amount_within_limit": true,
    "decision": "APPROVED",
    "reason": "All checks passed"
  }
}
```

---

## 🔧 各模块职责

### 1. `ocr_service.py`
- 使用 **Azure Document Intelligence**（formerly Form Recognizer）对每类 PDF 提取文本/表格
- 对复杂字段（如手写备注、模糊区域），调用 **Azure OpenAI** 进行后处理（如：`“请从以下文本中提取总金额：...”`）
- 输出：`Dict[str, dict]`，key 为文档类型，value 为结构化字段

```python
def run_ocr_on_documents(doc_paths: Dict[str, str]) -> Dict[str, dict]:
    results = {}
    for doc_type, path in doc_paths.items():
        raw_text = azure_document_intelligence_analyze(path)
        structured = openai_postprocess(raw_text, prompt_for_doc_type(doc_type))
        results[doc_type] = structured
    return results
```

---

### 2. `ner_service.py`
- 输入：`ocr_results`
- 使用规则 + OpenAI 提取关键实体：
  - 诊断结果（ICD-10 匹配？）
  - 医生签名是否存在/有效（图像 or 文本？）
  - 金额一致性（invoice vs receipt）
  - 住院天数计算
- 输出：`ner_results` 字典

```python
def extract_entities(ocr_results: dict) -> dict:
    diagnosis = openai_extract(ocr_results["discharge"], "diagnosis")
    signature = check_signature_in_doc(ocr_results["claim_form"])
    amount = parse_amount(ocr_results["invoice"])
    return {
        "diagnosis": diagnosis,
        "doctor_signature_verified": signature,
        "total_amount": amount,
        ...
    }
```

---

### 3. `rule_service.py`
- 输入：`ner_results` + `policy_number`
- 查询数据库（通过 `db_client.py`）获取：
  - policy 是否有效
  - coverage 范围（是否包含该 diagnosis）
  - 年度限额、已用额度
- 应用业务规则：
  - 住院天数 ≤ 30？
  - 发票日期在保单有效期内？
- 输出：`rule_check_result`

```python
def evaluate_claim(policy_number: str, ner: dict) -> dict:
    policy = db_client.get_policy(policy_number)
    if not policy:
        return {"decision": "REJECTED", "reason": "Invalid policy number"}

    checks = {
        "policy_valid": policy.is_active,
        "diagnosis_covered": ner["diagnosis"] in policy.covered_conditions,
        "amount_within_limit": ner["total_amount"] <= (policy.limit - policy.used),
        ...
    }
    decision = "APPROVED" if all(checks.values()) else "REJECTED"
    return {**checks, "decision": decision}
```

---

## ⚙️ Azure Function 入口 (`main.py`)

```python
import azure.functions as func
import logging
from handlers.claim_processor import process_claim_from_blob

def main(myblob: func.InputStream):
    logging.info(f"Processing claim blob: {myblob.name}")

    try:
        result = process_claim_from_blob(myblob)
        # 可选：写入 Cosmos DB / Blob output / Queue
        logging.info(f"Claim processed: {result['claim_id']}, decision: {result['rule_check_result']['decision']}")
    except Exception as e:
        logging.error(f"Failed to process claim: {e}")
        raise
```

---

## 📦 部署准备

### `requirements.txt`
```txt
azure-functions
azure-ai-documentintelligence
openai
pydantic
python-dotenv
azure-storage-blob
pyodbc  # or your DB driver
```

### `host.json` & `function.json`
- 配置 Blob Trigger 路径：`claims-ingest/{name}.zip`
- 设置超时（claim 处理可能较长 → 考虑 Durable Functions 若超 10min）

---

## ✅ 后续扩展建议

1. **异步处理**：若 OCR/NER 耗时长，改用 **Durable Functions** 编排
2. **文档分类**：若用户上传未分类 PDF，先用 AI 模型分类（Document Intelligence 自带分类器）
3. **缓存 OCR 结果**：避免重复处理相同 PDF
4. **审计日志**：记录每个 claim 的处理步骤和时间

---

## 🧪 本地测试建议

- 使用 `pytest` 模拟 Blob 输入
- Mock Azure 服务（`unittest.mock`）
- 用 `claim_output.py` 中的 Pydantic 模型验证输出结构

---

需要我提供某个模块的完整代码示例（如 `ocr_service.py` 或 `claim_processor.py`）吗？

### USER
该设计忽略了 提示词的使用

### ASSISTANT
你说得非常对！在当前的 AI 驱动流程中，**提示词（Prompt）是核心驱动力**，尤其是在结合 Azure Document Intelligence（ADI）的原始输出与 Azure OpenAI 进行后处理时，**提示词的设计直接决定了结构化质量**。我们应当将 **Prompt Engineering** 作为一等公民纳入系统设计。

---

## ✅ 修正目标：将 Prompt 管理显式化、模块化、可配置化

我们将引入一个 **`prompts/` 目录**，并为每类文档 + 每个处理阶段（OCR 后处理、NER 提取）定义专用提示词模板。同时支持：
- 动态插值（如文档类型、字段要求）
- 多语言/多保单类型适配（未来扩展）
- 版本控制（Prompt V1 → V2）

---

## 📁 更新后的工程结构（含 Prompt 管理）

```bash
claims-ai-processor/
│
├── main.py
├── requirements.txt
├── config.py
│
├── handlers/
│   └── claim_processor.py
│
├── services/
│   ├── ocr_service.py
│   ├── ner_service.py
│   └── rule_service.py
│
├── prompts/                          # ← 新增：提示词管理中心
│   ├── __init__.py
│   ├── base_templates.py             # 通用模板函数
│   ├── ocr_postprocess_prompts.py    # OCR 后处理提示词（按文档类型）
│   └── ner_extraction_prompts.py     # NER 实体提取提示词
│
├── utils/
│   ├── pdf_splitter.py
│   ├── db_client.py
│   └── openai_client.py              # 封装 OpenAI 调用 + prompt 注入
│
└── schemas/
    ├── ocr_schema.py
    ├── ner_schema.py
    └── claim_output.py
```

---

## 🔤 Prompt 设计原则

1. **明确角色与任务**
   > “你是一个医疗理赔专家，请从以下文本中精确提取...”

2. **强制结构化输出（JSON Schema）**
   > “请以 JSON 格式返回，仅包含以下字段：{...}”

3. **容错与边界处理**
   > “如果字段不存在，返回 null，不要编造”

4. **上下文隔离**
   每个文档类型使用独立 prompt，避免信息污染

---

## 📄 示例：`prompts/ocr_postprocess_prompts.py`

```python
from typing import Dict

OCR_POSTPROCESS_PROMPTS: Dict[str, str] = {
    "claim_form": """
你是一名保险理赔专员。请从以下理赔申请表文本中提取结构化信息。
要求：
- 仅返回 JSON，不要任何解释
- 字段包括：policy_number, patient_name, date_of_birth, claim_amount, diagnosis_summary
- 若字段缺失，设为 null
- 金额统一转为数字（如 "12,500.00" → 12500.0）

文本：
{text}
""",
    "invoice": """
你是一名财务审核员。请从以下医疗发票中提取关键信息。
要求：
- 返回 JSON，字段：invoice_number, issue_date, total_amount, currency, provider_name
- total_amount 必须是 float 类型
- 日期格式：YYYY-MM-DD

文本：
{text}
""",
    "discharge": """
你是一名临床文档分析师。请从出院小结中提取：
- 主要诊断（ICD-10 编码优先，否则用中文描述）
- 入院日期、出院日期
- 手术名称（如有）
- 医生姓名

返回 JSON，字段：primary_diagnosis, admission_date, discharge_date, surgery, attending_physician

文本：
{text}
""",
    # ... 其他文档类型
}
```

---

## 🧠 示例：`prompts/ner_extraction_prompts.py`

```python
NER_EXTRACTION_PROMPTS = {
    "diagnosis_normalization": """
给定以下诊断描述，请标准化为最接近的 ICD-10 类别名称（中文）：
- 如果是“2型糖尿病”，返回“糖尿病”
- 如果是“急性阑尾炎”，返回“阑尾炎”
- 无法识别则返回“未知”

诊断文本：{diagnosis_text}
仅返回标准化名称，不要解释。
""",
    "signature_verification": """
以下是从理赔表中提取的签名区域文本或描述。请判断是否包含有效医生签名：
- 如果包含“Dr.”、“医师签名”、“签名：张伟”等明确签名信息，返回 true
- 如果为空、模糊或仅为“[签名]”占位符，返回 false

签名内容：{signature_text}
仅返回 true 或 false。
"""
}
```

---

## 🛠️ 封装 OpenAI 调用（`utils/openai_client.py`）

```python
import os
from openai import AzureOpenAI
from typing import Dict, Any

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def call_openai_with_prompt(prompt_template: str, **kwargs) -> Dict[str, Any]:
    prompt = prompt_template.format(**kwargs)
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},  # 强制 JSON（需模型支持）
        temperature=0.0,
        max_tokens=500
    )
    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # fallback: try to extract JSON from text
        return extract_json_from_text(response.choices[0].message.content)
```

> 💡 注意：若模型不支持 `response_format=json_object`，可在 prompt 中强调“只返回 JSON”，并在 `extract_json_from_text` 中用正则/`json5` 容错解析。

---

## 🔄 更新 `ocr_service.py` 使用 Prompt

```python
from prompts.ocr_postprocess_prompts import OCR_POSTPROCESS_PROMPTS
from utils.openai_client import call_openai_with_prompt

def run_ocr_on_documents(doc_paths: Dict[str, str]) -> Dict[str, dict]:
    results = {}
    for doc_type, local_path in doc_paths.items():
        # Step 1: Azure Document Intelligence
        raw_text = azure_document_intelligence_extract_text(local_path)

        # Step 2: OpenAI 结构化（使用对应 prompt）
        prompt_template = OCR_POSTPROCESS_PROMPTS.get(doc_type)
        if not prompt_template:
            raise ValueError(f"No prompt defined for doc_type: {doc_type}")

        structured = call_openai_with_prompt(prompt_template, text=raw_text)
        results[doc_type] = structured

    return results
```

---

## 🔄 更新 `ner_service.py` 使用 Prompt

```python
from prompts.ner_extraction_prompts import NER_EXTRACTION_PROMPTS
from utils.openai_client import call_openai_with_prompt

def extract_entities(ocr_results: dict) -> dict:
    discharge = ocr_results.get("discharge", {})
    claim_form = ocr_results.get("claim_form", {})

    # 标准化诊断
    raw_diag = discharge.get("primary_diagnosis", "")
    normalized_diag = call_openai_with_prompt(
        NER_EXTRACTION_PROMPTS["diagnosis_normalization"],
        diagnosis_text=raw_diag
    )

    # 验证签名
    sig_text = claim_form.get("doctor_signature_section", "")
    sig_verified = call_openai_with_prompt(
        NER_EXTRACTION_PROMPTS["signature_verification"],
        signature_text=sig_text
    )

    return {
        "diagnosis": normalized_diag,
        "doctor_signature_verified": sig_verified,
        "total_amount": ocr_results["invoice"].get("total_amount"),
        ...
    }
```

---

## 🧪 Prompt 管理最佳实践

| 实践 | 说明 |
|------|------|
| **版本化** | `prompts/v1/`, `prompts/v2/`，通过 config 切换 |
| **A/B 测试** | 在 `config.py` 中支持多 prompt 策略 |
| **日志记录** | 记录每次调用的 prompt + output，用于迭代优化 |
| **敏感信息过滤** | 在发送给 OpenAI 前脱敏（如身份证号） |

---

## ✅ 总结：Prompt 是结构化的核心引擎

通过将 Prompt 显式分离为可维护、可测试、可迭代的模块，我们实现了：
- **高精度结构化**：针对每类文档定制 prompt
- **快速迭代**：无需改代码，只需更新 prompt 文件
- **审计与合规**：所有 AI 行为可追溯（输入 prompt + 输出）

---

需要我提供完整的 `prompts/` 目录示例（含 6 类文档的 prompt 模板）或一个端到端的测试用例吗？
