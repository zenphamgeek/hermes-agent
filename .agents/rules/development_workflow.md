# Hermes Agent — Development Workflow Rules

## Core Design Principles

These two properties override ALL other decisions:

1. **Per-conversation prompt caching is sacred.**
   - Never mutate past context mid-conversation.
   - Never swap toolsets or rebuild system prompts after the first turn.
   - The only exception is context compression (`/compress`).

2. **The core is a narrow waist; capability lives at the edges.**
   - Every model tool ships on EVERY API call → high bar for new core tools.
   - New capability should arrive as: skill → plugin → service-gated tool → core tool (last resort).

## The Footprint Ladder

When adding new capability, choose the HIGHEST rung that works:

1. **Extend existing code** — zero new surface
2. **CLI command + skill** — `hermes <subcommand>` guided by a skill
3. **Service-gated tool (`check_fn`)** — only appears when prerequisite configured
4. **Plugin** — lives in `~/.hermes/plugins/`, discovered at runtime
5. **MCP server** — in the MCP catalog, zero core footprint
6. **New core tool** — LAST resort, fundamental + broadly useful

## Code Modification Rules

### Before Editing Core Files
- `run_agent.py` (~12k LOC) — the agent loop. Touch with extreme care.
- `model_tools.py` — tool orchestration. Understand the registry before adding.
- `cli.py` (~11k LOC) — CLI orchestrator. Process commands via `process_command()`.
- `toolsets.py` — `_HERMES_CORE_TOOLS` list. Every entry costs on every API call.
- `hermes_cli/commands.py` — COMMAND_REGISTRY. All downstream consumers derive from this.

### File Dependency Chain
```
tools/registry.py  (no deps)
       ↑
tools/*.py  (registry.register() at import time)
       ↑
model_tools.py  (imports tools/registry)
       ↑
run_agent.py, cli.py, batch_runner.py
```

### Adding a Slash Command
1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `HermesCLI.process_command()` in `cli.py`
3. If gateway-available, add handler in `gateway/run.py`
4. For persistent settings, use `save_config_value()`

### Adding a New Tool
1. Check the Footprint Ladder first — most things should be skills or plugins
2. If core tool: create `tools/your_tool.py` with `registry.register()`
3. Add to `toolsets.py` in appropriate toolset
4. Use `display_hermes_home()` for profile-aware paths in schemas
5. Use `get_hermes_home()` for state files

## Configuration Rules

- **`.env` is for SECRETS ONLY** — API keys, tokens, passwords
- **`config.yaml` is for ALL behavioral settings** — timeouts, thresholds, feature flags
- Never tell users to "set X in .env" unless X is a credential
- Config changes via `save_config_value()` in code, `hermes setup` for users

## Testing Rules

### Run Tests
```bash
source .venv/bin/activate
python -m pytest tests/ -v                    # full suite
python -m pytest tests/skills/ -v             # skill tests only
scripts/run_tests.sh                          # official test runner
```

### Test Standards
- **Behavior contracts over snapshots** — assert invariants, not frozen values
- **E2E validation** — exercise real paths with real imports against temp `HERMES_HOME`
- **No change-detector tests** — don't freeze model lists, config versions, enum counts
- **Skill tests must validate**: frontmatter format, body structure, no machine-local paths, size limits

### What Tests Must Cover
- Resolution chains
- Config propagation
- Security boundaries
- Role alternation (never two same-role messages in a row)
- System prompt byte-stability

## Git & PR Practices

- **Fix the whole bug class** — sibling call paths included, not just the reported site
- **Verify premise against current `main`** before writing fixes
- **Read original commit intent** with `git log -p -S "<symbol>"` before "fixing" gaps
- **Contributor credit preserved** — cherry-pick, don't reimplement from scratch
- Commit messages: `fix(component): description` or `feat(component): description`

## TypeScript Style (ui-tui, desktop, website)

- Prefer nanostores over component state for shared state
- Components use `useStore`; non-rendering reads use `$atom.get()`
- Keep route roots thin — compose routes and shell, not controllers
- No monolithic hooks — one narrow job per hook
- Table-driven beats condition ladders for mapping ids/routes/views
- `src/app` → routes/pages, `src/store` → shared atoms, `src/lib` → pure helpers
