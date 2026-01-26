### USER
我现在使用 Microsoft Semantic Kernel 在 azure 平台上实现下面需求
我现在的开发语言是 python 3.11 部署在 azure function app
使用的模型是 azure open ai 4o
使用了 azure documentintelligence 做ocr 有些特殊情况使用直接把 图片base64后直接给 open ai ( 比如 id card 准确率更好 因为 adi 的结果太大不能全给 open ai )

我现在需要优化我现有的流程 使用 Semantic Kernel 的skills 更好的管理我的提示词 比如我在一份总文档分类每一页对应不同的文档类型 然后对不同的文档类型提取成不同 json object , 最后把这个合并一起 作为这份文档总的 ocr 结果

### ASSISTANT
你当前的流程已经非常清晰，使用 **Azure OpenAI (GPT-4o)** + **Azure Document Intelligence (ADI)** + **Semantic Kernel (SK)** 在 **Azure Function App**（Python 3.11）中实现文档 OCR 与结构化提取。现在希望借助 Semantic Kernel 的 **Skills 机制** 更好地管理提示词、模块化不同文档类型的处理逻辑，并最终合并为统一的 JSON 输出。

下面我将为你提供一个 **优化后的架构设计与代码示例**，帮助你：

1. **用 SK Skills 管理不同文档类型的提示词和输出结构**
2. **动态路由到对应 Skill 进行结构化提取**
3. **合并所有页面结果为一份总文档 JSON**

---

## ✅ 一、整体架构思路

```
[输入：PDF/图片] 
   ↓
Azure Document Intelligence (OCR) → 每页文本 + layout
   ↓
LLM（GPT-4o）初步分类每页 → {page_id: doc_type}
   ↓
根据 doc_type 路由到对应 Semantic Kernel Skill
   ↓
每个 Skill 使用专属 prompt 提取结构化 JSON
   ↓
合并所有页面 JSON → 最终输出
```

> 💡 对于 ID Card 等特殊类型，可跳过 ADI，直接传 base64 图像给 GPT-4o（通过 `image_url` 或 `content` 中的 `image` 类型）

---

## ✅ 二、使用 Semantic Kernel Skills 管理提示词

### 1. 安装依赖（确保已安装）

```bash
pip install semantic-kernel azure-ai-documentintelligence openai
```

### 2. 定义 Skill 目录结构（推荐）

```
skills/
├── invoice_skill.py
├── id_card_skill.py
├── bank_statement_skill.py
└── common/
    └── classification_prompt.txt
```

每个 Skill 是一个 Python 函数，绑定专属提示词模板。

---

## ✅ 三、代码实现（核心部分）

### 1. 初始化 Semantic Kernel

```python
# kernel_setup.py
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

def create_kernel():
    kernel = sk.Kernel()
    chat_service = AzureChatCompletion(
        deployment_name="your-gpt-4o-deployment",
        endpoint="https://your-resource.openai.azure.com/",
        api_key="your-api-key",
        api_version="2024-02-01"  # 或最新支持 vision 的版本
    )
    kernel.add_service(chat_service)
    return kernel
```

---

### 2. 定义通用文档分类 Skill（第一页或每页分类）

```python
# skills/classification_skill.py
from semantic_kernel.functions.kernel_function_decorator import kernel_function

class DocumentClassificationSkill:
    @kernel_function(
        description="Classify document page into a known type",
        name="classify_page"
    )
    def classify_page(self, input: str) -> str:
        # 实际由 LLM 执行，这里只是占位
        pass
```

注册提示词：

```python
# 在主函数中
kernel = create_kernel()

# 注册分类 prompt（从文件读取更佳）
classification_prompt = """
You are an expert document classifier.
Given the following text from a document page, classify it into one of these types:
- invoice
- id_card
- bank_statement
- unknown

Only output the type name.

Text:
{{$input}}
"""

kernel.create_function_from_prompt(
    prompt=classification_prompt,
    function_name="classify_page",
    plugin_name="DocumentClassifier",
    description="Classify a document page"
)
```

