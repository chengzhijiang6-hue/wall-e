---
name: one-three-one-rule
category: communication
description: Structured decision-making framework for technical proposals and trade-off analysis. 1 recommendation, 3 trade-offs, 1 action.
triggers:
  - user faces a choice between multiple approaches
  - architecture decisions, tool selection, refactoring strategies
  - user asks for a recommendation with reasoning
  - any decision with meaningful trade-offs
tags:
  - communication
  - decision-making
  - proposals
  - trade-offs
---

# 一三一规则 (1-3-1 Rule)

结构化决策框架，用于技术方案选型和权衡分析。

## 适用场景

当面临多个可选方案时（架构决策、工具选型、重构策略、部署方案等），
使用此框架输出结构化建议，避免罗列式平铺。

## 输出格式

严格按以下结构输出：

### 1 — 推荐方案

明确给出 1 个推荐方案，用一句话概括核心理由。
不要说"取决于场景"——如果信息足够，必须做出选择。

示例：
> 推荐方案：使用 Docker Compose 部署。理由：当前单机环境，Compose
> 足以覆盖编排需求，无需引入 K8s 的运维复杂度。

### 3 — 关键权衡

列出 3 个最重要的权衡点（pros/cons/risks），每个点：
- 用一句话说明事实
- 标注影响程度：高/中/低

示例：
> 1. [低] Compose 不支持自动水平扩展，但当前单机无此需求
> 2. [中] 学习成本低，团队已有 Docker 经验
> 3. [高] 未来迁移到 K8s 需重写编排文件，但 YAML 结构可复用

### 1 — 行动建议

给出 1 个明确的下一步行动，可直接执行。

示例：
> 下一步：创建 docker-compose.yml，包含当前 3 个服务定义，
> 配置 healthcheck 和 restart policy，今天内完成部署验证。

## 规则

1. 如果信息不足以做出推荐，明确指出缺少什么信息，而不是模糊推荐
2. 权衡点必须是真实的差异，不要列出所有方案都具备的优点
3. 行动建议必须具体到可执行，不能是"继续调研"之类的空话
4. 全文控制在 200 字以内，精炼为王
