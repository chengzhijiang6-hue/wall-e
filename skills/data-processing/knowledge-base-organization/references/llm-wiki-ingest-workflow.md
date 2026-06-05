# LLM-Wiki Ingest Workflow

## 容器配置

- Docker 挂载: `/home/ethan/llm-wiki` → `/app/data`
- MCP 端口: 18080
- 原始素材: `raw/docs/` 目录
- Wiki 页面: `wiki/concepts/`, `wiki/decisions/`, `wiki/entities/`
- 向量索引: 自动生成

## Embedding 模型配置

mimo-embedding 端点不稳定（502 Bad Gateway），已切换到 DashScope text-embedding-v3。

`.env` 关键配置：
```
LLM_PROVIDER=mimo          # LLM 用 MiMo
EMBED_PROVIDER=dashscope   # Embedding 用 DashScope
EMBED_MODEL=text-embedding-v3
DASHSCOPE_API_KEY=<key>
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

需要自定义 DashScopeProvider（providers.py 中添加），使用 OpenAI 兼容客户端。

DashScopeProvider 核心实现：
```python
class DashScopeProvider(BaseProvider):
    def __init__(self, api_key=None, base_url=None):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key or os.environ.get("DASHSCOPE_API_KEY", ""),
            base_url=base_url or os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            http_client=httpx.Client(proxy=_get_proxy()),
        )
        self.model = os.environ.get("DASHSCOPE_MODEL", "qwen-plus")

    def embed(self, texts):
        resp = self.client.embeddings.create(
            model=os.environ.get("EMBED_MODEL", "text-embedding-v3"),
            input=texts,
        )
        return [item.embedding for item in resp.data]
```

注册到 `get_provider()` 的 providers dict 中：`"dashscope": DashScopeProvider`。

**容器更新步骤**：
1. 编辑 providers.py 添加 DashScopeProvider
2. `docker cp providers.py llm-wiki:/app/src/providers.py`
3. `docker stop llm-wiki && docker rm llm-wiki`
4. `docker run -d --name llm-wiki --env-file .env -v /home/ethan/llm-wiki:/app/data -p 18080:18080 --user 1000:1000 --restart unless-stopped llm-wiki-llm-wiki`

## Ingest 流程

### 1. 准备文件
将精简后的 .md 文件复制到 `/home/ethan/llm-wiki/raw/docs/`

### 2. 批量 Ingest（3 个一组，避免超时）

每次并行提交 3 个 `ingest_file` 调用，等待完成后再提交下一组。

```
mcp_LLM_WIKI_ingest_file(file_path="docs/file1.md")
mcp_LLM_WIKI_ingest_file(file_path="docs/file2.md")
mcp_LLM_WIKI_ingest_file(file_path="docs/file3.md")
# 等待 3 个都返回后继续
```

**绝对不要用 `ingest_all`** — 文件多时会超时（180s 限制），且会导致 MCP 服务断连。
单文件也可能超时（>100KB），需控制文件大小或拆分。

处理顺序：先小文件（<30KB），后大文件（30-130KB）。

### 3. 批量审核
```
mcp_LLM_WIKI_approve_all_diffs(dry_run=False)
```

### 4. 重建向量索引
```
mcp_LLM_WIKI_build_index()
```

### 5. 验证
```
mcp_LLM_WIKI_check_health()   # 确认页面数和索引状态
mcp_LLM_WIKI_search_wiki(query="关键词")  # 测试检索
mcp_LLM_WIKI_ask_wiki(question="业务问题")  # 测试合成回答
```

## 更新流程

1. 修改 `项目-LLM-WIKI/` 下的源文件
2. 复制到 `raw/docs/`
3. 重新 ingest 该文件（会覆盖旧 diff）
4. approve + rebuild index

## Pitfalls

- `ingest_all` 超时后 MCP 服务会断连，需要等待 ~60s 才能恢复
- docker-compose v1 与新版 Docker 不兼容（ContainerConfig KeyError），用 `docker run` 替代
- .env 修改后必须 recreate 容器（`docker stop && docker rm && docker run --env-file .env`），restart 不生效
- 大文件（>100KB）的 ingest 耗时较长，但一般不会超时
- ask_wiki 的回答质量取决于 chunks 切分，过大的文件可能切分不佳
- MCP 超时断连后需等待 ~60s 恢复，或 `docker restart llm-wiki` + 等待 30s
- 用户说"重连"时 = MCP 断了，等 60s 后 check_health 确认恢复
- 用户说"重试"时 = 对进度不满，加快节奏，减少分析轮次
