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

### USER
加上 version control 设计 因为 ocr ner rule check 中经常出现版本更新 或者版本回退 最好通过一个配置文件 yaml 格式的
最后加上 pytest 的设计


### ASSISTANT
非常好！为了支持 **版本控制（Versioning）** 和 **可测试性（Testing）**，我们将引入：

1. **一个 YAML 配置文件**：统一管理 OCR、NER、Rule Check 各模块的版本（包括 Prompt 版本、模型版本、规则版本）
2. **Pytest 测试架构**：覆盖单元测试（各服务）、集成测试（端到端流程）、Mock 外部依赖

---

## 🧩 一、版本控制设计：`config/versions.yaml`

该文件作为 **单一事实源（Single Source of Truth）**，定义当前系统使用的各组件版本。

```yaml
# config/versions.yaml
version: "1.2.0"  # 整体 pipeline 版本（可选）

components:
  ocr:
    engine: "azure-document-intelligence"
    model_version: "2024-05-01-preview"        # ADI 模型版本
    prompt_version: "v1"                       # 对应 prompts/ocr/v1/
    postprocess_llm: "gpt-4o"                  # OpenAI 部署名

  ner:
    prompt_version: "v2"
    extraction_strategy: "openai+rules"        # 可扩展：如 "llm_only", "hybrid"
    openai_deployment: "gpt-4o"

  rule_check:
    rules_version: "2025-Q3-v1"                # 对应 rules/rules_2025_q3_v1.py
    db_schema_version: "v3"

  # 可选：全局 LLM 配置（覆盖）
  openai:
    temperature: 0.0
    max_tokens: 800
```

> ✅ **好处**：
> - 回滚只需改 YAML（如 `prompt_version: "v1"` → `"v0"`）
> - 不同环境（dev/staging/prod）可使用不同 YAML
> - CI/CD 可基于版本号打标签

---

## 📁 工程结构更新（含版本与测试）

```bash
claims-ai-processor/
│
├── config/
│   ├── versions.yaml               # ← 主版本配置
│   └── settings.py                 # 加载 YAML + 环境变量
│
├── prompts/
│   └── v1/                         # ← 按版本组织
│   │   ├── ocr_postprocess_prompts.py
│   │   └── ner_extraction_prompts.py
│   └── v2/
│       └── ...
│
├── rules/
│   ├── rules_2025_q3_v1.py         # ← 规则逻辑版本化
│   └── rules_2025_q2_v3.py
│
├── services/
│   ├── ocr_service.py
│   ├── ner_service.py
│   └── rule_service.py
│
├── tests/                          # ← Pytest 目录
│   ├── conftest.py                 # 全局 fixture
│   ├── unit/
│   │   ├── test_ocr_service.py
│   │   ├── test_ner_service.py
│   │   └── test_rule_service.py
│   └── integration/
│       └── test_end_to_end.py
│
├── main.py
├── requirements.txt
└── ...
```

---

## 🔧 二、加载版本配置：`config/settings.py`

```python
# config/settings.py
import os
import yaml
from pathlib import Path

CONFIG_DIR = Path(__file__).parent
VERSIONS_FILE = CONFIG_DIR / "versions.yaml"

def load_versions_config():
    with open(VERSIONS_FILE) as f:
        return yaml.safe_load(f)

VERSIONS = load_versions_config()

# 环境覆盖（用于测试或临时切换）
OCR_PROMPT_VERSION = os.getenv("OCR_PROMPT_VERSION") or VERSIONS["components"]["ocr"]["prompt_version"]
NER_PROMPT_VERSION = os.getenv("NER_PROMPT_VERSION") or VERSIONS["components"]["ner"]["prompt_version"]
RULES_VERSION = os.getenv("RULES_VERSION") or VERSIONS["components"]["rule_check"]["rules_version"]
```

---

## 🔄 三、服务层使用版本（示例：`ocr_service.py`）

