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
