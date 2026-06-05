# Docker 部署检查清单

在 Plan 阶段必须完成此检查，否则实施阶段会架构返工。

## 检查项

1. **哪些组件容器化？哪些本地运行？**
   - CLI 工具通常本地运行
   - API/数据库服务通常容器化
   - 本地 CLI 通过 HTTP 调用 Docker API

2. **端口规划**：检查 `docker ps` 确认已用端口，推荐 59000+

3. **网络通信**：Docker 内部网络 vs 宿主机网络
   - CLI 访问 Docker 服务：`localhost:<port>`
   - 跨容器访问：`host.docker.internal:<port>`
   - 代理配置：Dockerfile 中设置 HTTP_PROXY

4. **数据持久化**：哪些需要卷挂载
   - 数据库数据
   - 配置文件
   - 技能目录（~/.hermes/skills）

5. **健康检查**：各服务是否有可用的 health endpoint

## 常见问题

- Docker 内无 `~/.hermes/skills/` 目录 → 需卷挂载
- Mem0 无 `/health` 端点 → 用 `/memories` 代替
- 代理导致 apt/pip 下载失败 → Dockerfile 中设置代理
- Python 模块路径错误 → WORKDIR + ENV PYTHONPATH
- UUID 序列化 → Pydantic v2 中 id 字段用 uuid.UUID 类型