---

### 3. 为每种文档类型定义 Skill（以 ID Card 为例）

```python
# skills/id_card_skill.py
id_card_prompt = """
Extract structured information from this ID card image or text.
Return a JSON object with these fields:
{
  "full_name": "...",
  "id_number": "...",
  "date_of_birth": "YYYY-MM-DD",
  "address": "...",
  "issue_date": "YYYY-MM-DD"
}

If any field is missing, use null.

Input:
{{$input}}
"""

# 在主流程中注册
kernel.create_function_from_prompt(
    prompt=id_card_prompt,
    function_name="extract_id_card",
    plugin_name="IDCardSkill",
    description="Extract ID card info"
)
```

> 同理注册 `invoice_skill`, `bank_statement_skill` 等。

---

### 4. 主流程：处理整份文档

```python
import asyncio
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import base64

async def process_document(pages: list, images: list = None):
    kernel = create_kernel()
    
    # Step 1: 分类每页
    page_types = []
    for i, page_text in enumerate(pages):
        classify_func = kernel.plugins["DocumentClassifier"]["classify_page"]
        doc_type = await kernel.invoke(classify_func, input=page_text)
        page_types.append(str(doc_type).strip())

    # Step 2: 根据类型提取结构化数据
    results = []
    for i, doc_type in enumerate(page_types):
        if doc_type == "id_card":
            # 特殊处理：使用原始图像（base64）
            image_base64 = base64.b64encode(images[i]).decode('utf-8')
            input_content = f"image/jpeg;base64,{image_base64}"
            extract_func = kernel.plugins["IDCardSkill"]["extract_id_card"]
        elif doc_type == "invoice":
            input_content = pages[i]
            extract_func = kernel.plugins["InvoiceSkill"]["extract_invoice"]
        else:
            # fallback to raw text or skip
            results.append({"page": i, "type": doc_type, "data": None})
            continue

        json_result = await kernel.invoke(extract_func, input=input_content)
        results.append({
            "page": i,
            "type": doc_type,
            "data": json.loads(str(json_result))
        })

    # Step 3: 合并结果（可按需聚合，如合并所有发票行项）
    final_output = {
        "document_id": "doc_123",
        "pages": results
    }
    return final_output
```

---

### 5. 在 Azure Function 中调用

```python
# __init__.py (Azure Function)
import azure.functions as func
import asyncio

async def main(req: func.HttpRequest) -> func.HttpResponse:
    # 获取上传的 PDF/图片
    file = req.files['document']
    
    # 调用 ADI 获取每页文本
    pages = await run_document_intelligence(file)
    
    # 可选：保留原始图像用于 ID Card 等
    images = extract_images_from_pdf(file)  # 你需要实现

    # 处理文档
    result = await process_document(pages, images)
    
    return func.HttpResponse(json.dumps(result), mimetype="application/json")
```

---

## ✅ 四、优化建议

| 优化点 | 说明 |
|------|------|
| **Prompt 版本管理** | 将 prompt 存为 `.txt` 文件，用 Git 管理，便于 A/B 测试 |
| **缓存分类结果** | 对相同内容页面避免重复分类 |
| **错误重试** | 对 LLM 提取失败的页面，fallback 到规则或人工审核队列 |
| **Vision 输入优化** | GPT-4o 支持多图像输入，可一次传多页（但注意 token 限制） |
| **Skill 插件化** | 将每个 Skill 做成独立插件，便于团队协作 |

---

## ✅ 五、后续扩展

- 使用 **SK 的 Planner** 自动选择 Skill（适合复杂流程）
- 加入 **验证 Skill**：对提取的 JSON 做 schema 校验
- 使用 **Azure AI Search** 存储结构化结果，支持检索

---

如果你能提供当前代码片段（比如如何调用 ADI、如何传图给 GPT-4o），我可以进一步帮你做 **无缝迁移** 到 SK 架构。

是否需要我为你生成一个完整的可运行示例项目结构？

