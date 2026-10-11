---
name: automation-workflow
description: 'Deploy and run multi-step automation workflows.'
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
    - Workflow
    - Cron
    - Orchestration
    related_skills:
    - cron
---
# Automation Workflow Skill

Turn a series of agent tasks into a deployable, dependency-ordered DAG of cron
jobs. Each step is a real cron job (its own session — prompt-cache safe), so
scheduling, delivery, retries and the execution ledger all behave exactly like
plain `hermes cron`. This skill does not replace cron; it layers ordering and
chaining on top of it.

## When to Use

- "Run task A, then task B with A's output."
- "Set up a recurring pipeline (fetch → process → deliver)."
- "Make several steps run in order, each with its own tools."
- "Turn a scripted multi-agent flow into something schedulable."

Don't use for: a single scheduled task (use `cronjob`/`hermes cron`), or
interactive multi-turn sessions (use `delegate_task`).

## Prerequisites

- `hermes workflow` CLI (built in).
- Workflow engine docs: `cron/workflows.py` (source of truth for the YAML
  schema).

## How to Run

1. Author a YAML file (see Quick Reference).
2. Deploy: `hermes workflow deploy <file.yaml>`
3. Inspect: `hermes workflow status <name>`
4. Trigger now: `hermes workflow run <name>`

## Quick Reference

```yaml
name: daily-report          # letters, digits, '_', '-'
description: Optional one-liner
schedule: "every 1h"        # optional; applies to steps without their own
steps:
  - id: fetch               # unique step id
    prompt: "Fetch the latest numbers and save them."
    schedule: "every 1h"    # per-step override; absent = manual-only
    tools:                  # optional guardrail (toolset allow/deny)
      allow: [file, web]
      deny: [terminal]
    retry: 2                # attempts per run (default 1)
  - id: process
    prompt: "Read the saved numbers and write the report."
    depends_on: [fetch]     # fetch's last output is injected into this prompt
    continue_on_error: true # run even if fetch failed (default false)
```

## Procedure

1. **Design the DAG.** List steps, their `depends_on` edges, and the output each
   downstream step needs. Steps that don't depend on anything run first.
2. **Author the YAML.** One step per agent session. Each step needs at least a
   `prompt`, a `script`, or `skills`. Keep each prompt self-contained —
   upstream output arrives via `depends_on` (`context_from`), not by reading
   the conversation.
3. **Deploy.** `hermes workflow deploy <file.yaml>`. Re-deploy is idempotent:
   job ids are stable, so edits preserve `depends_on` chaining. Deploy fails
   loudly on unknown step refs and dependency cycles.
4. **Verify.** `hermes workflow status <name>` shows each step's job, state,
   and last run. Scheduled steps run on their own; schedule-less steps only run
   via `hermes workflow run <name>`.
5. **Operate.** `hermes workflow list`, `pause`, `resume`, `remove`. Per-step
   run history lives in `hermes cron runs <job_id>`.

## Pitfalls

- A step without a schedule is **paused** at deploy — it never fires on its
  own. Give it a schedule (step or workflow level) if it should.
- `depends_on` is enforced at deploy AND run time: a failed dependency skips
  downstream steps unless `continue_on_error: true`.
- Each step is a separate agent session; there is no shared conversation
  memory between steps. Chain data explicitly through `depends_on`.
- `tools.allow`/`deny` name **toolsets**, not individual tools (see
  `toolsets.py`). Global defaults can be set under
  `security.automation_policies` in `config.yaml`.

## Verification

- `hermes workflow status <name>` lists all steps with non-error state.
- `hermes workflow run <name>` returns PASS and each step shows `ok`.
- Cancel-able? No — a running workflow cannot be interrupted mid-step; steps
  are bounded by the same 3-minute cron hard interrupt.
