# DashScope Provider for llm-wiki

## 背景
mimo-embedding 端点不稳定（返回 502 Bad Gateway），需要备用 embedding 方案。
DashScope 的 text-embedding-v3 通过 OpenAI 兼容端点访问，稳定可用。

## 环境变量 (.env)
```
LLM_PROVIDER=mimo                    # LLM 保持用 MiMo
EMBED_PROVIDER=dashscope             # Embedding 切换到 DashScope
EMBED_MODEL=text-embedding-v3
DASHSCOPE_API_KEY=<dashscope-api-key>
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## providers.py 中添加的类

```python
class DashScopeProvider(BaseProvider):
    """阿里 DashScope — OpenAI 兼容接口，支持 qwen 系列和 text-embedding-v3。"""

    def __init__(self, api_key: str = None, base_url: str = None):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key or os.environ.get("DASHSCOPE_API_KEY", ""),
            base_url=base_url or os.environ.get("DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            http_client=httpx.Client(proxy=_get_proxy()),
        )
        self.model = os.environ.get("DASHSCOPE_MODEL", "qwen-plus")

    def chat(self, messages, **kwargs):
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, **kwargs,
        )
        return resp.choices[0].message.content or ""

    def embed(self, texts):
        resp = self.client.embeddings.create(
            model=os.environ.get("EMBED_MODEL", "text-embedding-v3"),
            input=texts,
        )
        return [item.embedding for item in resp.data]
```

## get_provider() 工厂函数更新

```python
providers = {
    "mimo": MiMoProvider,
    "deepseek": DeepSeekProvider,
    "gemini": GeminiProvider,
    "dashscope": DashScopeProvider,  # 新增
}
```

## 容器更新步骤

```bash
# 1. 编辑 providers.py
# 2. 复制到容器
docker cp providers.py llm-wiki:/app/src/providers.py
# 3. 更新 .env
# 4. Recreate 容器（restart 不会重新加载 env）
docker stop llm-wiki && docker rm llm-wiki
docker run -d --name llm-wiki \
  --env-file /home/ethan/llm-wiki/.env \
  -v /home/ethan/llm-wiki:/app/data \
  -p 18080:18080 \
  --user 1000:1000 \
  --restart unless-stopped \
  llm-wiki-llm-wiki
```

## Pitfalls
- DashScope API key 需要单独设置，不是 MIMO 的 key
- mimo-v2.5-pro 的 embedding 端点 (`mimo-embedding`) 和 LLM 端点是分开的，LLM 正常但 embedding 502
- docker-compose v1 与新版 Docker 不兼容（ContainerConfig KeyError），必须用 `docker run`
