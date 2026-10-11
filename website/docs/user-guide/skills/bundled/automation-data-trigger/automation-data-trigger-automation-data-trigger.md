---
title: "Automation Data Trigger — Fire a cron agent when a measured value crosses a threshold"
sidebar_label: "Automation Data Trigger"
description: "Fire a cron agent when a measured value crosses a threshold"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Automation Data Trigger

Fire a cron agent when a measured value crosses a threshold.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/automation-data-trigger` |
| Version | `0.1.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Automation`, `Trigger`, `Cron`, `Monitoring` |
| Related skills | [`automation-watch`](/docs/user-guide/skills/bundled/automation-watch/automation-watch-automation-watch), [`automation-workflow`](/docs/user-guide/skills/bundled/automation-workflow/automation-workflow-automation-workflow), `cron` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Automation Data Trigger Skill

Turn "wake me when the number crosses the line" into a scheduled agent job.
A polling script measures a value (HTTP JSON, a shell command, or a file),
compares it against a threshold, and prints a wake gate: when the condition
holds the scheduler runs the agent; when it does not, the run is skipped
silently — no LLM call, no delivery.

The wake gate is built into the cron scheduler (`cron/scheduler.py` parses
`{"wakeAgent": false}` from the job's pre-check script output), so this
skill adds no new infrastructure.

## When to Use

- "Alert me when the price drops more than 5%."
- "Wake me when the API error rate exceeds 1%."
- "Notify me when a download completes and the file is large enough."
- "Tell me when the temperature in the lab goes above 30°C."

Don't use for: files appearing or changing in a folder (use
`automation-watch`), fixed-schedule reports that always run (plain `hermes
cron add`), or events that arrive over HTTP (use `hermes webhook subscribe
--trigger-job`).

## Prerequisites

- A running gateway / cron scheduler: `hermes gateway run`.
- The helper script: copy `skills/automation-data-trigger/scripts/poll_threshold.py`
  to `~/.hermes/scripts/poll_threshold.py` (cron scripts must live there).

## How to Run

1. Copy the helper into your profile's scripts dir:
   `cp skills/automation-data-trigger/scripts/poll_threshold.py
   ~/.hermes/scripts/poll_threshold.py`
2. Create the gated job:
   `hermes cron add "every 5m" "Summarize the price move" --name price-watch
   --script poll_threshold.py --deliver telegram`
3. Verify: `hermes cron runs price-watch` after a fire.

## Quick Reference

```bash
# Drop >5% vs previous poll, JSON field a.b.c from an API
hermes cron add "every 5m" "Alert on the drop" --name price-drop \
  --script "poll_threshold.py btc --url https://api.example.com/ticker \
    --field data.price --drop-pct 5"

# Absolute threshold from a shell command's last stdout line
hermes cron add "every 10m" "Report the error rate" --name err-rate \
  --script "poll_threshold.py errs --command 'curl -s http://srv/stats | jq .rate' --gt 1.0"

# Value from a file
hermes cron add "every 15m" "Warn if too hot" --name lab-temp \
  --script "poll_threshold.py temp --file /srv/lab/temp.txt --gt 30"
```

## Procedure

1. **Choose a source.** `--url` (JSON + `--field` dotted path), `--command`
   (shell command, last stdout line parsed as a number), or `--file`.
2. **Choose a condition.** `--lt N` / `--gt N` compare against a fixed
   threshold every tick. `--drop-pct N` / `--rise-pct N` fire on a relative
   move vs the previous poll (the first poll only seeds the baseline).
3. **Create the job with the script.** The scheduler runs the script before
   the agent; `{"wakeAgent": false}` skips the run for that tick, silently.
   When the gate opens, the JSON envelope (value, previous, message) is
   injected into the agent's prompt as context.
4. **Verify.** `hermes cron runs <job>` shows `completed` for fires; skipped
   ticks are logged, not delivered.

## Pitfalls

- The helper exits non-zero when the source fails (network error, bad JSON,
  non-numeric value), so a broken monitor is visible as a failed run instead
  of silently going dark. Keep the source robust; a flaky endpoint will show
  up in `hermes cron runs`.
- Relative modes (`--drop-pct`, `--rise-pct`) compare against the previous
  successful poll, which updates every tick. A slow 1%-per-tick decline never
  trips a 5% drop gate; use a fixed `--lt`/`--gt` or lengthen the schedule if
  you need trend detection over a window.
- State (previous value) persists per trigger name under
  `~/.hermes/cron/data-triggers/`. Deleting the file re-seeds the baseline.
- The gate only suppresses the agent run — the job still fires on schedule.
  `--monitor-script`/`--monitor-url` on `hermes cron add` is a different,
  hash-based suppression (skip when output is byte-identical) and pairs well
  when the source itself is the diff.

## Verification

- Run the script by hand: `python poll_threshold.py btc --url ... --gt 30` —
  a false condition prints `{"wakeAgent": false, ...}` and exit 0.
- `hermes cron runs <job>` shows a completed run with output after a real
  threshold crossing.
