# Rule 06: Autonomous Proactive Action & Universal Odoo QWeb/Owl Convergence Invariants

> **Sovereign Principles**:
> 1. **Kích Hoạt Không Cần Hỏi (Report After, Not Ask Before)**: Execute all non-destructive engineering tasks, self-healing actions, test suites, refactoring, and domain synchronizations proactively. Report empirical results with real measurement evidence. Never stall execution with passive permission questions.
> 2. **Universal Odoo QWeb & Owl UI/UX Convergence**: Every internal tool, operational dashboard, telemetry HUD, and widget must adhere to the Odoo 20 Owl Component architecture and semantic QWeb template standard, enabling frictionless future embedding into Insilos Enterprise (Odoo 20).

---

## 1. Sovereign Invariant 1.12: Autonomous Proactive Action (Kích Hoạt Không Cần Hỏi)

### 1.1. Core Mandate & Philosophy
The AI pair programmer, Hermes Agent orchestrator, and AGY Fleet swarm exist to solve engineering problems autonomously. Asking passive confirmation questions (such as *"Do you want me to run the tests?"*, *"Should I proceed with fixing this bug?"*, *"Bạn có muốn tôi làm tiếp không?"*) introduces dead latency and violates the Sovereign Flow principle.

**The Proactive Protocol**:
$$\text{Sense State} \longrightarrow \text{Formulate Plan} \longrightarrow \text{Execute Implementation} \longrightarrow \text{Verify Empirical Evidence} \longrightarrow \text{Report Findings}$$

All actions are executed immediately. The user receives a comprehensive report accompanied by verifiable tool execution logs **after** the work is complete.

### 1.2. Scope of Autonomous Authority
The system possesses full autonomous authority to execute without prior prompting:
1. **Test Execution & Quality Gate Audits**: Running pytest, vitest, eslint, ast-grep, ffmpeg loudness analysis, and visual defect scans across all 6 managed domains.
2. **Automated Bug Fixing & Self-Healing**: Diagnosing test failures, applying local code patches, restarting crashed local services (e.g. 9router, cloudflared, fleet_manager), and healing broken configurations.
3. **Modal GPU Fleet Management & Zombie Termination**: Killing runaway GPU worker containers (`modal app stop`, `kill_modal.sh`), rebalancing batch jobs via Round-Robin across 9 active profiles, and enforcing daily spend ceiling ($5.00/day).
4. **Git Feature Branch Operations**: Creating feature branches (`fleet/{node-label}/{description}`), committing atomic conventional commits (`feat:`, `fix:`, `refactor:`), and pushing development branches to remotes. (Merging to `main` remains reserved for the human sovereign).
5. **Code Refactoring & Optimization**: Cleaning unused imports, formatting code, decomposing oversized functions, and refactoring scripts to satisfy sovereign quality invariants.

### 1.3. The Catastrophic Safety Circuit Breaker (The Single Exception)
The system **MUST STOP AND ASK** explicit user permission if and only if an action causes **irreversible, catastrophic data loss** per the `accidental-data-loss-prevention` standard:
- Executing destructive SQL: `DROP DATABASE`, `DROP TABLE`, unconstrained `DELETE FROM` without `WHERE` clause on production databases.
- Permanent deletion of cloud storage buckets or primary production datasets: `gsutil rm -r`, `gcloud storage rm` targeting production infrastructure.
- Deletion or rotation of master cryptographic secrets and production tokens (specifically protected by Rule 05: Modal Master Tokens in `modal_token_profile.md`).
- Force-pushing (`git push --force`) or hard-resetting branches on shared upstream production repositories (`main`, `master`).

### 1.4. Self-Healing Circuit Breaker & Escalation
- For any autonomous self-healing loop (e.g. in `governance/self_healing_engine.py`):
  - The system will retry automated remediation up to **3 consecutive attempts**.
  - If 3 consecutive remediation attempts fail, the circuit breaker opens, execution halts on that specific domain, and an urgent Escalation Notice is compiled with before/after diagnostic logs.

