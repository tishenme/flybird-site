下面给出一份可直接搬上 Azure Function App 的 Python 工程模板，聚焦“Input → OCR → NER → Rule Check”三步流水线。

工程结构、依赖、配置、日志、异常重试、幂等写入、本地调试、CI-CD 打包（VS Code + Azure Functions Core Tools）全部一次给齐。

你只需要把业务规则（Rule Check 里的 SQL/存储过程调用）和 NER 提示词替换成自己的即可。

---

一、工程结构（单函数 3 个 Activity，Durable 编排）
<project_root>
├── .funcignore
├── .gitignore
├── requirements.txt
├── host.json
├── local.settings.json
├── Dockerfile          # 可选，容器部署
├── claims_pipeline
│   ├── init.py
│   ├── orchestrator.py      # Durable Orchestrator
│   ├── activity_ocr.py      # Activity 1
│   ├── activity_ner.py      # Activity 2
│   ├── activity_rule.py     # Activity 3
│   ├── shared
│   │   ├── init.py
│   │   ├── blob.py          # Azure Storage 上传/下载封装
│   │   ├── doc_intel.py     # Azure Document Intelligence 封装
│   │   ├── openai_ner.py    # AOAI 封装（NER 提示词）
│   │   ├── sql.py           # PyODBC 连接 Policy DB
│   │   ├── models.py        # Pydantic 模型（强类型贯穿三步）
│   │   └── logger.py        # 统一日志（AppInsights）
│   └── tests                # pytest 单元
└── deploy
├── azure-pipelines.yml  # ADO CI-CD
└── bicep
├── funcapp.bicep    # 资源 IaC
└── role-assign.bicep

---

二、核心模型（models.py）

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import datetime as dt

class ClaimDoc(BaseModel):
    doc_type: str   # claims_form | discharge | invoice | receipt | payment_proof | id_card
    pages: int
    blob_url: str
    sas: Optional[str] = None

class OCRResult(BaseModel):
    policy_no: Optional[str] = None
    claim_no: str
    docs: List[ClaimDoc]
    raw_intel: Dict = Field(description="Azure DI output")
    openai_json: Dict = Field(description="OpenAI 抽取后统一 JSON")

class NERResult(BaseModel):
    ocr: OCRResult
    entities: Dict = Field(description="新增 NER 对象")
    confidence: float

class RuleResult(BaseModel):
    ner: NERResult
    rule_pass: bool
    rule_messages: List[str]
    final_status: str   # APPROVED / REJECTED / PENDING
    updated_on: dt.datetime = Field(default_factory=dt.datetime.utcnow)
```

---

三、Orchestrator（orchestrator.py）

```python
import azure.functions as func
import azure.durable_functions as df

def orchestrator_function(context: df.DurableOrchestrationContext):
    payload = context.get_input()          # {"case_id":"C-123","container":"claims","prefix":"C-123/"}
    # 1. OCR
    ocr_result = yield context.call_activity("activity_ocr", payload)
    if not ocr_result.get("policy_no"):
        return {"error": "policy_no not found in OCR"}
    # 2. NER
    ner_result = yield context.call_activity("activity_ner", ocr_result)
    # 3. Rule
    rule_result = yield context.call_activity("activity_rule", ner_result)
    return rule_result

main = df.Orchestrator.create(orchestrator_function)
```

---

四、Activity 1 – OCR（activity_ocr.py）

```python
import logging
from claims_pipeline.shared import blob, doc_intel, models

def main(payload: dict) -> dict:
    """
    输入: {"case_id":"C-123","container":"claims","prefix":"C-123/"}
    输出: OCRResult JSON
    """
    case_id = payload["case_id"]
    container = payload["container"]
    prefix  = payload["prefix"]

    # 1. 列出该 case 所有 PDF
    pdf_list = blob.list_blobs(container, prefix)
    ocr_docs = []
    policy_no = None
    for pdf in pdf_list:
        if not pdf.name.lower().endswith(".pdf"):
            continue
        # 2. 调用 Azure Document Intelligence（prebuilt-layout + 选自己训练的 custom model）
        di_result = doc_intel.run(pdf.url)
        # 3. 调用 OpenAI 把 DI 结果抽成统一 JSON（提示词里强制要求输出 policy_number）
        openai_json = doc_intel.openai_extract(di_result)
        if not policy_no and openai_json.get("policy_number"):
            policy_no = openai_json["policy_number"]
        ocr_docs.append(models.OCRResult.ClaimDoc(
            doc_type=classify_doc_type(pdf.name),
            pages=len(di_result.pages),
            blob_url=pdf.url
        ))
    ocr = models.OCRResult(
        policy_no=policy_no,
        claim_no=case_id,
        docs=ocr_docs,
        raw_intel=di_result,
        openai_json=openai_json
    )
    # 4. 把中间结果写回 blob：/intermediate/ocr/{case_id}.json
    blob.upload_json(f"intermediate/ocr/{case_id}.json", ocr.dict())
    return ocr.dict()
```

---

五、Activity 2 – NER（activity_ner.py）

```python
from claims_pipeline.shared import openai_ner, blob

def main(ocr_dict: dict) -> dict:
    ocr = models.OCRResult(**ocr_dict)
    # 1. 把 OCR.openai_json 里的诊断、医生签名、剂量等字段做二次 NER
    entities = openai_ner.run(ocr.openai_json)
    ner = models.NERResult(ocr=ocr, entities=entities, confidence=entities.get("confidence",0))
    # 2. 落盘
    blob.upload_json(f"intermediate/ner/{ocr.claim_no}.json", ner.dict())
    return ner.dict()