### USER
我是希望把提示词抽取出来 后面每多一种文档类型 写个新的提示词即可 怎么更好的管理 提取的 json 内容和约束?

### ASSISTANT
非常好的问题！你希望：

1. **将提示词（prompts）完全外置化**，新增文档类型时只需添加一个新提示词文件；
2. **自动约束输出为结构化 JSON**，并确保格式符合预期（字段、类型、必填等）；
3. **最小化代码改动**，避免每次新增类型都要写新函数或注册逻辑。

下面我为你提供一套 **基于 Semantic Kernel + JSON Schema + 动态 Prompt 加载** 的最佳实践方案，完全满足你的需求。

---

## ✅ 核心思路：**“Prompt + Schema = Skill”**

我们将每个文档类型定义为一个 **配置单元**，包含两个文件：

```
skills/
└── document_types/
    ├── invoice/
    │   ├── prompt.txt
    │   └── schema.json
    ├── id_card/
    │   ├── prompt.txt
    │   └── schema.json
    └── bank_statement/
        ├── prompt.txt
        └── schema.json
```

- `prompt.txt`：告诉 LLM 要提取什么
- `schema.json`：定义输出 JSON 的结构、类型、约束（用于验证 + 引导 LLM）

> 💡 GPT-4o 支持 **JSON mode**，可强制输出合法 JSON；结合 schema 可进一步提升准确性。

---

## ✅ 一、统一的动态 Skill 加载器

我们只写 **一个通用函数**，根据文档类型动态加载对应的 prompt 和 schema。

```python
# skill_loader.py
import os
import json
from pathlib import Path
from semantic_kernel.functions.kernel_function_decorator import kernel_function

class DynamicDocumentSkill:
    def __init__(self, skills_dir: str = "skills/document_types"):
        self.skills_dir = Path(skills_dir)
        self._load_all_schemas_and_prompts()

    def _load_all_schemas_and_prompts(self):
        self.type_configs = {}
        for type_dir in self.skills_dir.iterdir():
            if type_dir.is_dir():
                type_name = type_dir.name
                prompt_file = type_dir / "prompt.txt"
                schema_file = type_dir / "schema.json"
                if prompt_file.exists() and schema_file.exists():
                    prompt = prompt_file.read_text(encoding="utf-8").strip()
                    schema = json.loads(schema_file.read_text(encoding="utf-8"))
                    self.type_configs[type_name] = {
                        "prompt": prompt,
                        "schema": schema
                    }

    @kernel_function(
        description="Dynamically extract structured data based on document type",
        name="extract_by_type"
    )
    def extract_by_type(self, input: str, doc_type: str) -> str:
        # 实际由外部 invoke 调用，此处仅为占位
        pass
```

---

## ✅ 二、在主流程中动态注册函数（无需硬编码）

```python
# main.py 或 Azure Function 入口
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from skill_loader import DynamicDocumentSkill

def register_dynamic_skills(kernel: sk.Kernel, skill_loader: DynamicDocumentSkill):
    for doc_type, config in skill_loader.type_configs.items():
        # 构造带 JSON 模式约束的 prompt
        full_prompt = f"""
{config['prompt']}

Respond only in valid JSON format that matches this schema:
{json.dumps(config['schema'], indent=2)}

Do not include any other text or explanation.
"""

        # 注册函数（函数名 = extract_{doc_type}）
        kernel.create_function_from_prompt(
            prompt=full_prompt,
            function_name=f"extract_{doc_type}",
            plugin_name="DynamicDocumentExtractor",
            description=f"Extract {doc_type} as JSON"
        )
```

> ✅ **新增文档类型？只需在 `skills/document_types/` 下新建文件夹 + 两个文件，无需改代码！**

---

## ✅ 三、使用 JSON Schema 约束输出（关键！）

### 示例：`id_card/schema.json`

