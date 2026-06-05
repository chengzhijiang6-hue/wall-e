# LLM-Wiki 联动配置与工作流

## Docker 配置

### 容器信息
- 镜像: llm-wiki-llm-wiki (自建)
- 挂载: `/home/ethan/llm-wiki` → `/app/data`
- 端口: 18080
- 用户: 1000:1000

### 启动命令
```bash
docker run -d \
  --name llm-wiki \
  --env-file /home/ethan/llm-wiki/.env \
  -v /home/ethan/llm-wiki:/app/data \
  -p 18080:18080 \
  --user 1000:1000 \
  --restart unless-stopped \
  llm-wiki-llm-wiki
```

### .env 配置
```
LLM_PROVIDER=mimo
LLM_API_KEY=<mimo-key>
LLM_MODEL=mimo-v2.5-pro
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
EMBED_PROVIDER=dashscope
EMBED_API_KEY=<dashscope-key>
EMBED_MODEL=text-embedding-v3
DASHSCOPE_API_KEY=<dashscope-key>
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MCP_PORT=18080
HTTP_PROXY=http://10.197.216.7:3128
HTTPS_PROXY=http://10.197.216.7:3128
NO_PROXY=localhost,127.0.0.1
```

### providers.py DashScope 支持

在 `/app/src/providers.py` 中添加 DashScopeProvider 类（容器内修改后需 commit 或 bind mount）：

```python
class DashScopeProvider(BaseProvider):
    """阿里 DashScope — OpenAI 兼容接口。"""
    def __init__(self, api_key=None, base_url=None):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key or os.environ.get("DASHSCOPE_API_KEY", ""),
            base_url=base_url or os.environ.get("DASHSCOPE_BASE_URL", 
                "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            http_client=httpx.Client(proxy=_get_proxy()),
        )
        self.model = os.environ.get("DASHSCOPE_MODEL", "qwen-plus")
    
    def chat(self, messages, **kwargs):
        resp = self.client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        return resp.choices[0].message.content or ""
    
    def embed(self, texts):
        resp = self.client.embeddings.create(
            model=os.environ.get("EMBED_MODEL", "text-embedding-v3"), input=texts)
        return [item.embedding for item in resp.data]
```

工厂函数注册: `"dashscope": DashScopeProvider`

## Ingest 工作流

### 目录结构
```
/home/ethan/llm-wiki/
├── .env                    ← 环境变量
├── raw/docs/               ← 原始素材（Docker 挂载）
├── raw/docs/trouble/       ← 排错记录（单独目录）
├── wiki/concepts/          ← 生成的 wiki 页面
├── wiki/decisions/
└── data/                   ← 向量索引等
```

### MCP 工具调用顺序
1. `ingest_file("docs/文件名.md")` — 逐个 ingest
2. `review_diffs()` — 查看待审核 diff
3. `approve_all_diffs(dry_run=False)` — 批量通过
4. `build_index()` — 重建向量索引

### 数据溯源路径
```
Desktop/knowledge/PLMS数据梳理/PLMS-LLM-WIKI/  ← 精简版源头
  → /home/ethan/llm-wiki/raw/docs/              ← 复制到 raw
    → wiki/concepts/*.md                         ← LLM 生成 wiki
      → 向量索引                                  ← 语义检索
```

更新时只需修改 PLMS-LLM-WIKI/ 下的文件，复制到 raw 目录后重新 ingest。

## Frontmatter 元数据模式（提升检索质量的关键）

为 wiki 页面添加 YAML frontmatter 可显著提升 ask_wiki 检索质量。

### 格式
```yaml
---
views: ["LOI_V_OUTPUT_FULL"]
root_cause: "to_char占位符不足导致版本号乱码"
affected_tables: ["LOI_V_OUTPUT_FULL"]
severity: high
tags: ["oracle","to_char","output","monthly"]
---
```

### 效果对比
- 无 frontmatter: ask_wiki 只找到标题，给出通用推测
- 有 frontmatter: ask_wiki 找到具体根因和解决方案

### 适用场景
- 排错记录、故障案例、问题排查指南
- 需要精确匹配视图名、根因类型的关键文档

### 批量添加方法
```python
# 在 execute_code 中读取 wiki 页面
# 检查是否已有 frontmatter（以 ---\nviews: 开头）
# 如果没有，根据内容分析生成 frontmatter 并 prepend
# 关键：不要改正文内容，只加 frontmatter
```

### 三人小组讨论结论

关于"结构化 vs 自然语言"的讨论结论：
- **正方**：结构化提升向量检索精度，消除 LLM 编译损耗
- **反方**：结构化杀死语义多样性，维护成本高
- **架构师方案**：混合索引 — frontmatter 元数据 + 自然语言正文并存

