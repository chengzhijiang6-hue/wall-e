# LLM-Wiki MCP Server Management

## Overview

llm-wiki is a Docker-based MCP server that ingests documents, generates wiki pages via LLM, and provides vector search + LLM synthesis (ask_wiki).

Container: `llm-wiki` | Image: `llm-wiki-llm-wiki` | Port: 18080
Data mount: `/home/ethan/llm-wiki` → `/app/data`

## Embedding Provider Fix

**Problem**: mimo-embedding endpoint returns 502 Bad Gateway.
**Fix**: Switch to DashScope text-embedding-v3.

1. Update `.env`:
```
EMBED_PROVIDER=dashscope
EMBED_MODEL=text-embedding-v3
DASHSCOPE_API_KEY=<key>
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

2. Add DashScope provider class to `providers.py` (container `/app/src/providers.py`):
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
    # chat() and embed() use standard OpenAI client pattern
```

3. Register in `get_provider()` factory: `"dashscope": DashScopeProvider`

4. Restart container: `docker stop llm-wiki && docker rm llm-wiki && docker run -d ...`

## Pitfall: docker-compose v1 ContainerConfig Error

**Symptom**: `KeyError: 'ContainerConfig'` when running `docker-compose up -d`
**Cause**: docker-compose v1 (1.29.2) incompatible with newer Docker Engine
**Fix**: Use `docker run` directly instead of docker-compose:
```bash
docker stop llm-wiki && docker rm llm-wiki
docker run -d --name llm-wiki \
  --env-file /home/ethan/llm-wiki/.env \
  -v /home/ethan/llm-wiki:/app/data \
  -p 18080:18080 \
  --user 1000:1000 \
  --restart unless-stopped \
  llm-wiki-llm-wiki
```

## Pitfall: env_file Not Picked Up on Recreate

**Symptom**: Container env vars show old values after editing `.env`
**Cause**: `docker-compose up -d` recreates container but may not reload env_file
**Fix**: Always `docker rm` + `docker run --env-file` to ensure fresh env.

## Ingest Pipeline Architecture

```
raw/docs/*.md  →  extract_text()  →  LLM compile (generate_wiki_page)  →  diff/*.md
                                                                         ↓
                                                              approve_diff → wiki/*.md
                                                                         ↓
                                                              build_index → vector chunks
```

### Key Parameters (in ingest_pipeline.py)

```python
content[:8000]    # Input truncation (chars)
max_tokens=2048   # LLM output limit
```

### Ingest Workflow for Large Knowledge Bases

1. Split source files by functional domain (10-50KB each)
2. Remove DDL noise (PCTFREE, STORAGE, TABLESPACE etc.)
3. Copy to `/home/ethan/llm-wiki/raw/docs/`
4. Ingest in batches of 3 (MCP timeout 180s per file)
5. `approve_all_diffs(dry_run=false)`
6. `build_index()`

### Pitfall: ingest_all Timeout

**Symptom**: `ingest_all` times out for 30+ files
**Fix**: Ingest files one by one via `ingest_file`, batches of 3.

## Quality Optimization

### Problem: ask_wiki returns generic answers instead of specific facts

**Root cause ranking**:
1. LLM synthesis quality (70%) - ask_wiki's final LLM picks generic phrasing
2. Wiki page structure (25%) - ingest generates prose summaries, not structured facts
3. Token limits (5%) - rarely the bottleneck for short source files

### Solution: Frontmatter Metadata

Add structured metadata to wiki pages without changing content:
```yaml
---
views: [LOI_V_OUTPUT_FULL]
root_cause: "to_char placeholder insufficient"
affected_tables: [LOI_V_OUTPUT_FULL, INVENTORY_ALL]
tags: [output, data-missing, oracle-bug]
---
```

This enables:
- Precise matching via search_wiki (text match on metadata fields)
- Better LLM synthesis (structured fields guide answer generation)
- Preserves natural language in body (semantic richness for vector search)

### vs Full Manual Structuring

| Approach | Pros | Cons |
|----------|------|------|
| Full manual structure | Zero info loss, precise | 16+ hours for 33 records, kills semantic diversity |
| Frontmatter only | Best of both worlds | Still requires manual work |
| LLM ingest only | Zero effort | Info loss, generic summaries |

**Recommendation**: Frontmatter metadata for high-value records (5-10), LLM ingest for the rest.

## Vector Index Stats

- 81 wiki pages → ~483 vector chunks
- Embedding: DashScope text-embedding-v3
- search_wiki: exact text matching (works well for English keywords, poor for Chinese multi-word)
- ask_wiki: vector search + LLM synthesis (good for semantic queries)

## References
- Provider code: `/app/src/providers.py`
- Ingest pipeline: `/app/src/ingest_pipeline.py`
- Query pipeline: `/app/src/query_pipeline.py`
- Config: `/home/ethan/llm-wiki/.env`
