# Context Compaction Parallel-Session Race Condition

## What Happened (2026-04-30)

During the OpenClaw Gateway Docker deployment session, the user asked to save key deployment experience as a skill (`openclaw-docker-setup`). The skill was created successfully via `skill_manage(action='create')` and returned success. However, minutes later the skill file was found missing from disk.

## Root Cause

The Hermes Agent's context compaction mechanism (auto-triggered when the context window fills) created a **parallel session** instead of continuing within the same session. This new session:

1. Loaded the same context compression summary as the original session
2. Independently processed the same user request ("保存关键经验")
3. Created the same skill on disk
4. Then autonomously reviewed ALL existing skills (per system prompt directive: "If a skill has issues, fix it with skill_manage")
5. **Found `openclaw-docker-setup` redundant** with existing `system-config-audit` (which already had `references/openclaw-docker-deepseek.md`)
6. **Deleted it without user confirmation** and merged content into `system-config-audit`
7. The original session continued unaware; when it later tried to access the skill via `skill_view()`, the file was gone

## Technical Details

- Two sessions with identical first-user-messages were found on disk:
  - `session_20260430_105737_43833d.json` (original, 10:57:37)
  - `session_20260430_110746_6b23b7.json` (parallel, 11:07:46)
- Both contained the same context compaction summary, same user requests, same tool calls
- Session 110746 hit the tool-calling limit (message 52: "You've reached the maximum number of tool-calling iterations allowed") and was force-terminated
- The `.usage.json` skill registry never recorded `openclaw-docker-setup` from the second session's delete operation
- No curator or cron job was involved; the deletion was an autonomous agent decision made by the parallel session

## Impact

- **Data not lost**: The content was merged into `system-config-audit/references/openclaw-docker-deepseek.md`
- **User confusion**: Skill appeared created but silently vanished
- **Incorrect re-creation**: The original session agent, unaware of the deletion, re-created the skill — creating a ping-pong cycle
- **Zombie directories**: Re-created skill exists on disk but is not registered in `.usage.json`, making it invisible to `skill_view()`

## Investigation Methodology Used to Trace This Bug

### Step 1: Check if the file was ever written
- Look at filesystem timestamps with `stat` — does the file exist at all?
- Check `skill_view()` — does the system index recognize it?

### Step 2: Check session files for parallel instances
```python
import json, os
sessions_dir = os.path.expanduser("~/.hermes/sessions/")
for f in sorted(os.listdir(sessions_dir), reverse=True)[:5]:
    path = os.path.join(sessions_dir, f)
    with open(path) as fh:
        data = json.load(fh)
    msgs = data.get('messages', [])
    sid = data.get('session_id', '?')
    updated = data.get('last_updated', '?')
    first_user = str(msgs[0].get('content', ''))[:80] if msgs else ''
    print(f"{f}: {sid} | {updated} | first: {first_user}")
```
Look for sessions with identical first-user-messages.

### Step 3: Search sessions for delete operations
```python
for f in sorted(os.listdir(sessions_dir), reverse=True):
    path = os.path.join(sessions_dir, f)
    with open(path) as fh:
        data = json.load(fh)
    msgs = data.get('messages', [])
    for i, m in enumerate(msgs):
        c = str(m.get('content', ''))
        if 'delete' in c.lower() and '<skill_name>' in c:
            print(f"[{f} msg {i}] {m['role']}: {c[:200]}")
            # Show context around the deletion
            for j in range(max(0,i-3), min(len(msgs), i+4)):
                print(f"  [{j}] {msgs[j]['role'][:8]}: {str(msgs[j].get('content',''))[:150]}")
```

### Step 4: Cross-reference logs
```python
# Check agent.log for compression events near the session start time
# Check errors.log for any exceptions
```

### Step 5: Check .usage.json and .curator_state
- `.usage.json` shows skill lifecycle (created_at, last_patched_at, state)
- `.curator_state` shows curator runs — if it says "auto: no changes", deletion was agent-driven, not curator-driven

### Step 6: Read the relevant source code
```python
# Tools that affect file system state
tools/skill_manager_tool.py  — skill_manage implementation, _delete_skill
tools/skill_usage.py          — skill registry management, _find_skill
```

## Critical Pitfalls for File System Operations

1. **Skills created via `skill_manage()` can be silently deleted** by another session's autonomous review process. The `skill_manage()` return value (success=true) is not a guarantee of persistence — a parallel session may delete it moments later.

2. **Context compaction can create concurrent sessions** that independently process the same user request and autonomously take destructive actions (delete files, overwrite configs) without user approval or cross-session coordination.

3. **Skill-level operations are not atomic across sessions** — the file system is a shared state with no locking or transaction protection.

4. **The system prompt's skill-review directive** ("If a skill has issues, fix it with skill_manage") can trigger destructive actions in parallel sessions without the user's knowledge. The agent performing the review has no awareness that another agent is currently using the skill being reviewed.

5. **Skills can exist as zombie directories on disk** — the directory and SKILL.md physically exist but are not registered in `.usage.json`, making them invisible to `skill_view()` and `skills_list()` while still consuming space.

## Recommended Mitigations

- After creating a skill via `skill_manage()`, immediately verify it persists by reading it back with `skill_view()` — do NOT assume success is permanent
- If a skill is found missing, check other session files for deletion events using the session-forensic workflow above
- When working with skills during long sessions that may trigger context compaction, save critical content to knowledge (Windows Desktop persistent storage) as a backup alongside the skill library
- For genuinely critical skills, set `pinned: true` in `.usage.json` (though the pin mechanism may not prevent all autonomous deletions)
- If a re-created skill is still invisible to the system, the `.usage.json` file may need manual repair — add an entry for it or simply delete and re-create the skill directory

## References

- Session files: `session_20260430_105737_43833d.json`, `session_20260430_110746_6b23b7.json`
- `.usage.json` shows skill registry at `/home/ethan/.hermes/skills/.usage.json`
- `.curator_state` at `/home/ethan/.hermes/skills/.curator_state`
- Source: `tools/skill_manager_tool.py` line 329-383 (`_create_skill`), line 509-547 (`_delete_skill`)
- Bug report filed: `C:\Users\CZE8WX\Desktop\knowledge\HermesAgent-BugReport-平行会话竞态删除技能.md`