最终采用：**只加 frontmatter，不改正文**。兼顾精确匹配和语义检索。

## Ingest 质量优化

### 核心原则
1. **每个排错记录单独 ingest**：合并后 LLM 只生成 1 个 wiki 页面，检索质量极差
2. **大文件拆分**：>100KB 的文件拆分为 <50KB 的子文件，按功能域分组
3. **添加 frontmatter**：排错记录必须有结构化元数据，否则 ask_wiki 只能给出通用回答

### Ingest Pipeline 参数（当前值）
```python
content[:8000]    # 原文截断 8000 字符
max_tokens=2048   # LLM 输出上限
```

这些参数对短文件（<5000 字符）影响不大，但 LLM 的"提炼关键知识"prompt 会导致细节丢失。

## Pitfalls

1. **ingest 超时**: 单文件 >100KB 可能超时（MCP 180s limit）。拆分为 <50KB。
2. **MCP 断连**: ingest_all 超时后 MCP 断开，等 ~60s 自动恢复。也可 `docker restart llm-wiki`。
3. **docker-compose v1 不兼容**: `ContainerConfig` KeyError。用 `docker run --env-file`。
4. **env 变更不生效**: 修改 .env 后必须 `docker run` 重建容器，`docker restart` 不会重读 env。
5. **search_wiki 精确匹配**: 英文关键词 OK，中文多词查询常失败。用 ask_wiki 做语义查询。
6. **ingest 合并问题**: 多个文件合并为 1 个文件 ingest 后，LLM 只提取部分记录摘要。每个文件单独 ingest。
7. **LLM ingest 摘要过短**: ingest pipeline 的 max_tokens=2048 且 prompt 要求"提炼关键知识"，导致排错记录的 root cause/solution 细节丢失。解决方案：添加 frontmatter 元数据。
8. **ask_wiki 合成质量**: 向量检索能找到正确的 wiki 页面，但 LLM 合成回答时倾向于给出通用表述。frontmatter 元数据能显著改善。
9. **嵌入模型可独立切换**: LLM 用 mimo，embedding 可用 DashScope text-embedding-v3。需在 providers.py 新增 DashScopeProvider 类。
10. **mimo-embedding 502 错误**: mimo 的 embedding 端点不稳定，返回 502 Bad Gateway。解决方案：切换到 DashScope text-embedding-v3。

## Quartz Wiki 可视化

Quartz 将 wiki/ 目录渲染为可浏览的静态网站，支持双向链接和全文搜索。

### Docker 部署
- 容器: quartz-wiki
- 挂载: `/home/ethan/llm-wiki/wiki` → `/usr/src/app/content`
- 端口: 1313 → 8080
- 访问: http://localhost:1313

### 目录结构规范

```
wiki/
├── index.md / overview.md / glossary.md / links.md  ← 导航页
├── plms/         ← PLMS 系统（视图定义 + 排错案例）
├── i4-platform/  ← I4.0 数据平台（视图定义 + 排错案例）
└── infra/        ← 基础设施（Docker/K8s/Dify）
```

**关键规则**:
1. 每个目录必须有 `index.md` 作为入口页，否则目录 404
2. 目录名不能含 `.`（如 `i4.0/` 会导致路由 404，Quartz 将点视为文件扩展名）。用连字符替代：`i4-platform/`
3. 分类原则：PLMS vs I4.0 按系统归属，两者关联通过 frontmatter 的 views/affected_tables 字段体现

### Quartz Pitfalls

1. **重复 frontmatter key 导致崩溃**: LLM 生成的 diff 中可能出现重复 `tags:` 等字段，Quartz 的 YAML 解析器报错 `duplicated mapping key` 并退出。已修复：`mcp_server.py` 新增 `_sanitize_frontmatter()` 函数，在 approve_diff/approve_all_diffs 写入文件前自动清理重复 key（保留第一个）。
2. **目录删除后缓存残留**: 删除 wiki 子目录（如 decisions/）后，Quartz 的 `public/` 中仍有旧文件（如 `public/decisions.gitkeep`），检测到变化重建时报 `ENOENT: unlink 'public/decisions.gitkeep'` 并退出。解决：`docker exec quartz-wiki rm -rf /usr/src/app/public/*` 清空缓存后重启。
3. **目录名含点号 404**: `i4.0/` 目录访问返回 404，因为 Quartz 路由将 `.0` 解析为文件扩展名。重命名为 `i4-platform/` 解决。
4. **每次修改文件后需重启**或等待 Quartz 自动检测重建（文件监控模式）。大改动后建议直接 `docker restart quartz-wiki`。
