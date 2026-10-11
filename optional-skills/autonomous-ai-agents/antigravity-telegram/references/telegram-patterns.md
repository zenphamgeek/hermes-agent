# Telegram Patterns for Antigravity Coding Bridge

Reference material for agent-side handling of Telegram constraints when
delivering `agy` coding output.

## Message Chunking (4096-char limit)

Telegram enforces a hard 4096-character limit per message. The agent must
chunk any output exceeding this before delivery.

### Chunking procedure

1. Split output on newline boundaries (never mid-line).
2. Each chunk ≤ 4000 chars (leave 96 chars for prefix/suffix markers).
3. Prefix each chunk with `[1/N]`, `[2/N]`, etc.
4. If total chunks > 5, switch to **file upload** mode instead.

### File upload fallback

For large diffs (>20KB or >5 chunks):

```
terminal(command="git diff > /tmp/hermes-agy-diff-$(date +%s).patch", workdir=workdir)
```

Then send the `.patch` file as a Telegram document attachment.

## Inline Keyboard Patterns

Use Telegram inline keyboards for interactive decisions:

### Approve / Reject changes

When `agy` completes and the user needs to decide:

```
✅ agy completed — 3 files changed (+47/-2)

[👍 Apply] [👎 Revert] [📋 Show Diff]
```

Button callbacks:
- `apply` → `terminal(command="git add -A && git commit -m '<summary>'")`
- `revert` → `terminal(command="git checkout -- .")`
- `show_diff` → send chunked diff

### Continue / Stop for long runs

During heartbeat updates:

```
🔧 agy running (5m00s)
└─ Last: Refactoring auth module

[⏹ Stop] [⏭ Let it run]
```

## Screenshot Capture

For visual verification (UI changes, terminal output):

```
terminal(command="import -window root /tmp/hermes-screenshot-$(date +%s).png")
```

Or using `scrot` / `gnome-screenshot` if available. Send the image as a
Telegram photo attachment.

Note: this only works on machines with a display server. Headless servers
should skip screenshot functionality.

## Session State Management

### Per-user session tracking

Each Telegram user maintains their own coding session state:

```
{
  "user_id": 123456789,
  "active_session": {
    "process_id": "bg-agy-abc123",
    "workdir": "<project-dir>",
    "started_at": "2026-08-23T08:30:00Z",
    "model": "Gemini 3.1 Pro (High)",
    "prompt": "Add health check endpoint"
  },
  "default_workdir": "<project-dir>",
  "preferences": {
    "heartbeat_interval": 60,
    "auto_diff": true,
    "model": "Gemini 3.1 Pro (High)"
  }
}
```

### Thread/topic isolation

If Telegram topics are enabled, each topic can run an independent `agy`
session. The agent tracks `(user_id, topic_id)` as the session key.

### Concurrency

Multiple `agy` sessions can run in parallel across different projects
(worktree fan-out). The agent tracks each by `process_id` and reports
status per session when queried.

## Heartbeat Format

Compact heartbeat template (must stay under 200 chars):

```
🔧 agy [{elapsed}] {status_emoji}
└─ {last_action_truncated_to_100_chars}
```

Status emojis:
- 🔧 Running
- ✅ Completed
- ❌ Failed
- ⏸ Paused (waiting for input)
- ⏱ Timing out soon (>80% of timeout elapsed)

## Error Message Format

```
❌ agy error [{elapsed}]
├─ Exit: {exit_code}
├─ Error: {last_error_line_truncated}
└─ 💡 {suggestion}
```

Common suggestions:
- Exit 1 + "authentication": "Run `agy` locally first to complete auth"
- Exit 1 + "not found": "Check that the project path exists on the server"
- Timeout: "Increase timeout with `--timeout 20m`"
