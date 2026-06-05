# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Summary

[从规范提取：主要需求 + 技术方案]

## Technical Context

<!--  
  ACTION REQUIRED: 用项目实际技术细节替换以下内容  
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[基于 constitution.md 的检查点]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code

```text
[src structure based on project type]
```

## Phase 0: Research

**Goal**: Understand requirements, constraints, and existing solutions

**Activities**:
- [ ] 分析规范中的需求
- [ ] 研究现有解决方案
- [ ] 识别技术约束
- [ ] 评估可行性

**Output**: `research.md`

## Phase 1: Design

**Goal**: Define architecture, data model, and contracts

**Activities**:
- [ ] 设计系统架构
- [ ] 定义数据模型
- [ ] 设计 API 契约
- [ ] 创建快速启动指南

**Output**: `data-model.md`, `contracts/`, `quickstart.md`

## Phase 2: Implementation Planning

**Goal**: Break down into executable tasks

**Activities**:
- [ ] 生成任务列表
- [ ] 标记并行任务
- [ ] 分配用户故事

**Output**: `tasks.md`

## Phase 3: Implementation

**Goal**: Execute tasks systematically

**Activities**:
- [ ] 按任务列表执行
- [ ] 运行测试
- [ ] 验证验收场景

## Dependencies & Sequencing

[任务依赖关系和执行顺序]

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| [风险1] | [影响] | [缓解措施] |
| [风险2] | [影响] | [缓解措施] |

## Docker 部署评估（必须填写）

**是否需要 Docker 部署？** [是/否]

**架构方案**：
- [ ] CLI 本地运行 + API 容器化
- [ ] 全部容器化
- [ ] 其他：[说明]

**端口规划**：
| 服务 | 容器端口 | 宿主机端口 | 说明 |
|------|----------|------------|------|
| [服务名] | [端口] | [端口] | [说明] |

**Docker Compose 依赖**：
- [ ] 新增容器：[列表]
- [ ] 现有容器：[列表]
- [ ] 网络配置：[说明]
