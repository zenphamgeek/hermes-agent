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
5. ❌ **Never route Claude tasks to Ultra accounts**: Ultra accounts (`ultra-2` / `lthn.Ariana`, etc.) STRICTLY serve Gemini models (`gemini-3.1-pro-high`, `gemini-3.8-flash-high`). Consuming Claude quota on Ultra accounts for Fleet tasks is ABSOLUTELY FORBIDDEN.
6. ❌ **Never send Gemini tasks to Nebula or query Nebula for Gemini**: Nebula API Gateway (`b.ai`) ONLY supports Claude Opus 4.8 (`claude-opus-4.8`) and does NOT have Gemini models. Cấm ngặt việc hỏi hoặc điều phối Gemini sang Nebula.

## Rule: Claude Routing Hierarchy (Pro-First Then Nebula), Ultra Gemini-Only & Nebula Opus 4.8 Invariant

1. **Claude Pro-First Mandate**: When Claude models (`claude-sonnet-5-5-high`, `claude-opus-5-5-high`, `claude-opus-4-6-thinking`) are required, the scheduler MUST prioritize **Pro-first** (Pro CLI nodes with available Claude quota in `pro-claude-pool` defined in untracked `fleet_roster.yml` / `fleet_roster.defaults.yml`).
2. **Nebula API Fallback (Claude Opus 4.8 Only & Zero-Gemini Mandate)**: ONLY when ALL Pro CLI Claude nodes have exhausted their quota, are rate-limited, or are busy, the system automatically falls back to **Nebula API Gateway (`nebula` / `b.ai`)**.
   - **Nebula ONLY has Claude Opus 4.8 (`claude-opus-4.8`)**: Nebula does NOT have Gemini!
   - **Never Ask Nebula about Gemini**: Never route Gemini models or query Nebula for Gemini tasks. All Gemini tasks MUST strictly run on AGY CLI nodes (Ultra/Pro).
3. **Ultra Accounts Strictly Gemini-Only**: Ultra accounts (`ultra-2` / `lthn.Ariana`) exist exclusively for high-complexity Gemini inference (`gemini-3.1-pro-high`, `gemini-3.8-flash-high`). Consuming Claude quota on Ultra accounts for Fleet tasks is ABSOLUTELY FORBIDDEN. Ultra accounts are permanently excluded from Claude routing pools.

## Rule: Mandatory Clef Swarm Participation Across All Fleet Tasks (Sự Tham Gia Của Clef Là Bắt Buộc)

Every fleet job (dispatched via `fleet_run`, `fleet_parallel`, `/api/fleet/run-sync`, `/api/fleet/run`, or autonomous DAG enqueue) MUST engage the **Clef Swarm**:
1. **Tri-Tier Cognitive Pre-Routing (`decide_async`)**: Pre-classifies domain, complexity $[0.0, 4.0]$, and node persona across Cloudflare Free Edge PoPs $\to$ Modal T4 27B $\to$ Local In-Process Surrogate. Cost strictly `$0.00` (`output_tokens == 0`).
2. **Deep Dialect Metaprompting (`synthesize_specification`)**: Compiles raw prompts into target dialects (Claude XML `<context>/<task>/<constraints>`, Gemini JSON Schema, Codex scaffold) and injects sovereign invariants.
3. **Negative-Selection Anomaly Self-Gate (`clef_self_gate`)**: Rejects corrupted dialects, token bloat, or invalid assertions prior to dispatch.
4. **Automated UAT Specification & Sentinel Anti-Fabrication (`PDCAEvolutionEngine` & `clef_sentinel`)**: Automatically generates and executes verification commands to enforce **Zero-Fake-Pass**.
- **Fail-Closed Sovereign Mandate**: Any job lacking Clef telemetry or verification fails closed immediately (`JobStatus.FAILED`).

### Self-Check Before Responding

Before producing any code block >20 lines, ask yourself:
- "Am I generating this inline instead of delegating?"
- "Could this be a fleet_run task if I paste enough context?"
- "Did I actually call fleet_run/fleet_parallel, or am I about to fabricate?"
- "If routing Claude, did I verify it NEVER touches an Ultra account?"
- "If routing Gemini, did I verify it NEVER touches Nebula (Nebula only has Opus 4.8)?"