```

---

六、Activity 3 – Rule Check（activity_rule.py）

```python
from claims_pipeline.shared import sql, blob

def main(ner_dict: dict) -> dict:
    ner = models.NERResult(**ner_dict)
    policy_no = ner.ocr.policy_no
    # 1. 拿 policy 数据
    policy_row = sql.get_policy(policy_no)
    if not policy_row:
        return models.RuleResult(
            ner=ner,
            rule_pass=False,
            rule_messages=["Policy not found"],
            final_status="REJECTED"
        ).dict()
    # 2. 规则引擎（示例）
    messages = []
    status = "APPROVED"
    if policy_row["policy_status"] != "ACTIVE":
        messages.append("Policy inactive")
        status = "REJECTED"
    if ner.entities.get("diagnosis_code") in policy_row["excluded_codes"]:
        messages.append("Diagnosis excluded")
        status = "REJECTED"
    # 3. 组装结果
    rule = models.RuleResult(
        ner=ner,
        rule_pass=(status == "APPROVED"),
        rule_messages=messages,
        final_status=status
    )
    # 4. 落盘 + 写 SQL 结果表（可选）
    blob.upload_json(f"output/{ner.ocr.claim_no}.json", rule.dict())
    sql.insert_claim_result(rule)
    return rule.dict()
```

---

七、共享组件（节选）
1. blob.py

```python
from azure.storage.blob import BlobServiceClient
_conn_str = os.getenv("AzureWebJobsStorage")
_sas = os.getenv("BLOB_SAS_TOKEN")
client = BlobServiceClient.from_connection_string(_conn_str)
```

2. doc_intel.py

```python
from azure.ai.formrecognizer import DocumentAnalysisClient
endpoint = os.getenv("DOC_INTEL_ENDPOINT")
key = os.getenv("DOC_INTEL_KEY")
client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))
```

3. openai_ner.py

```python
import openai
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
```

4. sql.py

```python
import pyodbc
def get_policy(policy_no: str):
    with pyodbc.connect(os.getenv("POLICY_DB")) as conn:
        return conn.cursor().execute("SELECT * FROM Policy WHERE PolicyNo=?", policy_no).fetchone()
```

---

八、requirements.txt

```
azure-functions
azure-functions-durable
azure-storage-blob
azure-ai-formrecognizer
openai
pyodbc
pydantic
python-dotenv
```

---

九、host.json（精简）

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": { "samplingSettings": { "isEnabled": true } }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[3.*, 4.0.0)"
  }
}
```

---

十、local.settings.json（本地调试）

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DOC_INTEL_ENDPOINT": "https://<>.cognitiveservices.azure.com/",
    "DOC_INTEL_KEY": "<>",
    "AZURE_OPENAI_ENDPOINT": "https://<>.openai.azure.com/",
    "AZURE_OPENAI_KEY": "<>",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4o",
    "POLICY_DB": "Driver={ODBC Driver 18 for SQL Server};Server=tcp:<>;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Database=PolicyDB;Uid=<>;Pwd=<>",
    "BLOB_SAS_TOKEN": "?sv=<>"
  }
}
```

---

十一、本地运行 & 打包

```bash
# 1. 建虚拟环境
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 安装 Azure Functions Core Tools
npm i -g azure-functions-core-tools@4

# 3. 启动
func start

# 4. 触发（POST）
curl -X POST http://localhost:7071/orchestrators/claims_pipeline \
  -H "Content-Type:application/json" \
  -d '{"case_id":"C-123","container":"claims","prefix":"C-123/"}'

# 5. 查看结果
func durable get-runtime-status -i <instanceId>

# 6. 打包发布
func azure functionapp publish <funcapp-name> --python
```

---

十二、CI-CD（azure-pipelines.yml 节选）

```yaml
trigger:
- main
pool:
  vmImage: ubuntu-latest
steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'
- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pytest claims_pipeline/tests
- task: AzureFunctionApp@1
  inputs:
    azureSubscription: 'AzureServiceConnection'
    appType: 'functionAppLinux'
    appName: 'func-claims-ai'
    package: '$(Build.ArtifactStagingDirectory)'
```

---

十三、可扩展点
1. 多语言/多模型：NER 环节可再调一个 HuggingFace 模型，对比 OpenAI 置信度取高。
2. 人工复核：RuleResult.final_status=PENDING 时自动写队列，触发 Durable 外部事件，人工审核后把结果 push 回 Orchestrator。
3. 并行提速：一个 case 6 个 PDF，可在 OCR 环节用 `yield context.task_all([...])` 并行。
4. 灰度/AB：在 Rule Check 里加 Feature Flag，根据 policy_no 尾号切换新旧规则。
5. 计费与审计：中间 JSON 全部写 blob 带 SAS，前端可直接下载，作为审计凭证。

---

十四、下一步
1. 把 policy DB 的查询换成存储过程，减少往返。
2. 把 NER 提示词做成版本化模板存 blob，热更新。
3. 加 App Insights 自定义维度（case_id、policy_no），方便出报表。
4. 写 ARM/Bicep 一次性把 Function App、Storage、Doc Intel、VNets、私有终结点、Managed Identity、Key Vault 全拉起，做到“代码–基础设施”同库同源。

至此，一个可直接搬迁到 Azure Function App 的 Python 工程骨架就完成了。祝项目顺利上线！
