# MCP Tool Consumer Patterns — llm-wiki Case Study

Lessons learned from consuming MCP tools as an LLM agent. These patterns apply to any MCP server with search/read/query tools.

## Tool Priority for Query-Type MCP Servers

When an MCP server exposes multiple query tools, use this priority:

1. **Keyword search** (e.g. `search_wiki`) — most reliable, exact match
2. **Direct read** (e.g. `read_wiki_page`) — when you know the path
3. **Semantic/LLM query** (e.g. `ask_wiki`) — last resort, may miss results

### Why Keyword Search Beats Semantic Search

Semantic search (vector embeddings + LLM synthesis) can fail to match queries that keyword search handles trivially. Example: querying "Dify的配置" — `ask_wiki` returned "没有具体内容" while `search_wiki` found 11 matches.

**Rule of thumb**: Always try keyword search first. Fall back to semantic search only when keyword search returns nothing.

## Query Flow Pattern

```
User question
  → keyword search for relevant terms
  → found matches? 
    → yes: read full page for details
    → no: try semantic search, or check filesystem directly
```

## Pitfall: Don't Skip to Raw Files

When MCP query returns "no content, only references":
- ❌ Wrong: go read raw source files directly
- ✅ Right: check if processed wiki/content pages exist on disk first

The MCP's semantic search may simply not have indexed the content yet, but the processed files may already exist.

## Pitfall: MCP Tools Return Summaries

MCP tool responses are often summaries/truncated. If you need full content (markdown formatting, related pages, metadata), follow up with a direct read tool call.

## Applicable MCP Servers

These patterns were validated against:
- **llm-wiki** (port 18080): `search_wiki`, `read_wiki_page`, `ask_wiki`
- Any MCP server with search + read + ask tool tiers
