# AGY Fleet Mandatory Delegation Enforcement Rule

> **Purpose**: Prevent the orchestrator from bypassing `fleet_run` for code generation tasks >20 lines.

## Rule: Fleet-First Code Generation

When a task requires **non-trivial code generation, refactoring, or analysis** (>20 lines of code output), the orchestrator MUST follow this decision tree:

### Decision Tree

1. **Does the task need to READ existing project files to produce output?**
   - **YES** → Use `invoke_subagent` (AGY subagents have full filesystem access)
   - **NO** → Use `fleet_run` MCP tool (standalone generation, no disk context needed)

2. **For `fleet_run` tasks**: Always include ALL necessary context IN the prompt itself (paste relevant code snippets, file structures, API schemas). The fleet node runs in `--print` mode without file access.

3. **For `invoke_subagent` tasks**: Still counts as delegation per §1.11. Log which subagent was used and why fleet_run wasn't suitable.

### When to Use Each

| Scenario | Tool | Reason |
|----------|------|--------|
| Generate a new standalone Python file from a spec | `fleet_run` | No disk read needed |
| Refactor an existing file | `invoke_subagent` | Needs to read current code |
| Write tests for existing code | `invoke_subagent` | Needs to read source under test |
| Generate YAML/config from a description | `fleet_run` | Self-contained spec |
| Multi-file architecture design | `fleet_parallel` | Multiple perspectives, no disk |
| Debug a failing test | `invoke_subagent` | Needs to read test + source |

### Anti-Patterns to Avoid

1. ❌ **Never generate >20 lines of code inline** in the main orchestrator response
2. ❌ **Never use `invoke_subagent` when `fleet_run` would suffice** (wastes orchestrator quota)
3. ❌ **Never send `fleet_run` a task that requires reading files** without pasting the file content into the prompt (fleet nodes have no disk access in --print mode)
4. ❌ **Never claim "delegated to fleet" without actually calling fleet_run** — this is fabrication

### Self-Check Before Responding

Before producing any code block >20 lines, ask yourself:
- "Am I generating this inline instead of delegating?"
- "Could this be a fleet_run task if I paste enough context?"
- "Did I actually call fleet_run/fleet_parallel, or am I about to fabricate?"
