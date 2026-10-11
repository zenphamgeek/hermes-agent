---
name: trae-telegram
description: Control Trae IDE Autopilot and projects via Telegram.
version: 1.0.0
author: hermes-community
license: MIT
platforms:
- linux
- telegram
- windows
channels:
- telegram
- discord
- slack
tags:
- trae
- autopilot
- telegram
- ide-bridge
- vibe-coding
related_skills:
- trae-screen-analyst
- antigravity-telegram
- electron-ide-cdp-automation
metadata:
  hermes:
    tags:
    - trae telegram
    related_skills: []
---
# Trae IDE Autopilot — Telegram Mission Control

Operate Trae IDE remotely from Telegram: send coding prompts, capture
screenshots, toggle Autopilot auto-approval, and receive completion reports
with git diffs — all from your phone.

## When to Use

Activate this skill when the user sends a Telegram message that:
- Starts with `trae:` followed by a coding prompt
- Contains `trae screenshot`, `trae snap`, or `trae capture`
- Contains `trae continue`, `trae click`, or `trae approve`
- Contains `trae autopilot` with `on`, `off`, `status`, or `daemon`
- Contains `trae report`, `trae diff`, or `trae completion`
- Contains `trae status` (Autopilot state check)
- References controlling Trae IDE from a messaging platform

Do NOT activate for general coding requests that don't mention Trae IDE.

## Prerequisites

1. **Trae IDE running** on the workstation with CDP debug port enabled
   (default ports: 9339, 9222).
2. **`trae_bridge.py`** installed at
   `~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py`.
3. **`runner.py`** installed at
   `~/.hermes/skills/software-development/trae-screen-analyst/runner.py`.
4. **Wayland session** with `grim` or portal screencapture available.
5. **Telegram bot** configured with `TELEGRAM_BOT_TOKEN` and
   `TELEGRAM_ALLOWED_USERS` in `~/.hermes/.env`.
6. **Python dependencies**: `Pillow`, `websockets`, `numpy`.

## How to Run

The agent uses the `terminal` tool to invoke `trae_bridge.py` and `runner.py`
with appropriate flags. All commands run on the host workstation where Trae IDE
is displayed.

## Procedure

### Step 1 — Parse the Telegram command

Match the inbound message against these patterns (case-insensitive):

| Pattern | Action |
|---|---|
| `trae: <prompt>` | **Send prompt** to Trae IDE chat (with active project context) |
| `trae @<project>: <prompt>` | **Send prompt** CDP-routed to that project (no broadcast) |
| `trae screenshot [target]` | **Capture** and send screenshot |
| `trae continue` or `trae click` | **Click** Continue/Run button |
| `trae force click` | **Force-click** default button position |
| `trae autopilot on` | **BLOCKED** — Hermes autopilot luôn tắt; Trae Autopilot Extension là controller duy nhất |
| `trae autopilot off` | **Disable** auto-approval |
| `trae autopilot status` | **Check** current Autopilot state + active project |
| `trae autopilot daemon [interval]` | **BLOCKED** — daemon không được start; extension đảm nhận loop |
| `trae report` or `trae completion` | **Send** completion report + git diff |
| `trae diff` | **Show** git diff summary (active project) |
| `trae status` | Same as `trae autopilot status` |
| `trae project list` | **List** all registered projects |
| `trae project discover` | **Auto-scan** ~/home for git repos |
| `trae project select <name>` | **Switch** active project |
| `trae project add <name> <path>` | **Register** a new project |
| `trae project remove <name>` | **Unregister** a project |
| `trae project active` | **Show** current active project |

The optional `[target]` parameter selects the monitor:
- `dell` or `dp` — Dell DP-1 monitor (default)
- `samsung` or `hdmi` — Samsung HDMI-1 monitor
- `laptop` or `edp` — Laptop eDP-1 built-in display

### Step 2 — Execute via terminal tool

#### Send a prompt to Trae IDE

```bash
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --send '<prompt>' --target dell")
```

The bridge tries CDP injection first (zero-focus, zero-mouse-movement).
Routing depends on whether a project is specified:

- **No project** (`trae: <prompt>`): CDP targets the only open Trae window;
  if several windows are open the send fails closed (ambiguous). If CDP
  fails, the bridge falls back to AT-SPI clipboard paste on the target
  monitor.
- **Project specified** (`trae @<project>: <prompt>`): CDP-only, matched
  against the page's project title/path/URL. Never broadcasts — a
  non-unique or unmatched project refuses to send, and there is NO AT-SPI
  fallback when a project is named.