```json
{
  "type": "object",
  "properties": {
    "full_name": { "type": "string" },
    "id_number": { "type": "string" },
    "date_of_birth": { "type": "string", "format": "date" },
    "address": { "type": ["string", "null"] },
    "issue_date": { "type": "string", "format": "date" }
  },
  "required": ["full_name", "id_number"],
  "additionalProperties": false
}
```

### 示例：`invoice/schema.json`

```json
{
  "type": "object",
  "properties": {
    "invoice_number": { "type": "string" },
    "total_amount": { "type": "number" },
    "currency": { "type": "string" },
    "issue_date": { "type": "string", "format": "date" },
    "line_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": { "type": "string" },
          "amount": { "type": "number" }
        },
        "required": ["description", "amount"]
      }
    }
  },
  "required": ["invoice_number", "total_amount"]
}
```

> 🔒 这个 schema 会被拼接到 prompt 中，**引导 LLM 输出合规 JSON**。  
> 同时你也可以在后处理中用 `jsonschema` 库做二次验证。

---

## ✅ 四、主流程调用（分类 → 提取 → 验证）

```python
import asyncio
import json
import jsonschema

async def process_document_pages(pages: list, images: list, skill_loader: DynamicDocumentSkill):
    kernel = create_kernel()  # 你的 SK 初始化
    register_dynamic_skills(kernel, skill_loader)

    # Step 1: 分类每页（假设已有 classify_page 函数）
    page_types = []
    for text in pages:
        result = await kernel.invoke(
            kernel.plugins["DocumentClassifier"]["classify_page"],
            input=text
        )
        page_types.append(str(result).strip())

    # Step 2: 提取 + 验证
    results = []
    for i, doc_type in enumerate(page_types):
        if doc_type not in skill_loader.type_configs:
            results.append({"page": i, "type": doc_type, "error": "Unsupported type"})
            continue

        # 决定输入是文本还是图像 base64
        if doc_type == "id_card":
            img_b64 = base64.b64encode(images[i]).decode()
            input_content = f"data:image/jpeg;base64,{img_b64}"
        else:
            input_content = pages[i]

        # 调用对应提取函数
        func_name = f"extract_{doc_type}"
        try:
            raw_output = await kernel.invoke(
                kernel.plugins["DynamicDocumentExtractor"][func_name],
                input=input_content
            )
            json_data = json.loads(str(raw_output))

            # 可选：用 schema 验证
            schema = skill_loader.type_configs[doc_type]["schema"]
            jsonschema.validate(instance=json_data, schema=schema)

            results.append({
                "page": i,
                "type": doc_type,
                "data": json_data
            })
        except Exception as e:
            results.append({
                "page": i,
                "type": doc_type,
                "error": str(e),
                "raw_output": str(raw_output) if 'raw_output' in locals() else None
            })

    return {"pages": results}
```

---

## ✅ 五、部署建议（Azure Function）

- 将 `skills/document_types/` 目录放在项目根目录，打包进 Function App
- 使用 `__file__` 定位路径，避免部署路径问题：

```python
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills", "document_types")
skill_loader = DynamicDocumentSkill(SKILLS_DIR)
```

---

## ✅ 六、优势总结

| 特性 | 实现方式 |
|------|--------|
| **新增类型零代码** | 只需加 `prompt.txt` + `schema.json` |
| **强 JSON 约束** | Schema 引导 + 验证双保险 |
| **提示词版本可控** | 文件管理，支持 Git diff / review |
| **复用性强** | 一个函数处理所有类型 |
| **兼容图像输入** | 特殊类型走 base64 路径 |

---

如果你希望，我可以为你生成一个 **完整可运行的 GitHub 项目模板**（含 Azure Function 结构 + 示例技能）。是否需要？

### USER
这里怎么体现了 skills 的优越性? 怎么更好的使用了提示词?

### ASSISTANT
非常好的追问！你已经意识到：**“把提示词抽成文件”本身并不等于“用好了 Semantic Kernel 的 Skills”**。  
关键在于：**Skills 不只是“组织提示词”，而是“封装可复用、可组合、可管理的智能行为单元”**。

