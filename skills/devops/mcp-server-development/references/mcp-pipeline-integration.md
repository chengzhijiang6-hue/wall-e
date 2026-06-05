# MCP Server + Pipeline Module Integration Pattern

When building an MCP server that wraps existing pipeline logic (ingest, index, query, etc.), 
separate concerns cleanly:

## Directory Layout (inside container)

```
/app/
├── src/                    # COPY'd at build time (frozen until rebuild)
│   ├── mcp_server.py       # MCP server — tool definitions + dispatch
│   ├── providers.py        # LLM provider abstraction
│   ├── ingest_pipeline.py  # Business logic
│   └── ...
└── data/                   # Volume mount (always current from host)
    ├── raw/                # Input files
    ├── wiki/               # Output files
    ├── diff/               # Pending reviews
    ├── var/                # Runtime state
    └── src/                # Mirror of host src/ (for testing)
```

## Import Strategy

In `mcp_server.py`, add the src directory to sys.path so it can import sibling modules:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from providers import get_provider
from ingest_pipeline import process_single_file, ingest_all, RAW_DIR, WIKI_DIR, DIFF_DIR
```

## Lazy Global Provider

Avoid creating the LLM client on every tool call. Use a module-level lazy singleton:

```python
_provider = None

def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_provider()
    return _provider
```

## Tool-to-Pipeline Wiring

Each MCP tool is a thin dispatcher. Business logic lives in the pipeline module:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "ingest_file":
        file_path = arguments.get("file_path", "")
        full_path = RAW_DIR / file_path
        if not full_path.exists():
            return _result(f"Error: file not found — {full_path}")
        try:
            ok = process_single_file(full_path, _get_provider())
            return _result(f"Done" if ok else "Skipped (unchanged)")
        except Exception as e:
            return _result(f"Failed: {e}")
    # ... other tools
```

## Testing During Development

Since source is COPY'd at build time, use volume-mounted copies for rapid iteration:

```bash
# Test using host-mounted source (always current)
docker exec <container> python /app/data/src/ingest_pipeline.py --file docs/test.md

# After confirming works, rebuild to bake into image
docker-compose down && docker-compose up -d --build
```

## Pitfall: sys.path Must Match Runtime Context

When running scripts via `docker exec ... python /app/data/src/foo.py`, the `__file__` 
path is `/app/data/src/foo.py`, so `os.path.dirname(__file__)` correctly resolves to 
`/app/data/src/`. But when the MCP server runs from `/app/src/mcp_server.py` (COPY'd), 
the dirname is `/app/src/`. Both work because each resolves sibling imports from their 
own directory — just be aware the two copies may have different code if you haven't rebuilt.
