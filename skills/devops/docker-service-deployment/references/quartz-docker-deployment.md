# Quartz Docker 部署 — Obsidian 兼容知识库可视化

## 概述

Quartz 4 是专为 Obsidian Vault 设计的静态站点生成器，支持双向链接 `[[...]]`、图谱视图、全文搜索。
适合将 llm-wiki 的 wiki/ 目录可视化为 Web 知识库。

## 部署步骤

### 1. 克隆 Quartz

```bash
cd ~/project
git clone --depth 1 https://github.com/jackyzha0/quartz.git quartz
```

### 2. 不要复制内容，直接挂载源目录

> **关键教训**：不要 `cp -r wiki/* quartz/content/`。
> 复制后 wiki/ 新增的文件不会自动同步到 quartz/content/，导致 Quartz 内容过时。
> 正确做法是启动容器时直接挂载 wiki/ 目录（见步骤 7）。

```bash
# ❌ 错误：复制后新增文件不会同步
cp -r wiki/* quartz/content/

# ✓ 正确：启动时直接挂载 wiki/ 目录（见步骤 7）
```

### 3. 创建 index.md 首页

Quartz 要求 content/ 根目录有 index.md，否则 404：

```markdown
---
title: 知识库
---
# 知识库
- [[overview]]
- [[glossary]]
```

### 4. 修改 quartz.config.ts

```typescript
const config: QuartzConfig = {
  configuration: {
    pageTitle: "LLM Wiki",
    pageTitleSuffix: " | 知识库",
    locale: "zh-CN",
    baseUrl: "localhost:1313",  // 本地部署
    // ...
  },
}
```

### 5. 禁用 CustomOgImages 插件

quartz.config.ts 中注释掉 `Plugin.CustomOgImages()`：
```typescript
// Plugin.CustomOgImages(),  // 需要下载 Google Fonts，公司代理环境下会失败
```

**原因**：CustomOgImages 需要从 Google Fonts 下载字体，在公司代理环境下 fetch 失败导致构建崩溃。

### 6. Dockerfile 添加代理支持

```dockerfile
FROM node:22-slim AS builder
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
WORKDIR /usr/src/app
COPY package.json .
COPY package-lock.json* .
RUN npm ci

FROM node:22-slim
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/ /usr/src/app/
COPY . .
CMD ["npx", "quartz", "build", "--serve"]
```

### 7. 构建并启动

```bash
cd quartz
docker build \
  --build-arg HTTP_PROXY=http://10.197.216.7:3128 \
  --build-arg HTTPS_PROXY=http://10.197.216.7:3128 \
  -t quartz-wiki .

docker run -d --name quartz-wiki \
  -p 1313:8080 \
  -v ~/project/wiki:/usr/src/app/content \
  -e HTTP_PROXY=http://10.197.216.7:3128 \
  -e HTTPS_PROXY=http://10.197.216.7:3128 \
  quartz-wiki
```

**关键**：
- Quartz 内部监听 8080 端口（不是 1313），所以端口映射是 `1313:8080`
- 挂载 wiki/ 而非 quartz/content/，这样 wiki/ 新增文件实时可见，无需重启容器

### 8. 验证

```bash
curl --noproxy '*' -s http://localhost:1313/ | grep '<title>'
# 应返回: <title>知识库 | 知识库</title>
```

## 重启与健康检查

当 quartz-wiki 容器 Exited 时，标准重启流程：

```bash
[1/4] 启动容器
  $ docker start quartz-wiki

[2/4] 等待构建完成（Quartz 需要重新编译 .md → HTML）
  $ sleep 5

[3/4] 检查容器状态 + HTTP 响应
  $ docker ps --filter "name=quartz-wiki" --format "{{.Status}}"
  $ curl -s -o /dev/null -w "%{http_code}" http://localhost:1313

[4/4] 验证页面内容
  $ curl -s http://localhost:1313 | grep '<title>'
```

**退出码含义**：
- Exit (0): 正常停止（docker stop 或 SIGTERM）
- Exit (1): 异常退出，检查 `docker logs quartz-wiki --tail 30`
  - 日志中 `npm error signal SIGTERM` = 正常关闭信号，不是错误
  - 日志中 `npm error command failed` = 构建/启动失败，需排查

## 页面同步

Quartz 在启动时编译 content/ 下所有 .md 文件为静态 HTML。如果 llm-wiki 新增了 wiki 页面但 Quartz 未显示：

```bash
# 重启容器触发重新构建
docker restart quartz-wiki

# 验证页面数
docker logs quartz-wiki 2>&1 | grep "Parsed.*Markdown files"
```