下面我从 **对比视角** 和 **SK 核心能力** 两个维度，清晰说明 **为什么上述方案真正发挥了 Skills 的优势**，以及 **如何更深度地利用 SK 提升提示词工程效率**。

---

## 🔍 一、对比：普通写法 vs. 真正用好 SK Skills

### ❌ 普通做法（仅“抽离提示词”）
```python
# config/invoice_prompt.txt
# config/id_card_prompt.txt

def extract_invoice(text):
    prompt = read_file("invoice_prompt.txt")
    return call_llm(prompt + text)

def extract_id_card(image_b64):
    prompt = read_file("id_card_prompt.txt")
    return call_llm(prompt + image_b64)
```
**问题**：
- 每新增类型就要写新函数（违反开闭原则）
- 无法统一管理上下文、重试、日志、验证
- 不能被 Planner 自动调用
- 无法在 SK 生态中组合（如 chaining、filtering）

---

### ✅ 真正用好 SK Skills（你的优化方向）
```python
# 1. 所有类型 → 动态注册为 kernel function
kernel.create_function_from_prompt(..., name="extract_invoice")
kernel.create_function_from_prompt(..., name="extract_id_card")

# 2. 统一调用方式
result = await kernel.invoke(kernel.plugins["Extractor"]["extract_invoice"], input=text)

# 3. 支持自动编排（未来可扩展）
planner = BasicPlanner()
plan = await planner.create_plan("Extract all info from this multi-page doc", kernel)
```

**这才是 Skills 的核心价值**。

---

## 🚀 二、Semantic Kernel Skills 的四大优越性（在你的场景中如何体现）

### 1. **标准化接口（Standardized Interface）**
> Skills 让所有文档提取行为 **看起来像同一个 API**，无论底层是文本还是图像。

✅ 你的收益：
- 主流程无需 `if doc_type == "id_card": ... else: ...`
- 调用方式统一：`kernel.invoke(plugin["extract_xxx"], input=content)`
- 未来加新类型，主逻辑 **完全不用改**

> 💡 这就是 **多态（Polymorphism）** 在 AI 函数中的体现。

---

### 2. **内核级功能集成（Kernel-native Features）**
SK 的 function 不是普通函数，而是 **带元数据、可插件化、可监控的智能单元**。

✅ 你的收益：
- **自动日志/遥测**：通过 `kernel.add_function_invoked_handler()` 监控每个 Skill 调用
- **统一重试/超时**：通过 `AzureChatCompletion` 配置全局策略
- **输入/输出过滤**：可加中间件做敏感信息脱敏、格式校验
- **上下文共享**：所有 Skill 共享同一个 `SKContext`，可传递全局变量（如 document_id）

```python
# 示例：给所有提取结果加上来源页码
async def log_page(context: SKContext):
    context.variables["page"] = current_page_index  # 可在 prompt 中用 {{$page}}
kernel.import_skill(MyLoggingSkill(), "Logger")
```

---

### 3. **声明式 Prompt + Schema 绑定（Declarative Prompt Engineering）**
你将 `prompt.txt` + `schema.json` 作为 **一个 Skill 的完整定义**，这正是 SK 推崇的 **“配置即代码”**。

✅ 你的收益：
- **Prompt 版本 = Skill 版本**：Git 提交即发布新技能
- **非程序员可维护**：业务专家只改 `.txt` 和 `.json`，不碰 Python
- **A/B 测试友好**：可并行注册 `extract_invoice_v1` / `v2`，动态路由

> 🔧 更进一步：用 **YAML** 定义 Skill（社区已有实践）：
```yaml
# skills/invoice/skill.yaml
name: extract_invoice
description: Extract invoice data
prompt: prompt.txt
output_schema: schema.json
input_type: text  # or image
```

---

### 4. **为未来 AI 编排打下基础（Future-proof for AI Agents）**
今天你手动分类 → 提取，但明天可能用 **SK Planner** 自动决策。