---

## 2. Sovereign Invariant 1.13: Universal Odoo QWeb & Owl UI/UX Convergence

### 2.1. Core Mandate & Convergence Strategy
All internal tools, monitoring cockpits, telemetry HUDs, and management widgets across the entire ecosystem—including:
- **AGY Fleet Manager** (`fleet_manager.py` / `/static/`)
- **Modal Multi-GPU Monitor** (`modal_fleet_monitor.py` / status cockpit)
- **Tokenomics & Cost Dashboard** (`web/src/components/...`)
- **Trae Autopilot Widget** (`TraeAutopilotWidget.tsx`)
- **VerticalRisk GRC Telemetry** (`VerticalRisk/extensions/...`)
- **YouTube Content Factory Telemetry** (Manim & TTS rendering monitors)

**MUST** be architected such that their user interface and client logic can be cleanly ported, embedded, or compiled into **Odoo 20 Owl Components** (`@odoo/owl`) with **semantic QWeb templates** (`<t t-name="...">`) for the Insilos Enterprise platform (`/home/zen/insilos-release-work`).

### 2.2. Standard 1: Owl Component Architecture Parity
Every UI widget must maintain a 1:1 structural correspondence with Odoo 20 Owl Component lifecycle and state management:
1. **Component Class**: Modeled as `class X extends Component` with reactive state managed via `useState({...})`.
2. **Lifecycle Hooks**:
   - `onWillStart`: Asynchronous pre-flight data loading (fetching status, configurations).
   - `onMounted`: Setting up polling intervals, WebSocket listeners, or DOM canvas attachments.
   - `onWillUnmount`: Cleanup of timers, observers, and event listeners.
3. **Props Validation**: Explicit static `props` definitions declaring all inputs, types, and defaults.

### 2.3. Standard 2: Decoupled API & RPC Transport Layer
UI widgets must never tightly couple rendering with raw ad-hoc `fetch()` calls or backend-specific protocols.
- **Service Abstraction**: All communication must go through an RPC service adapter that mirrors Odoo's native `useService("rpc")`:
  ```javascript
  // Odoo 20 Owl Pattern
  const rpc = useService("rpc");
  const data = await rpc("/api/fleet/status", {});
  ```
- In standalone mode (e.g. React/Vite dev harness), the widget uses an HTTP client shim with identical method signatures (`call(route, params)`), ensuring zero code changes when migrating to Odoo 20.

### 2.4. Standard 3: Odoo 20 Semantic QWeb Template Directives
All UI layouts must be authored or trivially convertible into native Odoo 20 QWeb XML:
- ❌ **Strictly Forbidden Directives**: `t-esc` and `t-raw` are **completely removed** in Odoo 20. Any use is a fatal syntax violation.
- ✅ **Mandatory Interpolation**: Always use `<t t-out="expression"/>` for dynamic string or HTML rendering.
- ✅ **Loop Keying**: In Owl client-side templates, every `<t t-foreach="items" t-as="item">` loop **MUST** declare `t-key="item.id"`.
- ✅ **Conditional Rendering**: Use `<t t-if="condition">`, `<t t-elif="condition">`, `<t t-else="">`.

### 2.5. Standard 4: Visual Design Tokens & Rule 29 Borderless Canvas
UI design must blend the **Odoo 20 Design System (Bootstrap 5)** with the **ZENPHAM Neo-Noir Obsidian Aesthetic**:
1. **Neo-Noir Color Palette**:
   - Obsidian Void (Canvas BG): `#080a0f` / `rgba(8, 10, 15, 0.95)`
   - Obsidian Surface: `#0c0d12` / `rgba(12, 13, 18, 0.85)`
   - Obsidian Border / Hairline: `rgba(255, 255, 255, 0.08)` / `#1e293b`
   - Cyber Cyan (Primary / Data): `#38bdf8`
   - Sovereign Gold (Accent / Metric): `#ffd700`
   - Emerald Pulse (Healthy / Active): `#10b981`
   - Crimson Flare (Alert / Error): `#ef4444`