```python
# services/ocr_service.py
from config.settings import OCR_PROMPT_VERSION
from utils.openai_client import call_openai_with_prompt

def get_ocr_prompt(doc_type: str) -> str:
    # 动态导入对应版本的 prompt
    prompt_module = __import__(
        f"prompts.{OCR_PROMPT_VERSION}.ocr_postprocess_prompts",
        fromlist=["OCR_POSTPROCESS_PROMPTS"]
    )
    return prompt_module.OCR_POSTPROCESS_PROMPTS[doc_type]

def run_ocr_on_documents(doc_paths: Dict[str, str]) -> Dict[str, dict]:
    results = {}
    for doc_type, path in doc_paths.items():
        raw_text = azure_document_intelligence_extract(path)
        prompt = get_ocr_prompt(doc_type)
        structured = call_openai_with_prompt(prompt, text=raw_text)
        results[doc_type] = structured
    return results
```

> ✅ 同理，`ner_service.py` 和 `rule_service.py` 也通过 `NER_PROMPT_VERSION`、`RULES_VERSION` 动态加载逻辑。

---

## 📜 四、规则版本化示例：`rules/rules_2025_q3_v1.py`

```python
# rules/rules_2025_q3_v1.py
def evaluate_claim_v1(policy_data: dict, ner_data: dict) -> dict:
    """2025 Q3 版本规则：支持慢性病年度限额"""
    diagnosis = ner_data.get("diagnosis")
    amount = ner_data.get("total_amount", 0)

    covered = diagnosis in policy_data.get("covered_conditions", [])
    within_limit = amount <= policy_data.get("remaining_annual_limit", 0)

    return {
        "diagnosis_covered": covered,
        "amount_within_limit": within_limit,
        "decision": "APPROVED" if covered and within_limit else "REJECTED"
    }
```

`rule_service.py` 中动态调用：

```python
# services/rule_service.py
from config.settings import RULES_VERSION

def load_rule_engine():
    module = __import__(f"rules.rules_{RULES_VERSION}", fromlist=["evaluate_claim_v1"])
    return getattr(module, f"evaluate_claim_v1")  # 或通用函数名 evaluate_claim

def evaluate_claim(policy_number: str, ner: dict) -> dict:
    policy = db_client.get_policy(policy_number)
    rule_func = load_rule_engine()
    return rule_func(policy, ner)
```

---

## 🧪 五、Pytest 测试设计

### 1. `tests/conftest.py`（共享 fixture）

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, patch
import os

@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "AZURE_OPENAI_API_KEY": "fake-key",
        "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com",
        "OCR_PROMPT_VERSION": "v1",
        "NER_PROMPT_VERSION": "v1",
        "RULES_VERSION": "2025_q3_v1"
    }):
        yield
```

### 2. 单元测试：`tests/unit/test_ocr_service.py`

```python
# tests/unit/test_ocr_service.py
from services.ocr_service import run_ocr_on_documents
from unittest.mock import patch

@patch("services.ocr_service.azure_document_intelligence_extract")
@patch("services.ocr_service.call_openai_with_prompt")
def test_ocr_service(mock_openai, mock_adi):
    mock_adi.return_value = "Policy: POL-123, Amount: $1000"
    mock_openai.return_value = {"policy_number": "POL-123", "claim_amount": 1000.0}

    result = run_ocr_on_documents({"claim_form": "/fake/path.pdf"})

    assert result["claim_form"]["policy_number"] == "POL-123"
    mock_openai.assert_called_once()
```

### 3. 集成测试：`tests/integration/test_end_to_end.py`

```python
# tests/integration/test_end_to_end.py
from handlers.claim_processor import process_claim_from_dict

def test_full_claim_processing():
    # 模拟 OCR 输入（跳过真实 PDF）
    mock_ocr_input = {
        "claim_form": {"policy_number": "POL-999", "claim_amount": 5000},
        "invoice": {"total_amount": 5000},
        "discharge": {"primary_diagnosis": "糖尿病"}
    }

    # 模拟 DB 返回
    with patch("services.rule_service.db_client.get_policy") as mock_db:
        mock_db.return_value = {
            "covered_conditions": ["糖尿病"],
            "remaining_annual_limit": 10000
        }

        result = process_claim_from_dict("CLM-001", mock_ocr_input)

        assert result["rule_check_result"]["decision"] == "APPROVED"
