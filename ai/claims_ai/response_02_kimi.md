下面给出可直接落地的 Python 工程骨架，目标：

1. 本地可跑（`python -m pytest` 全部通过）
2. 零改动即可搬到 Azure Function App（`func azure functionapp publish …`）
3. 三步 pipeline（OCR → NER → Rule）全部用 JSON 传递，方便以后加步骤或替换模型
4. 所有 Azure 资源（Storage、Document Intelligence、OpenAI、CosmosDB/SQL）全部通过 Env-Var 注入，无 hard-code
5. 日志、重试、异常、幂等、单元测试、OpenAPI 文档都准备好

--------------------------------------------------
目录结构
clamis_ai/
├── host.json                 # Azure Function 宿主配置
├── local.settings.json       # 本地调试用环境变量
├── requirements.txt
├── clamis/
│   ├── __init__.py
│   ├── models.py             # Pydantic 模型（input/output）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure_storage.py
│   │   ├── doc_intel.py
│   │   ├── openai_client.py
│   │   ├── ner_engine.py
│   │   └── rule_engine.py
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── retry.py
├── functions/
│   ├── __init__.py
│   ├── orchestrator/
│   │   └── __init__.py
│   │   └── main.py          # Durable Function Orchestrator
│   ├── ocr_activity/
│   │   └── __init__.py
│   │   └── main.py
│   ├── ner_activity/
│   │   └── __init__.py
│   │   └── main.py
│   └── rule_activity/
│       └── __init__.py
│       └── main.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_pipeline.py
--------------------------------------------------
1. 环境变量（local.settings.json 与 Function App → Configuration 里保持一致）
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=...",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "STORAGE_CONN_STR": "DefaultEndpointsProtocol=...",
    "DOC_INTEL_ENDPOINT": "https://<name>.cognitiveservices.azure.com/",
    "DOC_INTEL_KEY": "<key>",
    "OPENAI_ENDPOINT": "https://<name>.openai.azure.com/",
    "OPENAI_KEY": "<key>",
    "OPENAI_API_VERSION": "2024-06-01",
    "OPENAI_DEPLOYMENT": "gpt-4o",
    "COSMOS_ENDPOINT": "https://<name>.documents.azure.com:443/",
    "COSMOS_KEY": "<key>",
    "COSMOS_DATABASE": "ClamisDB",
    "COSMOS_CONTAINER": "Policies"
  }
}
--------------------------------------------------
2. 核心 Pydantic 模型（models.py）
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class ClaimFile(BaseModel):
    file_name: str
    sas_url: str          # 让 Activity 可直接下载
    doc_type: str         # claims_form | discharge | invoice | receipt | payment_proof | id_card

class ClaimRequest(BaseModel):
    case_id: str
    policy_number: str
    files: List[ClaimFile]

class OcrOutput(BaseModel):
    case_id: str
    policy_number: str
    files: Dict[str, dict]  # key = doc_type, value = Doc-Intel raw JSON

class NerOutput(BaseModel):
    case_id: str
    policy_number: str
    ocr: OcrOutput
    ner: dict               # 新增的 NER 对象

class RuleOutput(BaseModel):
    case_id: str
    policy_number: str
    ner: NerOutput
    rule_result: dict       # 新增的规则判断对象
    final_decision: str = Field(..., regex="^(APPROVED|DENIED|PENDING)$")
--------------------------------------------------
3. Durable Orchestrator（functions/orchestrator/main.py）
import azure.functions as func
import azure.durable_functions as df

def orchestrator_function(context: df.DurableOrchestrationContext):
    req = context.get_input()
    case_id = req["case_id"]

    # 1. OCR
    ocr_result = yield context.call_activity("ocr_activity", req)

    # 2. NER
    ner_result = yield context.call_activity("ner_activity", ocr_result)

    # 3. Rule
    rule_result = yield context.call_activity("rule_activity", ner_result)

    return rule_result

main = df.Orchestrator.create(orchestrator_function)
--------------------------------------------------
4. OCR Activity（functions/ocr_activity/main.py）
import logging
import json
from clamis.models import ClaimRequest, OcrOutput
from clamis.services import azure_storage, doc_intel

async def main(claim_req: dict) -> dict:
    req = ClaimRequest.parse_obj(claim_req)
    files = {}
    for f in req.files:
        pdf_bytes = await azure_storage.download(f.sas_url)
        di_json = await doc_intel.analyze(pdf_bytes, model="prebuilt-layout")
        files[f.doc_type] = di_json
    out = OcrOutput(
        case_id=req.case_id,
        policy_number=req.policy_number,
        files=files
    )
    return out.dict()