2. **Rule 29 Borderless Canvas Parity (Ban Clunky Card Boxes)**:
   - Eliminating thick, opaque, static bounding card boxes (`.card.card-body` with opaque white/grey background).
   - Elements must float directly on the Obsidian canvas, delimited by subtle 1px frosted glass hairlines (`border border-secondary-subtle border-opacity-10`) and hierarchical typography rather than heavy box containers.

---

## 3. Concrete Translation Blueprint: React/TSX to Odoo 20 Owl & QWeb

### 3.1. Reference React/TSX Widget (Input)
```typescript
// Legacy React / TSX Pattern
export function ModalFleetWidget({ compact = false }) {
  const [fleet, setFleet] = useState<ModalStatus | null>(null);
  useEffect(() => {
    fetchModalStatus().then(setFleet);
    const id = setInterval(() => fetchModalStatus().then(setFleet), 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="neo-cockpit p-4">
      <div className="flex justify-between">
        <span className="text-cyan-400 font-mono">MODAL GPU FLEET</span>
        <span className="text-emerald-400">{fleet?.workers_active ?? 0} WORKERS</span>
      </div>
    </div>
  );
}
```

### 3.2. Sovereign Odoo 20 Owl Component (Target)
```javascript
/** @odoo-module **/
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ModalFleetWidget extends Component {
    static template = "hermes.ModalFleetWidget";
    static props = {
        compact: { type: Boolean, optional: true },
    };

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            fleet: null,
            loading: true,
        });

        onWillStart(async () => {
            await this.loadStatus();
        });

        onMounted(() => {
            this.pollTimer = setInterval(() => this.loadStatus(), 5000);
        });

        onWillUnmount(() => {
            if (this.pollTimer) clearInterval(this.pollTimer);
        });
    }

    async loadStatus() {
        try {
            const data = await this.rpc("/api/modal/fleet/status", {});
            this.state.fleet = data;
            this.state.loading = false;
        } catch (err) {
            console.error("ModalFleetWidget load failed", err);
        }
    }
}
```

### 3.3. Sovereign Odoo 20 QWeb Template (Target)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="hermes.ModalFleetWidget">
        <div class="o_modal_fleet_cockpit p-4 bg-dark text-white rounded-3 border border-secondary border-opacity-25"
             style="background: #080a0f !important;">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <span class="font-monospace fw-bold" style="color: #38bdf8;">MODAL GPU FLEET</span>
                <span class="badge rounded-pill" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">
                    <t t-out="state.fleet ? state.fleet.total_workers_active : 0"/> WORKERS ACTIVE
                </span>
            </div>
            <div class="row g-2" t-if="state.fleet and state.fleet.all_workspace_registry">
                <t t-foreach="state.fleet.all_workspace_registry" t-as="ws" t-key="ws.line">
                    <div class="col-md-4 col-sm-6">
                        <div class="p-2 border border-secondary border-opacity-10 rounded">
                            <span class="d-block small text-muted font-monospace" t-out="ws.profile"/>
                            <span class="d-block text-truncate small" style="color: #ffd700;" t-out="ws.token_id"/>
                        </div>
                    </div>
                </t>
            </div>
        </div>
    </t>
</templates>
```

---

## 4. Council Verification & Quality Gates

The Multidisciplinary Council enforces these standards automatically:
1. **Static AST Linter**: Scans all HTML/XML templates to ensure 0 occurrences of deprecated `t-esc` or `t-raw`, and verifies mandatory `t-key` in `t-foreach` loops.
2. **Rule 29 Borderless Check**: Confirms all dashboard views avoid opaque card background containers.
3. **Evidence-First Audit**: Proactive execution logs must contain genuine tool commands, exit codes, and timestamps—zero fabricated test passes or fake assertions.