#### Capture and send screenshot

```bash
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/runner.py --target dell")
```

This captures the Wayland screen, crops to the target monitor, and sends the
JPEG to Telegram with a caption.

#### Click Continue / approval button

```bash
# Vision-guided click (detects button text and position)
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --continue-click --target dell")

# Force click at default position (no vision check)
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --force-click --target dell")
```

This is the unblock path: the vision model reads the actual screen state and,
when it detects a "Model request failed" banner, auto-recovers by injecting a
context-aware recovery prompt (the vision model's suggested continuation for
the exact error state) with bounded retries — recovery stops after a fixed
number of attempts instead of spinning indefinitely.

#### Autopilot management

```bash
# BLOCKED: Hermes autopilot KHÔNG được bật/start. Trae Autopilot Extension (trae-controller systemd
# services) là bộ điều khiển duy nhất — loop, unblock, smart prompt đều do extension lo.
# Chạy các lệnh sau sẽ bị chặn (in thông báo vô hiệu hóa, không có hiệu lực):
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --autopilot on")

# Trạng thái (chỉ đọc, hợp lệ):
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --autopilot status")
```

#### Completion report

```bash
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --report-completion --target dell")
```

Captures a screenshot, collects `git diff --stat` and `git status --short`,
and sends a formatted report to Telegram.

#### Git diff only

```bash
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --git-diff")
```

#### Project Management

```bash
# Auto-discover git repos in ~/
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --project discover")

# List all registered projects
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --project list")

# Select active project
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --project 'select hermes-agent'")

# Add a custom project
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --project 'add myapp /path/to/myapp'")

# Remove a project
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --project 'remove myapp'")

# Show active project
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --project active")
```

#### Send prompt to specific project (overriding active)

```bash
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --send 'Fix the login bug' --project hermes-agent")
```

This prepends `[Project: hermes-agent @ /path/to/project]` to the prompt
so Trae's agent knows which codebase to work on, and routes CDP strictly
to the matching project window — no broadcast to other windows, no AT-SPI
fallback if the match is missing or ambiguous.

### Step 3 — Report result to user

After execution, relay the terminal output back to the Telegram user.
For screenshot commands, the runner already sends the image to Telegram
directly — confirm success in the chat reply.

## Quick Reference

```
trae: Fix the login bug          → Inject prompt into Trae (active project)
trae @hermes-agent: Fix bugs     → CDP-route prompt to matching project window
trae screenshot                  → Capture Dell screen → Telegram
trae screenshot samsung          → Capture Samsung screen → Telegram
trae continue                    → Vision-detect + click Continue
trae force click                 → Force-click default position
trae autopilot on                → BLOCKED — extension owns automation
trae autopilot off               → Disable auto-approval
trae autopilot status            → Show ON/OFF state + active project
trae autopilot daemon            → BLOCKED — extension owns loop
trae report                      → Screenshot + git diff → Telegram
trae diff                        → Print git changes (active project)
trae project list                → Show all registered projects
trae project discover            → Auto-find git repos
trae project select <name>       → Switch active project
trae project add <name> <path>   → Register new project
trae project remove <name>       → Unregister a project
```

## Common Pitfalls

1. **CDP port not open**: Trae must be launched with `--remote-debugging-port=9339`.
   If CDP fails, the bridge falls back to AT-SPI — but only for unprojected
   sends (`trae: <prompt>`). Project-routed sends (`trae @<project>:`) fail
   closed instead. AT-SPI requires the Wayland session to be active (not
   screen-locked).
2. **Screen locked**: Both screenshot and button-click require an unlocked
   Wayland session. If the screen is locked, commands fail silently.
3. **Wrong target monitor**: Clicking on the wrong monitor sends the click
   to the wrong Trae instance. Always verify with `trae screenshot` first.
4. **Vision model timeout**: The local LM Studio vision model (at
   `10.123.214.1:1234`) has a 30s timeout. Large screenshots may take longer.
5. **Hermes autopilot is BLOCKED**: `trae autopilot on` / `trae autopilot daemon` never
   start — the Trae Autopilot Extension (trae-controller) owns loop/unblock/smart-prompt.
   Do not attempt to enable them; do not run a second watcher.
6. **Message too long**: Telegram caps messages at 4096 chars. Git diff output
   is truncated to 800 chars; full diffs are sent as file attachments.

## Verification

After executing a command, verify by:
1. `trae screenshot` — visual confirmation the action took effect
2. `trae autopilot status` — confirms autopilot state (always OFF for Hermes)
3. `trae diff` — confirms code changes landed