✅ 你的收益：
- 当前写的 Skill **无需修改**，即可被 Planner 调用
- 示例：用户说“处理这份混合文档”，Planner 自动调用 `classify_page` → `extract_invoice` → `extract_id_card`

```python
# 未来只需一行
plan = await kernel.create_plan("Process the uploaded document and return structured JSON")
result = await kernel.execute_plan(plan)
```

> 🌟 **Skills 是通往自主 Agent 的基石**。你现在做的，就是在构建“原子能力”。

---

## 🛠 三、如何“更好”使用提示词？—— SK 的高级技巧

### 技巧 1：用 **模板变量** 解耦逻辑与内容
不要硬拼 prompt，用 SK 的变量系统：

```txt
# prompt.txt
Extract data from the following {{$input_type}}:

{{$input}}

Respond in JSON matching this schema:
{{$schema}}
```

注册时注入变量：
```python
kernel.create_function_from_prompt(
    prompt=prompt_template,
    ...
    default_variables={
        "schema": json.dumps(schema),
        "input_type": "ID card image" if is_image else "OCR text"
    }
)
```

### 技巧 2：启用 **JSON Mode（GPT-4o 原生支持）**
在创建 service 时开启 strict JSON 输出：

```python
chat_service = AzureChatCompletion(
    ...
    response_format={"type": "json_object"}  # 👈 强制 JSON
)
```
> ⚠️ 注意：需确保 prompt 明确要求 JSON，否则可能出错。

### 技巧 3：用 **后处理 Filter** 做二次验证
```python
async def validate_json_output(invocation_context: FunctionInvocationContext):
    try:
        data = json.loads(invocation_context.result)
        jsonschema.validate(data, expected_schema)
    except Exception as e:
        invocation_context.result = f"ERROR: {str(e)}"

kernel.add_function_invoked_handler(validate_json_output)
```

---

## ✅ 总结：你的方案为何是“真·Skills 用法”

| 你做的事 | 对应 SK 核心理念 |
|--------|----------------|
| 每个文档类型 = 一个 prompt + schema | **Skill as a unit of capability** |
| 动态注册为 kernel function | **Standardized callable interface** |
| 主流程无类型分支 | **Polymorphism & decoupling** |
| 文件化管理提示词 | **Declarative AI engineering** |
| 保留扩展到 Planner 的可能 | **Agent-ready design** |

> 🎯 **Skills 的优越性不在于“存提示词”，而在于“把提示词变成可编程、可组合、可演进的智能服务”**。

如果你按这个思路继续，未来无论是加 **多模态理解**、**人工审核回流**、还是 **RAG 增强提取**，都能平滑演进。

需要我帮你把这套设计封装成一个 **可复用的 SK 插件模板** 吗？

### USER
再帮我加强点 能灵活一点走 adi 还是 base64 对于 prompt 文件 模板请给的更好一点比如 md 格式 而不是太简单的描述 影响结果稳定性 如果后续这些 skills 维护在 azure storage table 合理么

### ASSISTANT
非常好的进阶需求！你希望：

1. **更灵活地决定每页走 ADI（文本）还是 Base64 图像**（由文档类型 + 内容质量动态判断）  
2. **使用结构化、鲁棒的提示词模板（如 Markdown 格式）**，提升 LLM 输出稳定性  
3. **将 Skills（prompt + schema）存储在 Azure Table Storage**，实现远程配置、热更新、多环境管理  

下面我为你提供一套 **生产级增强方案**，融合 **动态输入路由 + 结构化提示模板 + 云端 Skill 管理**。

---

## ✅ 一、核心设计原则

| 目标 | 实现方式 |
|------|--------|
| **输入路由灵活** | 每个 Skill 声明 `input_mode: ["text", "image", "auto"]` |
| **提示词专业稳定** | 使用 **Markdown 模板**，含角色、约束、示例、输出格式 |
| **Skills 可远程管理** | 存储在 **Azure Table Storage**，支持版本、生效开关、A/B 测试 |
| **零代码扩展** | 新增/修改 Skill 无需部署 Function App |

