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
5. ❌ **Never route ANY task (Gemini or Claude) to Ultra accounts (`innoria-team`, `ultra-2` / `lthn.Ariana`)**: Both Ultra accounts are currently **token-exhausted (`suspended` / `ineligible`)**. Route 100% of Fleet tasks strictly to Group B Standard Pro nodes (`tier="pro"`).
6. ❌ **Never send Gemini tasks to Nebula or query Nebula for Gemini**: Nebula API Gateway (`b.ai`) ONLY supports Claude Opus 4.8 (`claude-opus-4.8`) and does NOT have Gemini models. Cấm ngặt việc hỏi hoặc điều phối Gemini sang Nebula.

## Rule: Strict Pro-Only Fleet Swarm Routing (`tier="pro"` Exclusive — Ultra Nodes Token Exhausted), Claude Pro-First & Nebula Disabled Invariant

1. **Strict Pro-Only Fleet Swarm Mandate (`tier="pro"` Exclusive)**:
   - **Group B (17 Standard Pro Nodes — 100% Active Pool)**: Directly supports **3-Tier Gemini 4 Argon** (`gemini-4-argon-high`, `gemini-4-argon-medium`, `gemini-4-argon-low`), `claude-opus-5-5-high/medium/low`, `claude-opus-4-6-thinking`, `claude-opus-4.6`, `claude-sonnet-4-6`, `gpt-oss-120b-medium`. `resolve_model_for_node` dynamically adapts models on Group B nodes, load-balanced via **Quota-Balanced Round-Robin (QBRR)**.
   - **Group A (2 Ultra Nodes — `innoria-team` & `ariana`/`ultra-2` — TOKEN EXHAUSTED / SUSPENDED)**: Currently token-exhausted. **100% of tasks MUST be routed exclusively to Fleet Swarm Pro nodes (`tier="pro"`, e.g. `model="gemini-4-argon-high"`, `"gemini-4-argon-medium"`, `"gemini-4-argon-low"`, or `"claude-sonnet-4-6"`)**. Never dispatch `tier="ultra"` to Ultra accounts while Ultra tokens are exhausted.
2. **Claude Pro-First Mandate**: When Claude models (`claude-opus-5-5-high`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking`) are required, the scheduler MUST route exclusively to **Pro CLI nodes** (`tier="pro"`) with available Claude quota in `pro-claude-pool`.
3. **Nebula Disabled & Pro Gemini 4 Argon CLI Fallback**: **Nebula API Gateway (`nebula` / `b.ai`)** is **DISABLED (`disabled: True`, `ineligible: True`)** due to quota exhaustion. When ALL Pro CLI Claude nodes have exhausted their quota, the system automatically falls back to **healthy Pro CLI nodes running Gemini 4 Argon** (`gemini-4-argon-high`), NEVER `nebula` and NEVER Ultra.
4. **Ultra Accounts Strictly Excluded**: Ultra accounts (`innoria-team`, `ultra-2` / `lthn.Ariana`) are currently token-exhausted and strictly excluded from all task routing pools.

## Rule: Mandatory Clef Swarm Participation Across All Fleet Tasks (Sự Tham Gia Của Clef Là Bắt Buộc)

Every fleet job (dispatched via `fleet_run`, `fleet_parallel`, `/api/fleet/run-sync`, `/api/fleet/run`, or autonomous DAG enqueue) MUST engage the **Clef Swarm**:
1. **Tri-Tier Cognitive Pre-Routing (`decide_async`)**: Pre-classifies domain, complexity $[0.0, 4.0]$, and node persona across Cloudflare Free Edge PoPs $\to$ Modal T4 27B $\to$ Local In-Process Surrogate. Cost strictly `$0.00` (`output_tokens == 0`).
2. **Deep Dialect Metaprompting (`synthesize_specification`)**: Compiles raw prompts into target dialects (Claude XML `<context>/<task>/<constraints>`, Gemini JSON Schema, Codex scaffold) and injects sovereign invariants.
3. **Negative-Selection Anomaly Self-Gate (`clef_self_gate`)**: Rejects corrupted dialects, token bloat, or invalid assertions prior to dispatch.
4. **Automated UAT Specification & Sentinel Anti-Fabrication (`PDCAEvolutionEngine` & `clef_sentinel`)**: Automatically generates and executes verification commands to enforce **Zero-Fake-Pass**.
- **Fail-Closed Sovereign Mandate**: Any job lacking Clef telemetry or verification fails closed immediately (`JobStatus.FAILED`).

## Rule: Mandatory Gemini 4 Argon Strict Definition-of-Done (DoD) Reminder Invariant

Whenever the planner decomposes or delegates tasks to **Gemini 4 Argon** (`gemini-4-argon-high`, `gemini-4-argon-medium`, `gemini-4-argon-low`), it MUST proactively guard against premature `"Done"` declarations by embedding the **`[STRICT GEMINI 4 ARGON DEFINITION OF DONE (DoD) REMINDER — ZERO SHORTCUTS]`** block (`ensure_gemini_dod_reminder` / `build_gemini_strict_dod_reminder` in `tools/sovereign_victory_critic.py` and `agy_pinned_monitor.victory_critic_gate`):

1. **`[DoD-1] Zero Placeholders / Ellipsis`**: Never leave `TODO`, `FIXME`, `# ...`, `pass` placeholders, or truncated functions. Deliver 100% complete, production-ready code.
2. **`[DoD-2] 100% Requirement & Edge-Case Coverage`**: Implement every explicit requirement, boundary condition, and failure mode without dodging or simplifying.
3. **`[DoD-3] Non-Trivial Empirical Tests (fake_pass_risk_score == 0.0)`**: Every `def test_*` function must assert on concrete computed values and state transitions. `assert True`, `assert 1 == 1`, zero-assertion tests, and over-mocked SUTs are strictly forbidden.
4. **`[DoD-4] Fail-Closed Exception Hygiene`**: Never swallow exceptions with `except Exception: pass` or bare `except: pass`.
5. **`[DoD-5] Mandatory Pre-"Done" 4-Axis Victory Critic Self-Check`**: Do NOT declare `Done`, `Completed`, or `Task Victory` until Requirement Alignment, Empirical Proof (`pytest` exit code 0), Counterfactual Rigor, and Regression & Argon Safety (zero `gemini-3.8-flash*` leaks) are 100% satisfied.

### Self-Check Before Responding

Before producing any code block >20 lines, ask yourself:
- "Am I generating this inline instead of delegating?"
- "Could this be a fleet_run task if I paste enough context?"
- "Did I actually call fleet_run/fleet_parallel, or am I about to fabricate?"
- "If routing to Gemini 4 Argon (`gemini-4-argon-{high,medium,low}`), did I embed the Strict Definition-of-Done (`[DoD-1]`..`[DoD-5]`) reminder?"
- "If routing Claude, did I verify it NEVER touches an Ultra account?"
- "If routing Gemini, did I verify it NEVER touches Nebula (Nebula only has Opus 4.8)?"