```

### 4. 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-mock

# 运行全部
pytest

# 只运行单元测试
pytest tests/unit/

# 生成覆盖率报告
pytest --cov=services --cov-report=html
```

---

## 📦 六、部署与版本切换建议

- **生产部署**：将 `config/versions.yaml` 作为 **Function App 的应用设置文件**（或从 Key Vault 拉取）
- **灰度发布**：通过环境变量临时覆盖版本（如 `NER_PROMPT_VERSION=v2-staging`）
- **回滚**：Git 回退 `versions.yaml` + 重新部署 Function

---

## ✅ 总结

| 能力 | 实现方式 |
|------|--------|
| **版本控制** | `versions.yaml` + 动态导入 |
| **Prompt 管理** | `prompts/v1/`, `prompts/v2/` |
| **规则隔离** | `rules/rules_*.py` |
| **可测试性** | Pytest + Mock + Fixture |
| **快速回滚** | 修改 YAML + 重部署 |

---

需要我提供完整的 `versions.yaml` 示例、一个规则版本文件，或 GitHub Actions 的 CI 配置（自动运行 pytest）吗？

### USER
ocr 中有不同的 文档类型 处理规则不一致的 这里没有体现 也需要 版本控制和测试的

### ASSISTANT
你说得非常关键！在实际理赔场景中，**6 类文档（Claim Form、Discharge、Invoice 等）不仅内容不同，其 OCR 后处理逻辑、字段提取规则、校验要求也完全不同**。当前设计虽然按文档类型调用不同 prompt，但缺乏对 **每类文档的独立处理规则 + 版本控制 + 测试隔离**。

---

## ✅ 目标：实现 **文档类型粒度** 的版本化与规则解耦

我们将为 **每种文档类型** 定义：
- 独立的 OCR 后处理规则（字段映射、格式校验、默认值）
- 独立的 Prompt 模板（已支持）
- 独立的版本号（可单独升级 Invoice 的处理逻辑，不影响 ID Card）
- 独立的单元测试

---

## 📁 更新工程结构（支持 per-document-type 版本）

```bash
claims-ai-processor/
│
├── config/
│   └── document_versions.yaml    # ← 新增：每类文档的版本配置
│
├── document_processors/          # ← 新增：每类文档的专属处理器
│   ├── base_processor.py         # 抽象基类
│   ├── claim_form/
│   │   ├── v1/
│   │   │   ├── prompt.py
│   │   │   └── rules.py          # 字段清洗、校验逻辑
│   │   └── v2/
│   │       ├── prompt.py
│   │       └── rules.py
│   ├── invoice/
│   │   └── v1/
│   │       ├── prompt.py
│   │       └── rules.py
│   └── ...                       # discharge, receipt, etc.
│
├── services/
│   └── ocr_service.py            # 调度器：根据类型+版本路由到对应 processor
│
└── tests/
    └── unit/
        └── document_processors/  # 每类文档独立测试
            ├── test_claim_form_v1.py
            └── test_invoice_v1.py
```

---

## 📄 一、文档级版本配置：`config/document_versions.yaml`

```yaml
# config/document_versions.yaml
document_types:
  claim_form:
    enabled: true
    ocr_prompt_version: "v2"
    processing_rules_version: "v2"
    required_fields: ["policy_number", "patient_name", "claim_amount"]

  discharge:
    enabled: true
    ocr_prompt_version: "v1"
    processing_rules_version: "v1"
    required_fields: ["admission_date", "discharge_date", "primary_diagnosis"]

  invoice:
    enabled: true
    ocr_prompt_version: "v3"        # ← 可单独升级
    processing_rules_version: "v2"
    required_fields: ["total_amount", "invoice_number"]

  receipt:
    enabled: true
    ocr_prompt_version: "v1"
    processing_rules_version: "v1"
    required_fields: ["amount_paid", "payment_date"]

  payment_proof:
    enabled: false                  # ← 暂未支持
    ...

  id_card:
    enabled: true
    ocr_prompt_version: "v1"
    processing_rules_version: "v1"
    required_fields: ["id_number", "full_name"]
```

