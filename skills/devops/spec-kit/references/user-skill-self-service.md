# 用户技能自选模式

## 需求

管理员在管理界面为用户配置技能不够——用户应该能自己选择技能。

## 实现方案

### 后端 API

```
GET  /api/v1/skills/available  — 列出所有可用技能（无需认证或需认证）
PUT  /api/v1/skills/user       — 更新当前用户的技能列表
GET  /api/v1/skills/user       — 获取当前用户的技能
```

PUT /api/v1/skills/user 接收：
```json
{"skills": ["docker-management", "hermes-agent", "spec-kit"]}
```

返回：
```json
{
  "user_id": "xxx",
  "skill_names": ["docker-management", "hermes-agent"],
  "loaded_skills": [...],
  "invalid_skills": ["spec-kit"],
  "message": "Updated skills: 2 valid, 1 invalid (skipped)"
}
```

### 前端实现

在用户详情模态框中添加"配置技能"按钮：
1. 点击按钮 → 弹出技能选择模态框
2. 加载 GET /admin/skills/overview 获取可用技能列表
3. 加载 GET /profile/me 获取用户当前技能
4. 渲染复选框列表（已选中的打勾）
5. 用户勾选/取消 → 点击保存 → PUT /skills/user

### 关键设计决策

- **技能验证**：后端验证每个技能名是否存在于文件系统，无效的跳过
- **Profile 依赖**：用户必须先创建 Profile 才能配置技能
- **管理员也能用**：管理员可以通过同样的 API 为自己配置技能
- **技能目录挂载**：Docker 容器需要挂载 `~/.hermes/skills` 目录

### CSS 样式

```css
.skills-checkbox-list {
    max-height: 350px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px;
}

.skill-checkbox-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 8px;
    border-bottom: 1px solid var(--border);
}

.skill-checkbox-item .skill-desc {
    display: block;
    font-size: 0.75rem;
    color: var(--text-secondary);
}
```
