---
title: "Trae Telegram — Control Trae IDE Autopilot and projects via Telegram"
sidebar_label: "Trae Telegram"
description: "Control Trae IDE Autopilot and projects via Telegram"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Trae Telegram

Control Trae IDE Autopilot and projects via Telegram.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/autonomous-ai-agents/trae-telegram` |
| Path | `optional-skills/autonomous-ai-agents/trae-telegram` |
| Version | `1.0.0` |
| Author | hermes-community |
| License | MIT |
| Platforms | linux, telegram, windows |
| Tags | `trae telegram` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

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
| `trae @<project>: <prompt>` | **Send prompt** targeting a specific project |
| `trae screenshot [target]` | **Capture** and send screenshot |
| `trae continue` or `trae click` | **Click** Continue/Run button |
| `trae force click` | **Force-click** default button position |
| `trae autopilot on` | **Enable** auto-approval daemon |
| `trae autopilot off` | **Disable** auto-approval |
| `trae autopilot status` | **Check** current Autopilot state + active project |
| `trae autopilot daemon [interval]` | **Start** background watcher |
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
Falls back to AT-SPI clipboard paste if CDP fails.

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

The vision-guided path also detects "Model request failed" banners and
auto-recovers by injecting a retry prompt.

#### Autopilot management

```bash
# Enable Autopilot (persists in ~/.hermes/autopilot.json)
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --autopilot on")

# Disable Autopilot
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --autopilot off")

# Check status
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --autopilot status")

# Start background daemon (checks every 5 minutes)
terminal(command="python3 ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py --autopilot daemon --interval 300 --target dell")
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
so Trae's agent knows which codebase to work on.

### Step 3 — Report result to user

After execution, relay the terminal output back to the Telegram user.
For screenshot commands, the runner already sends the image to Telegram
directly — confirm success in the chat reply.

## Quick Reference

```
trae: Fix the login bug          → Inject prompt into Trae (active project)
trae @hermes-agent: Fix bugs     → Inject prompt for specific project
trae screenshot                  → Capture Dell screen → Telegram
trae screenshot samsung          → Capture Samsung screen → Telegram
trae continue                    → Vision-detect + click Continue
trae force click                 → Force-click default position
trae autopilot on                → Enable auto-approval daemon
trae autopilot off               → Disable auto-approval
trae autopilot status            → Show ON/OFF state + active project
trae autopilot daemon            → Background watcher (5min interval)
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
   If CDP fails, the bridge falls back to AT-SPI which requires the Wayland
   session to be active (not screen-locked).
2. **Screen locked**: Both screenshot and button-click require an unlocked
   Wayland session. If the screen is locked, commands fail silently.
3. **Wrong target monitor**: Clicking on the wrong monitor sends the click
   to the wrong Trae instance. Always verify with `trae screenshot` first.
4. **Vision model timeout**: The local LM Studio vision model (at
   `10.123.214.1:1234`) has a 30s timeout. Large screenshots may take longer.
5. **Autopilot daemon persistence**: The daemon runs in the foreground. Use
   `/background` to run it as a background task: `/background trae autopilot daemon`.
6. **Message too long**: Telegram caps messages at 4096 chars. Git diff output
   is truncated to 800 chars; full diffs are sent as file attachments.

## Verification

After executing a command, verify by:
1. `trae screenshot` — visual confirmation the action took effect
2. `trae autopilot status` — confirms daemon state
3. `trae diff` — confirms code changes landed
