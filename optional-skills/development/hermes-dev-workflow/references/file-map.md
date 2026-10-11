# Hermes Agent — File Map Quick Reference

## Core Files (Touch with Care)

| File | Purpose | LOC |
|---|---|---|
| `run_agent.py` | AIAgent class, conversation loop | ~12k |
| `model_tools.py` | Tool orchestration, discovery | ~3k |
| `cli.py` | CLI orchestrator, command dispatch | ~11k |
| `toolsets.py` | `_HERMES_CORE_TOOLS` list | ~500 |
| `hermes_state.py` | SessionDB (SQLite + FTS5) | ~2k |
| `hermes_constants.py` | `get_hermes_home()`, paths | ~300 |
| `hermes_logging.py` | Logging setup | ~200 |

## Command System

| File | Purpose |
|---|---|
| `hermes_cli/commands.py` | `COMMAND_REGISTRY` — all slash commands |
| `cli.py:process_command()` | CLI dispatch |
| `gateway/run.py` | Gateway dispatch |
| `agent/skill_commands.py` | Skill slash commands |

## Tool System

| File | Purpose |
|---|---|
| `tools/registry.py` | Tool registration (no deps) |
| `tools/*.py` | Individual tool implementations |
| `tools/environments/` | Terminal backends (local, docker, ssh) |
| `model_tools.py` | Discovery + `handle_function_call()` |

## Plugin System

| Directory | Purpose |
|---|---|
| `plugins/memory/` | Memory providers (honcho, mem0) |
| `plugins/model-providers/` | Inference backends |
| `plugins/kanban/` | Multi-agent board |
| `plugins/image_gen/` | Image generation |
| `~/.hermes/plugins/` | User-installed plugins |

## Gateway & Platforms

| File | Purpose |
|---|---|
| `gateway/run.py` | Main gateway handler |
| `gateway/session.py` | Session management |
| `gateway/platforms/` | Per-platform adapters |
| `gateway/platforms/telegram/` | Telegram adapter |

## UI

| Directory | Purpose |
|---|---|
| `ui-tui/` | Ink (React) terminal UI |
| `tui_gateway/` | Python JSON-RPC backend |
| `apps/desktop/` | Electron desktop app |
| `web/` | Dashboard React frontend |
| `hermes_cli/web_server.py` | Dashboard server |

## Testing

| Pattern | Purpose |
|---|---|
| `tests/` | Main test directory |
| `tests/skills/` | Skill validation tests |
| `tests/test_*.py` | Component tests |
| `scripts/run_tests.sh` | Official test runner |