> ✅ **优势**：
> - `invoice` 可用 `v3` prompt + `v2` rules，而 `claim_form` 用 `v2`/`v2`
> - 某类文档可临时禁用（`enabled: false`）
> - 明确每类文档的必填字段（用于后续校验）

---

## 🧱 二、文档处理器基类：`document_processors/base_processor.py`

```python
# document_processors/base_processor.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class DocumentProcessor(ABC):
    DOCUMENT_TYPE = "base"

    @abstractmethod
    def extract_structured_data(self, raw_text: str) -> Dict[str, Any]:
        """使用 LLM + prompt 提取原始结构"""
        pass

    @abstractmethod
    def apply_postprocessing_rules(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """应用业务规则：类型转换、默认值、校验"""
        pass

    def process(self, raw_text: str) -> Dict[str, Any]:
        extracted = self.extract_structured_data(raw_text)
        cleaned = self.apply_postprocessing_rules(extracted)
        return cleaned
```

---

## 📄 三、具体文档处理器示例：`document_processors/invoice/v2/rules.py`

```python
# document_processors/invoice/v2/rules.py
import re
from decimal import Decimal, InvalidOperation

def clean_amount(value) -> float:
    if value is None:
        return None
    # 移除货币符号、逗号
    cleaned = re.sub(r'[^\d.]', '', str(value))
    try:
        return float(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None

def validate_invoice_number(inv_num: str) -> str:
    if not inv_num or len(inv_num.strip()) < 3:
        return None
    return inv_num.strip().upper()

def apply_rules_v2(extracted: dict) -> dict:
    return {
        "invoice_number": validate_invoice_number(extracted.get("invoice_number")),
        "total_amount": clean_amount(extracted.get("total_amount")),
        "issue_date": parse_date(extracted.get("issue_date")),  # 自定义日期解析
        "currency": extracted.get("currency", "CNY").upper(),
    }
```

对应 Prompt：`document_processors/invoice/v2/prompt.py`

```python
PROMPT_TEMPLATE = """
你是一名财务审核员，请从以下发票文本中提取：
- invoice_number（发票号）
- total_amount（总金额，含小数）
- issue_date（开票日期，格式 YYYY-MM-DD）
- currency（货币，如 CNY、USD）

仅返回 JSON，不要解释。
文本：
{text}
"""
```

---

## 🧩 四、OCR 服务调度器：`services/ocr_service.py`

```python
# services/ocr_service.py
import importlib
from config.document_versions import load_document_config
from utils.openai_client import call_openai_with_prompt

def get_processor(doc_type: str, raw_text: str):
    config = load_document_config()[doc_type]
    if not config["enabled"]:
        raise ValueError(f"Document type {doc_type} is disabled")

    prompt_ver = config["ocr_prompt_version"]
    rules_ver = config["processing_rules_version"]

    # 动态导入 prompt
    prompt_mod = importlib.import_module(
        f"document_processors.{doc_type}.{prompt_ver}.prompt"
    )
    # 动态导入 rules
    rules_mod = importlib.import_module(
        f"document_processors.{doc_type}.{rules_ver}.rules"
    )

    # 提取
    extracted = call_openai_with_prompt(prompt_mod.PROMPT_TEMPLATE, text=raw_text)
    # 应用规则
    cleaned = rules_mod.apply_rules_v2(extracted)  # 或通用函数名 apply_rules

    # 校验必填字段
    missing = [f for f in config["required_fields"] if cleaned.get(f) is None]
    if missing:
        raise ValueError(f"Missing required fields in {doc_type}: {missing}")

    return cleaned

def run_ocr_on_documents(doc_paths: Dict[str, str]) -> Dict[str, dict]:
    results = {}
    for doc_type, path in doc_paths.items():
        raw_text = azure_document_intelligence_extract(path)
        results[doc_type] = get_processor(doc_type, raw_text)
    return results
```

---

