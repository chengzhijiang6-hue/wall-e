# Auto-Index on Approve Pattern

When an MCP server manages a knowledge base with vector search, newly approved 
content should be indexed immediately so it's available for retrieval.

## Pattern: Chain index update into approve_diff

```python
from index_pipeline import update_index_for_page

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "approve_diff":
        # ... existing approve logic (read diff, write wiki page, delete diff) ...
        
        target_file.write_text(content, encoding="utf-8")
        diff_path.unlink()
        
        # Auto-update vector index
        try:
            chunk_count = update_index_for_page(target_file, _get_provider())
            index_msg = f", index updated ({chunk_count} chunks)"
        except Exception as e:
            index_msg = f", index update failed: {e}"
        
        return _result(f"Approved: {diff_filename} → {target_path}{index_msg}")
```

## Implementation (index_pipeline.py)

```python
def update_index_for_page(page_path: Path, provider=None) -> int:
    """Incremental update: delete old chunks for this page, add new ones."""
    provider = provider or get_provider()
    collection = _get_collection()
    rel_path = str(page_path.relative_to(WIKI_DIR))
    content = page_path.read_text(encoding="utf-8")
    
    # Remove old chunks for this page
    try:
        collection.delete(where={"source_wiki_page": rel_path})
    except Exception:
        pass
    
    # Chunk, embed, store
    chunks = _chunk_by_heading(content, rel_path)
    if not chunks:
        return 0
    
    texts = [c["text"] for c in chunks]
    ids = [f"{rel_path}#{c['metadata']['chunk_index']}" for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    
    collection.add(ids=ids, documents=texts, metadatas=metadatas)
    return len(chunks)
```

## Key Points

1. **Delete-then-add**: Remove all old chunks for the page, then add new ones. Simpler than diffing.
2. **Error isolation**: Index update failure should not block the approval. Catch exceptions and report in the response.
3. **Metadata carries source**: Each chunk's metadata includes `source_wiki_page` for targeted deletion and citation.
4. **Incremental vs full**: `update_index_for_page` for single-page changes, `build_index` for full rebuild.

## ChromaDB Collection Metadata Filter

```python
# Delete all chunks from a specific page
collection.delete(where={"source_wiki_page": "concepts/docker.md"})

# Query with metadata filter
results = collection.query(
    query_texts=["docker networking"],
    where={"source_wiki_page": {"$eq": "concepts/docker.md"}},
    n_results=3,
)
```