## Quartz 构建失败：YAML Frontmatter 修复

### 常见根因

Quartz 使用 YAML 解析 frontmatter，对格式敏感。最常见的错误是 **duplicated mapping key**（重复的 mapping key），通常是 `tags:` 字段出现两次：

```
 ERROR
Failed to process markdown `content/concepts/xxx.md`: duplicated mapping key (11:1)

  8 | root_cause: "SQL空值过滤导致GIT数据丢失"
  9 | affected_tables: ["LTAP_LTAK_POE"]
 10 | severity: high
 11 | tags: ["git","data-loss","sql", ...
------^
```

### 原因

LLM-Wiki 的 ingest 流程可能生成带重复 `tags:` 行的 frontmatter（第 1 行使用中文列表格式 `tags: [PLMS, 排错]`，第 2 行使用英文数组格式 `tags: ["git","data-loss"]`）。

### 批量检测与修复

```bash
# [1/3] 检测所有有重复 tags 的文件
grep -rn "^tags:" /path/to/wiki/ | awk -F: '{print $1}' | sort | uniq -c | sort -rn | awk '$1 > 1 {print $2}'

# [2/3] 修复脚本保留第一个 tags 行，删除后续重复
python3 << 'PYEOF'
import os
wiki_dir = "/path/to/wiki"
for root, dirs, files in os.walk(wiki_dir):
    for fn in sorted(files):
        if not fn.endswith('.md'): continue
        fpath = os.path.join(root, fn)
        with open(fpath, 'r', encoding='utf-8') as f: content = f.read()
        if not content.startswith('---'): continue
        parts = content.split('---', 2)
        if len(parts) < 3: continue
        fm_lines = parts[1].split('\n')
        tags_indices = [i for i, line in enumerate(fm_lines) if line.strip().startswith('tags:')]
        if len(tags_indices) > 1:
            for idx in sorted(tags_indices[1:], reverse=True): fm_lines.pop(idx)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(f'---{"\\n".join(fm_lines)}---{"---".join(parts[2:])}')
            print(f"Fixed: {fn}")
PYEOF

# [3/3] 重启 Quartz 并验证
docker stop quartz-wiki && docker start quartz-wiki
sleep 8
docker logs quartz-wiki --tail 5  # 应显示 "Done processing N files" 无 ERROR
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:1313  # 应返回 200
```

### 修复后仍然报错的排查

1. 确认挂载是 bind mount：`docker inspect quartz-wiki --format '{{json .Mounts}}'`
2. 容器内验证文件内容：`docker exec quartz-wiki grep "^tags:" /usr/src/app/content/concepts/file.md`
3. 确认日志来自当前启动，而非旧启动残留：
   - `docker inspect quartz-wiki --format '{{.State.StartedAt}}'` 确认启动时间
   - `docker logs quartz-wiki --tail 5` 看最新行
   - 最新日志显示 `Started a Quartz server listening` 则运行正常，旧 ERROR 只是日志残留

### Pitfall：日志中的旧错误可能误导

`docker logs` 保留容器整个生命周期的所有输出。重启后旧的 ERROR 行不会自动清除。如果最新几行显示成功，说明当前运行正常。判断依据是 `Started a Quartz server listening` 而非看日志中是否有 ERROR。

## Pitfalls

| 问题 | 原因 | 解决 |
|------|------|------|
| 构建时 npm ci 超时 | Docker build 不继承宿主代理 | 传 `--build-arg HTTP_PROXY=...` |
| CustomOgImages fetch failed | Google Fonts 被代理阻断 | 注释掉该插件 |
| 首页 404 | 缺少 content/index.md | 创建 index.md |
| 端口 1313 无响应 | Quartz 监听 8080 | 映射 `1313:8080` |
| 内容更新不生效 | 复制内容到 content/ 后新增文件不同步 | 挂载 wiki/ 直接到容器：`-v ./wiki:/usr/src/app/content` |
| 页面数比 llm-wiki 少 | Quartz 构建时快照 content/，新增文件需重建 | `docker restart quartz-wiki` 触发重新构建（挂载模式下自动读取新文件） |
| 容器 Exited (1) 重启后 HTTP 000 | Quartz 需要几秒构建 + 启动 HTTP 服务 | 等待 5 秒后再 curl 检查 |

## Quartz 启用的功能

- 双向链接 `[[...]]` — ObsidianFlavoredMarkdown 插件
- 图谱视图 — Component.Graph()
- 全文搜索 — Component.Search()
- 反向链接 — Component.Backlinks()
- 暗色/亮色模式 — Component.Darkmode()
- 目录导航 — Component.Explorer()