## 🧪 五、文档级单元测试：`tests/unit/document_processors/test_invoice_v2.py`

```python
# tests/unit/document_processors/test_invoice_v2.py
from document_processors.invoice.v2.rules import apply_rules_v2, clean_amount

def test_clean_amount():
    assert clean_amount("¥12,500.00") == 12500.0
    assert clean_amount("1000") == 1000.0
    assert clean_amount("N/A") is None
    assert clean_amount(None) is None

def test_apply_rules_v2():
    raw = {
        "invoice_number": " inv-2025-001 ",
        "total_amount": "RMB 12,500.00",
        "issue_date": "2025/10/01",
        "currency": "cny"
    }
    result = apply_rules_v2(raw)
    assert result["invoice_number"] == "INV-2025-001"
    assert result["total_amount"] == 12500.0
    assert result["currency"] == "CNY"
```

> ✅ 每个文档类型、每个版本都有独立测试，确保规则变更不影响其他类型。

---

## 🔁 六、版本演进示例

| 场景 | 操作 |
|------|------|
| **Invoice 金额解析出错** | 创建 `invoice/v3/`，修改 `rules.py`，更新 `document_versions.yaml` 中 `invoice.ocr_prompt_version: "v3"` |
| **Discharge 诊断字段变更** | 创建 `discharge/v2/`，仅更新该类型，不影响 Claim Form |
| **回滚 ID Card 处理** | 将 `id_card.processing_rules_version` 从 `v2` 改回 `v1` |

---

## ✅ 总结：文档类型粒度的版本控制优势

| 能力 | 实现 |
|------|------|
| **独立演进** | 每类文档可单独升级 prompt/rules |
| **风险隔离** | Invoice 规则 bug 不影响 Discharge |
| **精准测试** | 每个 `(doc_type, version)` 有专属测试 |
| **配置驱动** | 通过 YAML 控制启用/版本/必填字段 |
| **审计清晰** | Git 历史中 `invoice/v2/` 修改一目了然 |

---

是否需要我提供：
1. 完整的 `document_versions.yaml` 示例（含 6 类文档）？
2. `claim_form/v2/rules.py` 的具体实现？
3. 一个 GitHub Actions workflow 自动运行 per-document-type 测试？

### USER
展示整个代码结构 具体一点 包含所有流程 和可以优化的地方

### ASSISTANT
以下是为 **Claims AI 结构化处理系统** 设计的完整、生产就绪级 Python 工程结构，涵盖你提出的所有核心需求：

- 多文档类型（6 类）差异化处理
- OCR → NER → Rule Check 三阶段流水线
- Prompt 工程显式管理
- **文档类型粒度 + 全局粒度** 的双重版本控制
- 完整的 Pytest 测试体系
- Azure Function App 可部署架构
- 可扩展性与可维护性优化点

---

## 🌐 完整工程结构（含说明）

```bash
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
├── main.py                            # Azure Function 入口（BlobTrigger）
├── host.json                          # Function App 配置
├── function.json                      # Trigger 配置
├── requirements.txt
├── requirements-test.txt              # ← 测试依赖
└── README.md
```

---

## 🔁 核心流程：端到端数据流

```mermaid
graph LR
A[User Upload: ZIP/PDFs] --> B[Azure Blob Trigger]
B --> C[main.py]
C --> D[handlers/claim_processor.py]
D --> E[services/ocr_service.py]
E --> F[document_processors/{type}/{ver}/]
F --> G[OCR 结果: Dict[type, dict]]
G --> H[services/ner_service.py]
H --> I[ner_extractors/{ver}/]
I --> J[NER 结果: diagnosis, amount, signature...]
J --> K[services/rule_service.py]
K --> L[rule_engines/{ver}.py + DB]
L --> M[schemas/claim_result.py]
M --> N[Output: JSON to Cosmos DB / Queue]
```

---

## 📄 关键配置文件示例

### `config/global_versions.yaml`
```yaml
openai:
  deployment: "gpt-4o"
  temperature: 0.0
  max_tokens: 1000

azure_document_intelligence:
  model_id: "prebuilt-document"  # 或 custom model ID
  api_version: "2024-02-29-preview"
```

