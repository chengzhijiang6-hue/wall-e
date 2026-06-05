# MCP Server ID Mismatch Analysis (2026-06-04)

## 问题背景

`mem0_delete` 工具返回 502 Bad Gateway，即使使用 `mem0_list` 返回的 ID。

## MCP Server 代码分析

**文件**: `/mnt/c/wsl/mem0/mcp-server/mem0_mcp_server.py`

### `_list_memories` 函数
```python
def _list_memories(user_id: str) -> list:
    r = _api_request("get", "/memories", params={"entity_id": user_id, "entity_type": "user"})
    # 返回的 ID 来自 Mem0 API，可能是向量数据库索引 ID
```

### `_delete_memory` 函数
```python
def _delete_memory(memory_id: str) -> list:
    r = _api_request("delete", f"/memories/{memory_id}")
    # 尝试删除时，PostgreSQL 中找不到该 ID
```

## 日志证据

```
# 成功删除（ID 在 PostgreSQL 中存在）
INFO: 172.20.0.1:48714 - "DELETE /memories/ab931ec2-d38e-40bf-9cf0-c6a36868ee93 HTTP/1.1" 200 OK

# 失败删除（ID 在 PostgreSQL 中不存在）
INFO: 172.20.0.1:46300 - "DELETE /memories/60010614-e3a8-46b4-9626-45514a19b2ad HTTP/1.1" 502 Bad Gateway
# 日志显示: ValueError: Memory with id 60010614-e3a8-46b4-9626-45514a19b2ad not found
```

## 架构图

```
MCP Server (59180)
    │
    ├─ _list_memories ──→ GET /memories?entity_id=ethan&entity_type=user
    │                         │
    │                         ▼
    │                    Mem0 API (59110)
    │                         │
    │                         ├─→ PostgreSQL (mem0_app)  ← 主存储
    │                         └─→ 向量索引 (pgvector)     ← 可能返回不同 ID
    │
    └─ _delete_memory ──→ DELETE /memories/{id}
                              │
                              ▼
                         PostgreSQL 查找 → "not found" → 502
```

## 解决方案

1. **Dashboard 删除**: http://localhost:59101 (Web UI，最可靠)
2. **search 获取正确 ID**: `mem0_search` 返回的 ID 可能是 PostgreSQL 的正确 ID
3. **直接 SQL 删除**: `docker compose exec postgres psql ...`

## 用户偏好

- 清理重复条目时，**必须先展示内容让用户决定**
- 重复条目保留规则：**以最新时间戳版本为准**
- 不要假设记忆中的日期是当前的（如 API key 过期日期）
