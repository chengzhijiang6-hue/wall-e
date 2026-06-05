---
name: spec-kit
category: devops
description: Spec-Driven Development workflow — define specs before code, generate plans and tasks, then implement systematically.
triggers:
  - user asks to create a feature specification
  - user wants structured development workflow
  - user mentions spec-driven development
  - user wants to plan a software feature systematically
  - user asks for technical comparison or decision analysis
  - user starts a multi-phase project
  - user asks about Docker deployment feasibility
---

# Spec-Driven Development Skill

基于 GitHub Spec Kit 的规范驱动开发工作流，包含三 Agent 协作执行模式。

## 核心理念

规范先行，分步骤精炼，而非一次性代码生成。

## 工作流程

### 阶段 1: 创建项目宪法 (Constitution)
定义项目治理原则和开发指南。输出: `constitution.md`

### 阶段 2: 创建功能规范 (Specify)
定义用户故事（P1/P2/P3 优先级）和验收场景（Given/When/Then）。输出: `spec.md`

### 阶段 3: 创建实现计划 (Plan)
选择技术栈，包含 **Docker 部署可行性分析**。输出: `plan.md`

### 阶段 4: 生成任务列表 (Tasks)
按用户故事分组，并行标记 [P]。输出: `tasks.md`

### 阶段 5: 执行实现 (Implement)
按任务列表实现。推荐使用三 Agent 协作模式（见下文）。

## 三 Agent 协作执行模式

用户偏好的项目执行方式。适用于多人/多模块项目。

| Agent | 职责 | 工具集 |
|-------|------|--------|
| 汇总 Agent (Coordinator) | 整合成果、生成报告、维护文档 | file, session_search, memory |
| 监督 Agent (Supervisor) | 审查代码、检测异常、纠正偏差 | terminal, file |
| 实施 Agent (Implementer) | 编码、部署、测试 | terminal, file, execute_code |

**工作流**：
```
汇总分配任务 → 实施执行 → 监督审查 → 汇总记录 → 循环
```

**监督 Agent 触发条件**：
- 任务超时（> 预估 200%）
- 测试失败、配置错误、语法错误
- 安全漏洞

**Pitfall — 子代理中断**：`delegate_task` 的超时（600s）或网络中断会导致子代理被截断。应对：
- 监督 Agent 被中断 2 次后，汇总 Agent 直接接管审查
- 子代理写入的文件即使中断也已落盘，可检查后继续
- 不要重复重试被中断的子代理 >2 次，改为直接执行

## 三 Agent 技术选型头脑风暴

用户偏好的技术决策方式：派发 3 个子代理从不同角度独立分析，然后汇总。

**示例**：
```python
delegate_task(tasks=[
    {"goal": "从技术架构师角度分析...", "toolsets": ["terminal"]},
    {"goal": "从产品经理角度分析...", "toolsets": ["terminal"]},
    {"goal": "从成本分析师角度分析...", "toolsets": ["terminal"]},
])
```

## Docker 部署前置检查

在设计阶段（Phase 3 Plan）必须评估 Docker 兼容性。用户会问"这些都能在 Docker 环境中部署运行吗"，不能等用户提醒。

1. 哪些组件容器化，哪些本地运行（CLI 通常本地）
2. CLI 如何与 Docker API 通信（HTTP localhost:端口）
3. 端口规划与现有服务协调
4. Docker 内部网络 vs 宿主机网络（代理、host.docker.internal）

## 多 Session 项目进度快照

当项目跨多个 Session 时（用户说"下周一继续"），启动记忆空间管理：

**memory 中**只记录项目路径和进度摘要（≤200 字符），完整内容写入文件。
**文件**保存到 `specs/<feature>/progress-snapshot.md`，包含：
- 已完成/待完成阶段
- 已创建文件清单
- API 端点清单
- 遇到并修复的问题
- 下次启动步骤

**记忆空间管理**：Memory 有 2200 字符上限。合并重复条目，精简冗长描述，删除已过时的内容。

**记忆存储分工**（用户明确要求）：
- **MCP Mem0**：用户偏好、项目信息、工作规范 — 可语义搜索，支持多用户隔离
- **本地 MEMORY.md**：系统配置、环境变量、代理规则、API 密钥位置 — 系统级硬性规则

不要把所有信息都存本地 MEMORY.md。用户偏好和项目知识应该同步到 Mem0。用户明确批评过"那我给你配置mcp的mem0有什么用，你全部记载本地干嘛"。

## 多用户 Profile 系统模板

基于 Multi-User Profile System 项目的完整实现经验，整理了可复用的模板。详见：
- [多用户架构模式](references/multi-user-architecture.md)
- [多用户系统模板](references/multi-user-template.md)
- [多用户项目示例](references/multi-user-project-example.md)
- [管理面板增强模式](references/admin-dashboard-pattern.md)
- [用户技能自选模式](references/user-skill-self-service.md)

实施 Agent 可能生成有语法错误的代码（如 `/mnt/c/wsl/.../multi_user/` 项目中 settings.py 第 47-48 行代码被截断）。监督 Agent 必须：
1. 用 `python3 -c "compile(open('file.py').read(), 'file.py', 'exec')"` 验证语法
2. 用 `patch` 修复后发现 lint 报错时，直接 `write_file` 重写整段
3. 不要只检查文件是否存在，要检查语法和逻辑

## 系统概览仪表板增强模式

当管理员需要更详细的信息时，按此顺序分阶段增强系统概览页面：

| Phase | 内容 | API |
|-------|------|-----|
| Phase 1 | 服务器信息 + 当前用户 + 修复记忆统计 | 扩展 GET /admin/stats |
| Phase 2 | 按用户记忆统计（带缓存 5min TTL） | GET /admin/memory/stats |
| Phase 3 | 技能总览 + 用户技能配置 | GET /admin/skills/overview |
| Phase 4 | 动态健康检查（DB/Redis/Mem0 ping） | GET /admin/health-detailed |
| Phase 5 | 记忆归属详情 | 增强 memory/stats |

通用 Pitfall：Mem0 可能没有 `/health` 端点，需用 `/memories` 或其他实际端点代替。

## GitLab 上传与脱敏

项目开发完成后上传到 GitLab 时，必须执行脱敏流程。详见 `git-gitlab-push` 技能。

**关键步骤**：
1. 配置代理：`git config http.proxy http://10.197.216.7:3128`
2. 脱敏检查：`grep -rn "password\|secret\|api_key\|10.197\|bosch\|apac" . --include="*.py" --include="*.yaml" --include="Dockerfile"`
3. Dockerfile 中的代理配置必须删除（构建时不需要，运行时更不需要）
4. 提供 `.env.example` 替代硬编码密码

**彻底清除历史**（orphan 分支）：
```bash
git checkout --orphan clean-main
git add -A
git commit -m "feat: initial commit"
git branch -D master
git branch -m clean-main master
git push --force origin master
```

## 模板文件

- [规范模板](references/spec-template.md)
- [计划模板](references/plan-template.md)
- [任务模板](references/tasks-template.md)
- [使用指南](references/usage-guide.md)
- [三 Agent 协作模式](references/three-agent-pattern.md)
- [管理面板增强模式](references/admin-dashboard-pattern.md)
- [Docker 部署检查清单](references/docker-review-checklist.md)
- [多用户架构模式](references/multi-user-architecture.md)
- [多用户系统模板](references/multi-user-template.md)
- [多用户项目示例](references/multi-user-project-example.md)
- [实施经验总结](references/implementation-experience.md)
- [用户技能自选模式](references/user-skill-self-service.md)