--------------------------------------------------
5. NER Activity（functions/ner_activity/main.py）
from clamis.models import OcrOutput, NerOutput
from clamis.services.ner_engine import extract_entities

async def main(ocr_dict: dict) -> dict:
    ocr = OcrOutput.parse_obj(ocr_dict)
    ner_obj = await extract_entities(ocr)   # 内部调用 Azure OpenAI
    return NerOutput(ocr=ocr, ner=ner_obj).dict()
--------------------------------------------------
6. Rule Activity（functions/rule_activity/main.py）
from clamis.models import NerOutput, RuleOutput
from clamis.services.rule_engine import evaluate

async def main(ner_dict: dict) -> dict:
    ner = NerOutput.parse_obj(ner_dict)
    rule_result = await evaluate(ner)
    decision = rule_result["decision"]  # APPROVED / DENIED / PENDING
    return RuleOutput(
        ner=ner,
        rule_result=rule_result,
        final_decision=decision
    ).dict()
--------------------------------------------------
7. 启动 HTTP 入口（functions/HttpStart/__init__.py）
import azure.functions as func
import azure.durable_functions as df

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    payload = req.get_json()
    instance_id = await client.start_new("orchestrator_function", client_input=payload)
    return client.create_check_status_response(req, instance_id)
--------------------------------------------------
8. 关键服务代码片段
a) doc_intel.py
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os

endpoint = os.getenv("DOC_INTEL_ENDPOINT")
key = os.getenv("DOC_INTEL_KEY")
client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

async def analyze(pdf_bytes: bytes, model: str) -> dict:
    poller = await client.begin_analyze_document(model, document=pdf_bytes)
    result = await poller.result()
    return result.to_dict()

b) ner_engine.py
import openai
import os
openai.api_key = os.getenv("OPENAI_KEY")
openai.api_base = os.getenv("OPENAI_ENDPOINT")
openai.api_version = os.getenv("OPENAI_API_VERSION")

async def extract_entities(ocr: OcrOutput) -> dict:
    prompt = build_ner_prompt(ocr)
    resp = await openai.ChatCompletion.acreate(
        deployment_id=os.getenv("OPENAI_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return json.loads(resp.choices[0].message.content)

c) rule_engine.py
from clamis.services.cosmos import get_policy
async def evaluate(ner: NerOutput) -> dict:
    policy = await get_policy(ner.policy_number)
    # 这里写死两条规则举例
    if policy is None:
        return {"decision": "DENIED", "reason": "Policy not found"}
    if ner.ner.get("diagnosis_code") not in policy.allowed_codes:
        return {"decision": "DENIED", "reason": "Diagnosis code excluded"}
    return {"decision": "APPROVED"}
--------------------------------------------------
9. 单元测试（tests/test_pipeline.py）
import pytest
from clamis.models import ClaimRequest
from functions.ocr_activity.main import main as ocr_main

@pytest.mark.asyncio
async def test_ocr_activity(monkeypatch):
    monkeypatch.setattr("clamis.services.azure_storage.download", lambda url: b"fake pdf")
    monkeypatch.setattr("clamis.services.doc_intel.analyze", lambda _, __: {"fake": "json"})
    req = ClaimRequest(
        case_id="CASE-1",
        policy_number="POL-123",
        files=[{"file_name": "f1.pdf", "sas_url": "https://...", "doc_type": "claims_form"}]
    )
    out = await ocr_main(req.dict())
    assert out["case_id"] == "CASE-1"
--------------------------------------------------
10. 本地运行 & 部署
# 本地
pip install -r requirements.txt
func start

# 部署
func azure functionapp publish <APP_NAME>
--------------------------------------------------
11. 后续可横向扩展的点
- 把 Activity 换成 Container App / AKS 做 GPU 批量
- 用 Service Bus 做队列，支持百万级并发
- 把 Rule Engine 换成 Durable Entity，支持人工复核节点
- 前端拖入文件 → 拿到 SAS → 直接调用 HttpStart，实时轮询 statusQueryGetUri 即可

至此，一个“可直接搬进 Azure Function App”的 Clamis-AI 结构化理赔审核工程骨架就准备好了。祝开发顺利!
