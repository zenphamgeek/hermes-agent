---
name: automation-watch
description: 'Fire a cron job when files appear or change in a folder.'
version: 0.1.0
author: Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Automation
    - File
    - Trigger
    - Cron
    related_skills:
    - automation-workflow
    - cron
---
# Automation Watch Skill

Turn "new or changed files in a directory" into a scheduled agent job. A
watcher polls a folder and fires a bound cron job via `trigger_job` — the same
mechanism the webhook adapter uses, so scheduling, retries, the execution
ledger, and toolset gating all behave like a normal cron run.

## When to Use

- "When a file lands in `incoming/`, process it."
- "Whenever `report.csv` changes, regenerate the dashboard."
- "Watch a download folder for new PDFs and summarize them."

Don't use for: real-time streaming (polling has latency), or events that
arrive over HTTP (use `hermes webhook subscribe --trigger-job` instead).

## Prerequisites

- `hermes watch` CLI (built in).
- The target job must exist first: `hermes cron add` or a deployed workflow
  step. A schedule-less workflow step works: `hermes workflow run` is manual,
  but `trigger_job` fires it on the next scheduler tick too.
- A running gateway (or cron scheduler) to actually execute fired jobs:
  `hermes gateway run`.

## How to Run

1. `hermes watch add <name> <path> --job <job> [--on new|change|any] [--pattern '*.csv']`
2. `hermes watch list` to verify.
3. `hermes watch serve` to start polling (foreground). For 24/7 monitoring run
   it under systemd or as a background process.

## Quick Reference

```bash
hermes watch add ingest /srv/inbox --job my-job --on new --pattern '*.csv'
hermes watch add reports /srv/data --job regenerate --on change --debounce 300
hermes watch serve --interval 15
hermes watch list
hermes watch remove ingest
```

## Procedure

1. **Create the job.** `hermes cron add` (or deploy a workflow). Confirm with
   `hermes cron list`.
2. **Add a watcher.** `--on new` fires when a file that matches `--pattern`
   first appears; `--on change` fires when an existing file's mtime changes;
   `--on any` fires on either. `--debounce` caps how often a busy directory
   can trigger (default 30s).
3. **Serve.** `hermes watch serve` polls every `--interval` seconds. Each
   matched event fires the job exactly once — the snapshot advances even when
   the trigger is debounced, so the same file never re-fires.
4. **Verify.** `hermes cron runs <job_id>` shows each fired run; `hermes watch
   list` shows `last fired`.

## Pitfalls

- Polling only; there is no inotify event stream. Expect `interval`-level
  latency.
- Fired jobs execute on the next scheduler tick, not instantly. The gateway
  must be running.
- `--pattern` matches file **basenames** (globs), and only files directly in
  the watched directory (non-recursive).
- Pre-existing files are snapshotted at add time — only changes after that
  fire.

## Verification

- `hermes watch list` shows the watcher with a real `last fired` timestamp
  after an event.
- `hermes cron runs <job_id>` shows a `completed` run for the fired job.
