# Lint / Quality Check Pipeline Pattern

When an MCP server manages user-facing content (wiki pages, docs, configs),
a quality-check tool catches structural issues before they accumulate.

## Architecture

```
Content files → Rule engine → Issue list → Report (markdown file + MCP response)
```

## Issue Object Design

Use a structured Issue class with severity levels and rule IDs for traceability:

```python
class Issue:
    def __init__(self, level: str, rule: str, message: str, file: str, line: int = 0):
        self.level = level  # ERROR / WARN / INFO
        self.rule = rule    # e.g., "L-001", "W-003"
        self.message = message
        self.file = file
        self.line = line

    def __str__(self):
        loc = f"{self.file}:{self.line}" if self.line else self.file
        return f"[{self.level}] {self.rule} — {loc}: {self.message}"
```

## Rule Categories

| Level | Purpose | Examples |
|-------|---------|---------|
| ERROR | Must fix, blocks quality | Missing required fields, invalid structure |
| WARN | Should fix, degrades quality | Broken links, empty sections, orphan content |
| INFO | Metrics, no action needed | Word count, last update date |

## Rule ID Convention

Prefix by severity: `L-xxx` for structural rules, `W-xxx` for quality warnings,
`I-xxx` for informational. Numbers are sequential within each prefix.

## Report Generation

Save reports as timestamped markdown files for historical tracking:

```python
REPORTS_DIR = data_dir / "var" / "reports"

def run_lint() -> str:
    all_issues = []
    for file in sorted(wiki_dir.rglob("*.md")):
        all_issues.extend(lint_page(file, all_files))

    errors = [i for i in all_issues if i.level == "ERROR"]
    warns = [i for i in all_issues if i.level == "WARN"]

    # Build markdown report
    report = f"# Quality Report\nErrors: {len(errors)} | Warnings: {len(warns)}\n..."
    
    # Save to disk
    report_file = REPORTS_DIR / f"lint_{timestamp}.md"
    report_file.write_text(report)
    
    return report  # Also returned via MCP tool
```

## Common Check Functions

### Frontmatter Validation
```python
def _parse_frontmatter(content: str) -> tuple[dict, int]:
    if not content.startswith("---"):
        return {}, 0
    end = content.find("---", 3)
    # Parse YAML-like key: value pairs
```

### Heading Level Checks
```python
def _find_heading_issues(content: str) -> list[Issue]:
    prev_level = 0
    for i, line in enumerate(content.split("\n"), 1):
        m = re.match(r'^(#{1,6})\s+', line)
        if m:
            level = len(m.group(1))
            if level > prev_level + 1:  # Skip level
                issues.append(Issue("ERROR", "L-003", f"Skip: h{prev_level}→h{level}", "", i))
            prev_level = level
```

### Broken Link Detection
```python
def _find_broken_links(content: str, all_pages: set) -> list[Issue]:
    for m in re.finditer(r'\[\[([^\]]+)\]\]', content):
        target = m.group(1)
        if not any(target.lower() in p.name.lower() for p in all_pages):
            issues.append(Issue("WARN", "W-002", f"Broken: [[{target}]]", "", line_num))
```

### Orphan Page Detection
```python
def _check_orphan(file_path: Path, all_files: list[Path]) -> bool:
    page_name = file_path.stem
    for other in all_files:
        if other == file_path:
            continue
        content = other.read_text()
        if f"[[{page_name}]]" in content:
            return False  # Found a reference
    return True  # No references → orphan
```

## MCP Integration

Register as a single tool that returns the full report:

```python
Tool(
    name="run_lint",
    description="Quality check all content pages",
    inputSchema={"type": "object", "properties": {}},
)

# In call_tool:
elif name == "run_lint":
    report = run_lint()
    return [TextContent(type="text", text=report)]
```

## Key Design Points

1. **Rule IDs enable filtering**: Users can suppress specific rules
2. **Line numbers in output**: Makes fixes actionable
3. **Report persistence**: Timestamped files for trend tracking
4. **Non-blocking**: Lint issues don't prevent content operations
5. **Cross-file checks**: Orphan detection and link validation require scanning all files
