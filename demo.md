```python

import os
import requests
from flask import Flask, request, jsonify, stream_with_context, Response
import json
from functools import wraps

app = Flask(__name__)

# 从环境变量获取配置
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_OPENAI_RESOURCE = os.getenv("AZURE_OPENAI_RESOURCE")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")

def require_env_vars(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        required_vars = [
            "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
            "AZURE_OPENAI_RESOURCE"
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            return jsonify({
                "error": "Missing environment variables",
                "missing": missing
            }), 500
        return f(*args, **kwargs)
    return decorated

def get_azure_token():
    """获取Azure AD访问令牌"""
    token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "scope": "https://cognitiveservices.azure.com/.default"
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

@app.route('/v1/chat/completions', methods=['POST'])
@require_env_vars
def chat_completions():
    try:
        # 获取Azure访问令牌
        access_token = get_azure_token()

        # 构建Azure OpenAI请求
        azure_url = f"https://{AZURE_OPENAI_RESOURCE}.openai.azure.com/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"

        # 转换请求体（开源UI发送的是标准OpenAI格式）
        payload = request.json

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # 转发请求到Azure OpenAI
        azure_response = requests.post(
            azure_url,
            json=payload,
            headers=headers,
            stream=request.args.get('stream') == 'true'
        )

        # 检查响应状态
        azure_response.raise_for_status()

        # 如果是流式响应，直接流式转发
        if request.args.get('stream') == 'true':
            return Response(
                stream_with_context(azure_response.iter_content(chunk_size=1024)),
                content_type=azure_response.headers['Content-Type']
            )

        # 非流式响应，直接返回JSON
        return jsonify(azure_response.json())

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "Azure OpenAI Proxy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

```

```bash

pip install flask requests python-dotenv
flask run --port=5000

# 使用Docker部署（最简单方式）
docker run -d -p 3000:8080 \
  -e OPENAI_API_KEY=dummy \
  -e OPENAI_API_BASE_URL=http://your-proxy-host:5000/v1 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main

docker run -d -p 3001:3001 \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_BASE_URL=http://your-proxy-host:5000/v1 \
  -e OPENAI_API_KEY=dummy \
  -v anything-llm:/app/server/storage \
  --name anything-llm \
  mintplexlabs/anything-llm:latest

git clone https://github.com/mckaywrigley/chatbot-ui.git
cd chatbot-ui
npm install
# 修改 .env 文件中的 OPENAI_API_BASE_URL=http://your-proxy-host:5000/v1
npm run dev

```