### `config/document_versions.yaml`
```yaml
document_types:
  claim_form:
    enabled: true
    prompt_version: "v2"
    rules_version: "v2"
    required_fields: [policy_number, patient_name, claim_amount]

  invoice:
    enabled: true
    prompt_version: "v2"
    rules_version: "v2"
    required_fields: [total_amount, invoice_number]

  discharge:
    enabled: true
    prompt_version: "v1"
    rules_version: "v1"
    required_fields: [admission_date, discharge_date, primary_diagnosis]

  # ... 其他类型
```

---

## ⚙️ 可优化点与最佳实践

| 模块 | 优化建议 | 说明 |
|------|--------|------|
| **Prompt 管理** | 引入 `jinja2` 模板 | 支持更复杂插值（如多语言） |
| **OCR 服务** | 缓存原始 ADI 结果 | 避免重复调用（按 PDF hash 缓存） |
| **文档分类** | 增加 AI 分类器 | 若用户上传未标记 PDF，先用 ADI 分类 |
| **规则引擎** | 支持 JSON 规则 | 非代码化规则（如 `{"max_amount": 50000}`） |
| **错误处理** | 结构化错误码 | 如 `ERR_OCR_MISSING_FIELD_INVOICE` |
| **性能** | 异步并行处理 6 类文档 | 使用 `asyncio.gather`（需 Function App 支持） |
| **监控** | 集成 Application Insights | 记录每阶段耗时、失败率 |
| **安全** | 敏感字段脱敏 | 在发送给 OpenAI 前移除身份证号等 |
| **测试** | 添加 snapshot 测试 | 用 `pytest-snapshot` 固化 LLM 输出 |
| **部署** | 使用 Durable Functions | 若处理 >10 分钟，改用 orchestration |

---

## 🧪 测试策略总结

| 测试类型 | 覆盖范围 | 工具 |
|--------|--------|------|
| **Unit** | 单个规则函数（如 `clean_amount`） | `pytest` + `unittest.mock` |
| **Component** | 单个文档处理器（如 `invoice/v2`） | `pytest` + fake raw text |
| **Integration** | OCR → NER → Rule 全链路 | Mock ADI + OpenAI + DB |
| **Contract** | 最终输出符合 `claim_result.py` | Pydantic validation |
| **Regression** | LLM 输出稳定性 | `pytest-snapshot` |

---

## 🚀 部署到 Azure Function App

### `requirements.txt`
```txt
azure-functions
azure-ai-documentintelligence>=1.0.0b1
openai>=1.13.0
pydantic>=2.0
PyYAML
python-dotenv
pyodbc  # or your DB driver
```

### `main.py`（简化版）
```python
import azure.functions as func
from handlers.claim_processor import process_claim_from_blob

def main(myblob: func.InputStream):
    claim_id = myblob.name.split("/")[-1].replace(".zip", "")
    result = process_claim_from_blob(myblob.read(), claim_id)
    # 可选：写入 Cosmos DB
    func.Out(result)
```

---

## ✅ 总结：该设计满足

- ✅ **文档类型差异化处理**：6 类文档独立规则 + 版本
- ✅ **Prompt 作为一等公民**：显式管理、版本化、可测试
- ✅ **三阶段流水线清晰**：OCR → NER → Rule Check
- ✅ **双重版本控制**：全局（OpenAI/ADI） + 文档级（prompt/rules）
- ✅ **完整测试覆盖**：从字段清洗到端到端
- ✅ **Azure 原生集成**：Function App + Blob Trigger + 可选 Cosmos DB
- ✅ **生产就绪**：错误处理、配置驱动、安全、监控扩展点

---

如需，我可以提供：
1. 完整的 `document_processors/claim_form/v2/rules.py` 实现
2. GitHub Actions CI 配置（pytest + coverage）
3. `schemas/claim_result.py` 的 Pydantic 模型
4. 模拟 ADI + OpenAI 的测试 fixture

请告诉我你最想先看哪一部分？
