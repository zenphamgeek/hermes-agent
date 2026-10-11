---
title: "Hermes Dev Workflow — Contribute to hermes-agent with testing standards"
sidebar_label: "Hermes Dev Workflow"
description: "Contribute to hermes-agent with testing standards"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Hermes Dev Workflow

Contribute to hermes-agent with testing standards.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/development/hermes-dev-workflow` |
| Path | `optional-skills/development/hermes-dev-workflow` |
| Version | `1.0.0` |
| Author | hermes-community |
| License | MIT |
| Platforms | cli, telegram, windows |
| Tags | `hermes dev workflow` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Hermes Agent — Development Contribution Workflow

Guide for making changes to the hermes-agent codebase. Covers the full
lifecycle from feature design to testing to merge.

## When to Use

Activate this skill when:
- The user asks to add a new feature, tool, or command to Hermes
- A bug fix is needed in core files (`run_agent.py`, `cli.py`, `model_tools.py`)
- Adding a new slash command to `hermes_cli/commands.py`
- Creating a new plugin or extending an existing one
- Writing or updating tests for hermes-agent components
- The user mentions "hermes dev", "contribute", or "add command"

Do NOT use for general coding tasks unrelated to hermes-agent internals.

## Prerequisites

1. **Python 3.11+** with `.venv` activated
2. **Git** with access to the hermes-agent repository
3. **Understanding of AGENTS.md** — the canonical source of truth

## How to Run

The agent uses terminal commands for all development tasks: running tests,
editing files, checking git status, and verifying changes.

## Procedure

### Step 1 — Understand the Design Intent

Before any change, verify you understand the design:

```bash
# Check if a symbol exists and its history
terminal(command="git -C ~/hermes-agent log --oneline -5 -S '<symbol>'")

# Read the AGENTS.md section for the component
terminal(command="grep -n '## <section>' ~/hermes-agent/AGENTS.md | head -5")
```

Key rules:
- **Prompt caching is sacred** — never mutate past context mid-conversation
- **Core is narrow waist** — capability lives at edges (skills, plugins)
- **Every tool costs on every API call** — use the Footprint Ladder

### Step 2 — Apply the Footprint Ladder

For NEW capability, evaluate in this order:

1. **Extend existing code** → Can an existing function handle this?
2. **CLI command + skill** → `hermes <subcommand>` + SKILL.md
3. **Service-gated tool** → `check_fn` + conditional availability
4. **Plugin** → `~/.hermes/plugins/<name>/`
5. **MCP server** → catalog entry, zero core footprint
6. **New core tool** → LAST resort (terminal + file can't do it)

### Step 3 — Make the Change

#### Adding a Slash Command

```bash
# 1. Add CommandDef to COMMAND_REGISTRY
terminal(command="grep -n 'COMMAND_REGISTRY' ~/hermes-agent/hermes_cli/commands.py | head -3")

# 2. Add handler in process_command()
terminal(command="grep -n 'process_command' ~/hermes-agent/cli.py | head -3")

# 3. If gateway-available, add to gateway/run.py
terminal(command="grep -n 'canonical ==' ~/hermes-agent/gateway/run.py | head -10")
```

#### Adding a Tool

```bash
# Check existing tools for patterns
terminal(command="ls ~/hermes-agent/tools/*.py")

# Create tool file with registry.register()
# Add to toolsets.py in appropriate toolset
terminal(command="grep -n '_HERMES_CORE_TOOLS' ~/hermes-agent/toolsets.py")
```

#### Adding a Skill

Follow the structure in `.agents/rules/skill_standards.md`:
- Create `SKILL.md` with proper frontmatter
- Create `references/` directory if needed
- Create test at `tests/skills/test_<name>_skill.py`

### Step 4 — Test

```bash
# Run full test suite
terminal(command="cd ~/hermes-agent && source .venv/bin/activate && python -m pytest tests/ -v --tb=short 2>&1 | tail -30")

# Run specific skill tests
terminal(command="cd ~/hermes-agent && source .venv/bin/activate && python -m pytest tests/skills/ -v")

# Run specific component tests
terminal(command="cd ~/hermes-agent && source .venv/bin/activate && python -m pytest tests/<component>/ -v")
```

### Step 5 — Verify

```bash
# Check git status
terminal(command="cd ~/hermes-agent && git diff --stat")

# Verify no broken imports
terminal(command="cd ~/hermes-agent && source .venv/bin/activate && python -c 'import run_agent; import model_tools; import cli; print(\"OK\")'")

# Check for machine-local paths in skills
terminal(command="grep -rn '/home/' ~/hermes-agent/optional-skills/ ~/hermes-agent/skills/ --include='*.md' | grep -v '~/' | head -10")
```

## Quick Reference

```
# Development
source .venv/bin/activate              # Activate venv
python -m pytest tests/ -v             # Run all tests
python -m pytest tests/skills/ -v      # Run skill tests
scripts/run_tests.sh                   # Official test runner

# Git
git diff --stat                        # Check changes
git log --oneline -10                  # Recent history
git log -p -S "<symbol>"              # Find symbol history

# File locations
hermes_cli/commands.py                 # COMMAND_REGISTRY
run_agent.py                           # AIAgent core loop
model_tools.py                         # Tool orchestration
toolsets.py                            # Tool schema bundles
tools/registry.py                      # Tool registration
cli.py                                 # CLI orchestrator
gateway/run.py                         # Gateway handler
```

## Common Pitfalls

1. **Adding tool without toolset entry**: Tool registers but is never exposed
   to the agent. Must add to `toolsets.py`.
2. **Breaking prompt caching**: Any system prompt mutation mid-conversation
   invalidates the cache. Never do this.
3. **Machine-local paths in skills**: Use `~/.hermes/` not `/home/<user>/.hermes/`.
4. **Missing test coverage**: Every skill needs `tests/skills/test_<name>_skill.py`.
5. **Env var for non-secret config**: Use `config.yaml` for behavioral settings.
6. **Change-detector tests**: Assert invariants, not frozen values.

## Verification

After making changes:
1. `python -m pytest tests/ -v` — zero failures
2. `git diff --stat` — only expected files changed
3. No machine-local paths in new skill files
4. COMMAND_REGISTRY entries have proper categories and descriptions
