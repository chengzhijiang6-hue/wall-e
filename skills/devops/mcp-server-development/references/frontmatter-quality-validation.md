# Frontmatter Quality Validation for LLM-Generated Content

## Problem

When MCP tools use LLMs to generate structured content (wiki pages with YAML frontmatter, configuration files, etc.), the LLM occasionally produces **duplicate keys** in the frontmatter:

```yaml
---
title: "Page Title"
tags: [category1, category2]
tags: [tag1, tag2]   # ← DUPLICATE! LLM writes this
---
```

## Root Cause

LLMs are instructed to follow a template (e.g., `wiki-page.md` template with frontmatter fields). However, the model may:
- Re-emit tags it sees in the template PLUS generate a second set
- Append additional frontmatter fields when context contains multiple examples
- Misunderstand "fill in the template" as "append new fields to existing frontmatter"

This is an **LLM output quality issue**, not a template design problem.

## Impact

- **Static site generators** (Quartz, Hugo, Jekyll) fail on YAML parse errors → container crashes
- **Linters** report errors for duplicate mapping keys
- **Downstream tools** that parse frontmatter silently use either the first or last value (unpredictable)

## Solution: Sanitize Before Write

Add a `_sanitize_frontmatter()` function called **immediately before writing** the file:

```python
def _sanitize_frontmatter(content: str) -> str:
    """清理 frontmatter 中的重复 key，保留第一个出现的值。"""
    if not content.startswith("---"):
        return content  # No frontmatter, nothing to clean
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content  # Malformed, don't touch
    frontmatter, body = parts[1], "---".join(parts[2:])
    lines = frontmatter.split("\n")
    seen_keys = {}
    for i, line in enumerate(lines):
        m = __import__("re").match(r"^(\w+)\s*:", line)
        if m:
            key = m.group(1)
            seen_keys.setdefault(key, []).append(i)
    remove_indices = []
    for key, indices in seen_keys.items():
        if len(indices) > 1:
            remove_indices.extend(indices[1:])
    for idx in sorted(remove_indices, reverse=True):
        lines.pop(idx)
    new_fm = "\n".join(lines)
    return f"---{new_fm}---{body}"
```

## Integration Points

Call this function at every write path:

```python
# In approve_diff (single file):
content = _sanitize_frontmatter(content)
target_file.write_text(content, encoding="utf-8")

# In approve_all_diffs (batch):
content = _sanitize_frontmatter(content)
target_file.write_text(content, encoding="utf-8")
```

## Verifying the Fix

Test with real-world duplicate patterns:

```python
# Test: duplicate tags
test = "---\ntitle: Test\ntags: [a, b]\ntags: [c, d]\n---\n# Content"
result = _sanitize_frontmatter(test)
assert result.count("tags:") == 1

# Test: no duplicates (no-op)
test = "---\ntitle: Test\ntags: [a, b]\n---\n# Content"
result = _sanitize_frontmatter(test)
assert result == test

# Test: multiple duplicate keys
test = "---\ntags: [a]\ntags: [b]\ntags: [c]\nviews: [v1]\nviews: [v2]\n---\n# Content"
result = _sanitize_frontmatter(test)
assert result.count("tags:") == 1
assert result.count("views:") == 1
```

## Related

- `references/llm-backed-tool-pattern.md` — general pattern for LLM-backed tools
- Quartz static site: sensitive to frontmatter quality, crashes on duplicate YAML keys
