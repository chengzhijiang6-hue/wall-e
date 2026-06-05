# Spec-Driven Development 使用指南

## 快速开始

### 1. 初始化项目规范结构

```bash
mkdir -p specs/
```

### 2. 创建项目宪法（一次性）

描述项目的核心原则和开发指南：

```
创建项目原则：
- 代码质量：严格的代码审查，90%+ 测试覆盖率
- 测试标准：TDD 开发，红-绿-重构循环
- 用户体验：一致性设计系统，响应式布局
- 性能要求：<200ms API 响应时间，<2s 页面加载
```

**输出**：`constitution.md`

### 3. 创建功能规范

描述要构建的功能，专注于"做什么"和"为什么"：

```
构建一个照片管理应用：
- 支持按日期自动分组的相册
- 相册可拖拽重组
- 照片以网格布局预览
- 支持批量操作（删除、移动、标签）
```

**输出**：`specs/###-feature-name/spec.md`

### 4. 创建实现计划

提供技术栈和架构选择：

```
技术栈：
- 前端：Vite + React + TypeScript
- 后端：FastAPI + Python 3.11
- 存储：PostgreSQL + S3
- 测试：pytest + Jest
```

**输出**：`specs/###-feature-name/plan.md`

### 5. 生成任务列表

自动从计划生成可执行任务：

**输出**：`specs/###-feature-name/tasks.md`

### 6. 执行实现

按任务列表逐步实现：

```
执行任务 T001-T005（Phase 1: Setup）
```

## 完整示例

### 用户输入

```
/speckit.specify 构建一个任务管理应用，支持：
- 创建、编辑、删除任务
- 任务分类和标签
- 优先级排序（P1/P2/P3）
- 截止日期和提醒
- 团队协作和分配
```

### Agent 输出

```markdown
# Feature Specification: Task Management App

## User Story 1 - Basic Task CRUD (Priority: P1)

As a user, I want to create, edit, and delete tasks so that I can manage my to-do list.

**Why this priority**: Core functionality, MVP requirement

**Independent Test**: Can be fully tested by creating, editing, and deleting tasks

**Acceptance Scenarios**:

1. **Given** I am on the task list page, **When** I click "Add Task", **Then** a new task form appears
2. **Given** I have a task, **When** I click "Edit", **Then** I can modify the task details
3. **Given** I have a task, **When** I click "Delete", **Then** the task is removed from the list
```

## 工作流命令

### /speckit.constitution — 创建项目原则

**输入**：项目原则描述
**输出**：`constitution.md`

**示例**：
```
/speckit.constitution 
核心原则：
1. 测试驱动开发（TDD）
2. 代码简洁性（KISS）
3. 不重复自己（DRY）
4. 模块化设计
5. 文档即代码
```

### /speckit.specify — 创建功能规范

**输入**：功能描述
**输出**：`specs/###-feature-name/spec.md`

**示例**：
```
/speckit.specify 
构建一个博客平台：
- 用户注册和登录
- 创建、编辑、发布文章
- 评论系统
- 标签和分类
- 搜索功能
```

### /speckit.plan — 创建实现计划

**输入**：技术栈选择
**输出**：`specs/###-feature-name/plan.md`

**示例**：
```
/speckit.plan 
技术栈：
- 前端：Next.js 14 + TypeScript
- 后端：Node.js + Express
- 数据库：PostgreSQL
- ORM：Prisma
- 部署：Vercel + Supabase
```

### /speckit.tasks — 生成任务列表

**输入**：无（自动从规范和计划生成）
**输出**：`specs/###-feature-name/tasks.md`

### /speckit.implement — 执行实现

**输入**：任务 ID 或范围
**输出**：代码实现

**示例**：
```
/speckit.implement T001-T005
```

## 最佳实践

### 1. 用户故事独立性

每个用户故事应该是独立的 MVP：
- 可独立开发
- 可独立测试
- 可独立部署
- 可独立演示

### 2. 优先级排序

- **P1**：核心功能，MVP 必需
- **P2**：重要功能，增强用户体验
- **P3**：锦上添花，可后续迭代

### 3. 验收场景

使用 Given/When/Then 格式：
```markdown
**Given** [初始状态]
**When** [用户操作]
**Then** [预期结果]
```

### 4. 并行任务标记

标记可并行执行的任务：
```markdown
- [ ] T003 [P] Configure linting
- [ ] T004 [P] Set up testing
```

## 目录结构

```
project/
├── constitution.md              # 项目宪法
├── specs/
│   ├── 001-user-auth/
│   │   ├── spec.md             # 功能规范
│   │   ├── plan.md             # 实现计划
│   │   ├── research.md         # 研究文档
│   │   ├── data-model.md       # 数据模型
│   │   ├── contracts/          # API 契约
│   │   └── tasks.md            # 任务列表
│   ├── 002-task-management/
│   │   └── ...
│   └── 003-blog-platform/
│       └── ...
└── src/                        # 源代码
```

## 常见问题

### Q: 规范和需求文档有什么区别？

A: 规范是**可执行的**，直接生成实现计划和任务列表。需求文档只是描述性的。

### Q: 用户故事优先级如何确定？

A: 基于业务价值和 MVP 需求。P1 是最小可行产品必需的功能。

### Q: 任务可以并行执行吗？

A: 是的，标记 [P] 的任务可以并行执行（不同文件，无依赖）。

### Q: 如何处理规范变更？

A: 更新规范文档，重新生成计划和任务列表。

## 扩展阅读

- [Spec Kit 官方文档](https://github.github.io/spec-kit/)
- [规范驱动开发方法论](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [社区扩展](https://github.github.io/spec-kit/community/extensions.html)
- [社区预设](https://github.github.io/spec-kit/community/presets.html)