---

## ✅ 二、Skill 配置结构（存储在 Azure Table）

### 表名：`DocumentSkills`

| PartitionKey | RowKey | PromptTemplate (string) | OutputSchema (JSON) | InputMode | IsActive | Version |
|--------------|--------|--------------------------|---------------------|-----------|----------|--------|
| invoice      | v1     | ```md ... ```            | `{...}`             | text      | true     | 1      |
| id_card      | v2     | ```md ... ```            | `{...}`             | image     | true     | 2      |
| bank_stmt    | v1     | ```md ... ```            | `{...}`             | auto      | true     | 1      |

> 🔹 `PartitionKey = doc_type`，`RowKey = version`  
> 🔹 `InputMode`:  
> - `text`: 强制用 ADI 文本  
> - `image`: 强制用 Base64 图像  
> - `auto`: 自动选择（根据 ADI 置信度或字段缺失判断）

---

## ✅ 三、专业级提示词模板（Markdown 格式）

以 `id_card` 为例（存储在 `PromptTemplate` 字段）：

```markdown
# Role
You are an expert ID document processor. Extract structured data with high precision.

# Input
- If input is base64 image: analyze the ID card visually.
- If input is text: use only the provided OCR result.

# Instructions
1. Extract ONLY the fields defined in the output schema.
2. Normalize dates to ISO format (YYYY-MM-DD).
3. If a field is unreadable or missing, set it to `null`.
4. DO NOT infer or guess values.
5. Respond ONLY with valid JSON—no explanations, no markdown.

# Output Format
Respond strictly in JSON matching this schema:
{{schema}}

# Examples
## Example 1 (Image Input)
Input: image/jpeg;base64,/9j/4AAQ...
Output:
{
  "full_name": "张三",
  "id_number": "11010119900307XXXX",
  "date_of_birth": "1990-03-07",
  "address": "北京市东城区...",
  "issue_date": "2015-08-20"
}

## Example 2 (Text Input)
Input: 姓名：李四 身份证号：31011519851212XXXX 出生：1985年12月12日
Output:
{
  "full_name": "李四",
  "id_number": "31011519851212XXXX",
  "date_of_birth": "1985-12-12",
  "address": null,
  "issue_date": null
}
```

> ✅ **优势**：
> - 清晰的角色定义 → 提升 LLM 专注度
> - 明确的输入/输出规则 → 减少幻觉
> - 包含正反例 → 引导格式和边界处理
> - 使用 `{{schema}}` 占位符 → 动态注入 JSON Schema

---

## ✅ 四、动态加载 Skills 从 Azure Table Storage

```python
# skill_manager.py
from azure.data.tables import TableServiceClient
import json

class AzureTableSkillManager:
    def __init__(self, connection_string: str, table_name: str = "DocumentSkills"):
        self.table_client = TableServiceClient.from_connection_string(connection_string).get_table_client(table_name)

    def get_active_skills(self) -> dict:
        """返回 {doc_type: {prompt, schema, input_mode}}"""
        skills = {}
        entities = self.table_client.query_entities("IsActive eq true")
        for entity in entities:
            doc_type = entity["PartitionKey"]
            skills[doc_type] = {
                "prompt_template": entity["PromptTemplate"],
                "schema": json.loads(entity["OutputSchema"]),
                "input_mode": entity["InputMode"],  # "text", "image", or "auto"
                "version": entity["Version"]
            }
        return skills
```

---

## ✅ 五、智能输入路由：text vs image？

```python
def decide_input_mode(page_text: str, image_bytes: bytes, skill_config: dict) -> tuple[str, str]:
    mode = skill_config["input_mode"]
    
    if mode == "text":
        return "text", page_text
    elif mode == "image":
        b64 = base64.b64encode(image_bytes).decode()
        return "image", f"image/jpeg;base64,{b64}"
    elif mode == "auto":
        # 启发式：如果 ADI 结果太短 or 缺关键字段 → 用图像
        if len(page_text.strip()) < 50 or "身份证" in page_text and "号码" not in page_text:
            b64 = base64.b64encode(image_bytes).decode()
            return "image", f"image/jpeg;base64,{b64}"
        else:
            return "text", page_text
    else:
        raise ValueError(f"Unknown input_mode: {mode}")
```

