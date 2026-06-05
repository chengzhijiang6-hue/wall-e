# LLM-Backed MCP Tool Pattern

When an MCP tool needs to call an LLM (e.g., knowledge base Q&A, content generation),
follow this pattern for clean context assembly and error handling.

## Pattern: ask_wiki (Context from Filesystem + LLM Call)

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "ask_wiki":
        question = arguments.get("question", "")
        provider = _get_provider()

        # 1. Collect context from filesystem
        context_parts = []
        if WIKI_DIR.exists():
            for wiki_file in sorted(WIKI_DIR.rglob("*.md")):
                text = wiki_file.read_text(encoding="utf-8")[:2000]  # Truncate per file
                context_parts.append(f"=== {wiki_file.name} ===\n{text}")
        context = "\n\n".join(context_parts[:5]) or "(Knowledge base empty)"

        # 2. Assemble prompt with context + question
        prompt = f"""You are a knowledge base assistant. Answer based on the content below.
If no relevant information exists, say so explicitly.

## Knowledge Base Content
{context}

## Question
{question}
"""
        # 3. Call LLM
        answer = provider.chat([{"role": "user", "content": prompt}], max_tokens=1024)
        return [TextContent(type="text", text=answer)]
```

## Key Design Decisions

1. **Filesystem as context source**: Read wiki/ files directly. No vector DB needed for small KBs.
2. **Truncation**: Limit per-file content (`[:2000]`) and total files (`[:5]`) to stay within token budget.
3. **Max tokens**: Use >= 512 for reasoning models (MiMo), >= 1024 for Q&A responses.
4. **Graceful empty state**: If no wiki files exist, return a clear message instead of error.

## Pitfall: Reasoning Model Token Budget

Models like MiMo consume `reasoning_tokens` from the `max_tokens` budget. 
If max_tokens=20, the model may spend 19 on reasoning and return empty content.

**Rule**: Always use `max_tokens >= 512` for reasoning models. Prefer 1024-2048 for Q&A.

## Evolution Path

This filesystem-scan approach works for small knowledge bases (<50 pages). 
For larger KBs, evolve to:
1. Vector index (ChromaDB) with embedding-based retrieval (Phase 3 of llm-wiki)
2. Retrieve top-K chunks → assemble context → call LLM
3. Keep the same prompt structure, just change the context source

Implemented pattern: see [Vector retrieval + LLM synthesis](references/vector-retrieval-pattern.md)
