---
name: antigravity-telegram
description: Drive Antigravity coding sessions remotely via Telegram.
version: 0.1.0
author: Pham Vu Thang (zenpham), Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Coding-Agent
    - Antigravity
    - Telegram
    - Remote
    - Vibe-Coding
    related_skills:
    - antigravity-cli
---
# Antigravity–Telegram Coding Bridge

Orchestrate `agy` (Antigravity CLI) coding sessions through the Hermes
Telegram gateway. Start, monitor, review, and stop coding tasks from your
phone. This skill does NOT wrap a network API — it teaches the agent the
procedure for bridging `terminal`-driven `agy` commands with Telegram message
delivery.

## When to Use

- User sends a coding prompt from Telegram and wants `agy` to execute it
- Monitoring a long-running `agy` coding session from a phone
- Reviewing diffs, build output, or test results via Telegram messages
- Multi-project worktree fan-out triggered from Telegram
- User says "code from Telegram", "remote agy", "vibe code from phone"

Don't use for:
- Local `agy` sessions where the user is at their terminal (use `antigravity-cli`)
- Non-coding Telegram interactions (normal Hermes chat)
- Tasks better served by `codex` or `claude-code` (choose the right backend)

## Prerequisites

- `agy` binary on PATH: `terminal(command="command -v agy && agy --version")`
- Telegram bot configured with `TELEGRAM_BOT_TOKEN` in `~/.hermes/.env`
- `TELEGRAM_ALLOWED_USERS` set (security: only authorized users can trigger code)
- Hermes gateway running: `hermes gateway start`
- Target project directory accessible on the host machine

## How to Run

All commands below are initiated from Telegram. The agent interprets the
message, runs `agy` through the `terminal` tool, and sends results back
through the Telegram gateway.

### Start a coding task

User sends from Telegram:
```
agy: Add a /health endpoint to the FastAPI app
```

Agent executes:
```
terminal(command="agy -p 'Add a /health endpoint to the FastAPI app' --print-timeout 10m", workdir="/path/to/project", background=true, notify_on_complete=true)
```

### Check status

User sends: `agy status`

Agent checks the background process state and reports:
- Running / completed / failed
- Elapsed time
- Last output lines (truncated to 4000 chars for Telegram)

### Get the diff

User sends: `agy diff`

Agent executes:
```
terminal(command="git diff --stat && git diff", workdir="/path/to/project")
```

Then chunks the output into ≤4096-char Telegram messages (see
`references/telegram-patterns.md`).

### Stop a session

User sends: `agy stop`

Agent kills the background `agy` process:
```
process(action="kill", session_id=<id>)
```

### Switch project context

User sends: `agy switch ~/projects/other-app`

Agent updates the working directory for subsequent `agy` commands.

## Procedure

### 1. Receive coding prompt from Telegram

Parse the user's Telegram message. If it starts with `agy:` or references
coding/development intent, activate this skill.

Completion criterion: intent classified as agy-coding-task.

### 2. Resolve project directory

Check for an active project context. If none, ask the user which project
directory to target. Store the choice for the session.

Completion criterion: `workdir` is a valid directory containing source code.

### 3. Launch agy in background

```
terminal(command="agy -p '<user prompt>' --print-timeout <timeout>", workdir=workdir, background=true, notify_on_complete=true)
```

Default timeout: `10m`. User can override: `agy: Fix the auth bug --timeout 20m`

Completion criterion: background process started, session ID captured.

### 4. Send heartbeat updates

While `agy` runs, poll the process log every 60 seconds. Send a compact
status message to Telegram:

```
🔧 agy running (2m12s)
└─ Working on: Add /health endpoint
└─ Last action: Created app/routes/health.py
```

Keep heartbeats under 200 chars. Don't flood — skip if no new output.

Completion criterion: heartbeat sent or skipped (no new output).

### 5. Deliver results

When `agy` completes:

1. Capture full stdout
2. Run `git diff --stat` for a summary
3. Chunk output into Telegram-safe messages (≤4096 chars each)
4. Send summary first, then full diff on request (`agy diff`)

```
✅ agy completed (4m38s)
├─ Files changed: 3
├─ Insertions: +47, Deletions: -2
└─ Send "agy diff" for the full diff
```

Completion criterion: result summary delivered to Telegram.

### 6. Handle failures

If `agy` exits non-zero or times out:

```
❌ agy failed (exit code 1, 5m00s timeout)
└─ Last output: <truncated error>
└─ Send "agy logs" for full output
```

Completion criterion: failure reported with actionable next step.

## Quick Reference

| Telegram message | Agent action |
|---|---|
| `agy: <prompt>` | Start `agy -p` in background |
| `agy status` | Report running/completed/failed state |
| `agy diff` | Send `git diff` chunked to Telegram |
| `agy logs` | Send last 50 lines of `agy` output |
| `agy stop` | Kill background `agy` process |
| `agy switch <dir>` | Change project working directory |
| `agy models` | List available `agy` models |
| `agy: <prompt> --model <m>` | Start with specific model |
| `agy: <prompt> --timeout 20m` | Start with custom timeout |

## Pitfalls

1. **Telegram 4096-char limit.** Always chunk long outputs. Use
   `references/telegram-patterns.md` for the chunking procedure.
2. **`agy -p` returns plain text only.** No `--output-format json`, no result
   envelope. Parse stdout directly.
3. **No `--max-turns` on `agy`.** Bound with `--print-timeout` only.
4. **Security: `TELEGRAM_ALLOWED_USERS` is mandatory.** Never run coding
   commands from unverified Telegram users — this gives shell access.
5. **File paths must be server-side.** Telegram users reference paths on the
   host machine, not their phone. Confirm paths exist before launching.
6. **Heartbeat polling is advisory.** If the `terminal` background process
   doesn't expose incremental logs, heartbeats may be empty.
7. **Large diffs should use file upload.** If `git diff` exceeds ~20KB, send
   as a `.patch` file attachment instead of inline messages.
8. **`agy` auth.** If `agy` hasn't been authenticated on the host, it will
   try to open a browser — which fails headlessly. Pre-auth `agy` before
   using this skill remotely.

## Verification

Confirm end-to-end flow, all through Telegram:

1. Send `agy: echo hello world` from Telegram — verify agent starts `agy -p`
2. Send `agy status` — verify running state reported
3. Wait for completion — verify result summary arrives
4. Send `agy diff` — verify diff is chunked and delivered
5. Send `agy stop` on a running session — verify process killed
6. Send `agy switch /tmp/test-project` — verify directory change acknowledged
7. Verify all messages respect 4096-char limit
8. Verify unauthorized Telegram users cannot trigger `agy` commands

## Support files

- `references/telegram-patterns.md` — message chunking, inline keyboards,
  screenshot sharing, and session state management patterns.