> 🧠 未来可替换为 **小模型分类器** 或 **ADI 置信度阈值**

---

## ✅ 六、注册动态 Skills 到 Semantic Kernel

```python
def register_skills_from_azure(kernel: sk.Kernel, skill_manager: AzureTableSkillManager):
    skills = skill_manager.get_active_skills()
    
    for doc_type, config in skills.items():
        # 渲染最终 prompt：将 {{schema}} 替换为实际 JSON
        final_prompt = config["prompt_template"].replace(
            "{{schema}}", 
            json.dumps(config["schema"], ensure_ascii=False, indent=2)
        )

        # 启用 GPT-4o JSON mode（确保输出合法）
        kernel.create_function_from_prompt(
            prompt=final_prompt,
            function_name=f"extract_{doc_type}",
            plugin_name="RemoteDocumentExtractor",
            description=f"Extract {doc_type} (v{config['version']})",
            # 关键：启用 strict JSON
            response_format={"type": "json_object"}
        )
```

---

## ✅ 七、主流程整合（Azure Function）

```python
async def main(req: func.HttpRequest) -> func.HttpResponse:
    # 1. 初始化
    kernel = create_kernel()  # 含 Azure OpenAI 配置
    skill_manager = AzureTableSkillManager(os.environ["AZURE_TABLE_CONN_STR"])
    
    # 2. 加载并注册远程 Skills
    register_skills_from_azure(kernel, skill_manager)
    
    # 3. 获取文档（PDF → pages + images）
    pages, images = await extract_pages_and_images(req.files["document"])
    
    # 4. 分类 + 提取（略，同前）
    results = await process_document_pages(kernel, pages, images, skill_manager)
    
    return func.HttpResponse(json.dumps(results))
```

---

## ✅ 八、为什么用 Azure Table Storage？合理吗？

| 优势 | 说明 |
|------|------|
| ✅ **低成本** | Table Storage 是 NoSQL，按请求计费，适合低频配置读取 |
| ✅ **高可用** | 内置 99.99% SLA，跨区域复制可选 |
| ✅ **结构化查询** | 支持 `IsActive eq true` 过滤，按 `PartitionKey` 快速检索 |
| ✅ **与 Azure 生态集成** | Function App 可直接用托管身份访问，无需密钥 |
| ✅ **支持版本控制** | 通过 `RowKey=version` 实现 A/B 测试、灰度发布 |

> ⚠️ 注意：**不要频繁读取**（可在 Function 启动时缓存，或加 Redis）。  
> 对于高并发场景，建议：
> - 启动时加载一次（冷启动可接受）
> - 或配合 **Azure App Configuration**（更适合配置管理）

---

## ✅ 九、进一步增强建议

1. **加缓存层**：用 `functools.lru_cache` 缓存技能配置，避免每次请求查表
2. **加监控**：记录每个 Skill 的调用成功率，自动降级到备用版本
3. **加审批流**：Skill 修改需经审批才设 `IsActive=true`
4. **支持多语言**：`PartitionKey = "invoice_zh"` / `"invoice_en"`

---

## ✅ 总结

你现在拥有的是一个 **企业级文档智能提取平台**：

- **提示词**：专业 Markdown 模板 + JSON Schema → 稳定输出  
- **输入路由**：按 Skill 配置智能选择 ADI 或 Base64  
- **Skills 管理**：Azure Table Storage → 远程、版本化、零部署更新  
- **架构扩展性**：无缝支持未来 Agent、RAG、人工审核等模块  

> 🎯 **这不仅是“用 SK”，而是“用 SK 构建可演进的 AI 产品”**。

需要我为你生成一个 **完整的 Azure Function + Table Storage 初始化脚本 + 示例数据** 吗？