# Vector Retrieval + LLM Synthesis Pattern

When the knowledge base grows beyond what fits in a single LLM context window,
use vector retrieval to find relevant chunks before calling the LLM.

## Architecture

```
User question → Embed query → ChromaDB search (top-K) → Assemble context → LLM answer
```

## Implementation (query_pipeline.py)

```python
import chromadb
from providers import get_provider

COLLECTION_NAME = "wiki_chunks"

def _get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION_NAME)

def retrieve(query: str, top_k: int = 5) -> list[dict]:
    collection = _get_collection()
    if collection.count() == 0:
        return []
    # ChromaDB handles embedding internally via its default function
    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks

def synthesize_answer(question: str, chunks: list, provider=None) -> str:
    provider = provider or get_provider()
    if not chunks:
        return "No relevant content found in knowledge base."
    
    # Each chunk carries source metadata for citation
    context_parts = []
    for i, chunk in enumerate(chunks):
        source = chunk["metadata"].get("source_wiki_page", "unknown")
        section = chunk["metadata"].get("section_title", "")
        header = f"[Chunk {i+1}] Source: {source}"
        if section:
            header += f" / Section: {section}"
        context_parts.append(f"{header}\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_parts)
    prompt = f"""Answer based on the retrieved chunks below. Cite sources (e.g., "According to [Chunk 1]...").
If insufficient, state what's missing.

## Retrieved Chunks
{context}

## Question
{question}
"""
    return provider.chat([{"role": "user", "content": prompt}], max_tokens=2048)

def ask_with_retrieval(question: str, provider=None) -> str:
    chunks = retrieve(question, top_k=5)
    return synthesize_answer(question, chunks, provider)
```

## Key Design Decisions

1. **ChromaDB default embedding**: Uses ONNX MiniLM L6 v2 locally — no external API needed for embeddings.
2. **Metadata per chunk**: `source_wiki_page`, `section_title`, `chunk_index`, `source_raw` — enables citation.
3. **query_texts vs query_embeddings**: Let ChromaDB handle embedding internally via `query_texts=[query]`.
4. **Top-K = 5**: Balances relevance vs context window usage.

## Evolution

- Small KB (<50 pages): Direct filesystem scan + LLM (no vector DB)
- Medium KB (50-5000 pages): Vector retrieval + LLM (this pattern)
- Large KB (>5000 pages): Hybrid search (vector + keyword) + reranking
