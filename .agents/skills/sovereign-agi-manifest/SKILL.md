---
name: sovereign-agi-manifest
description: >-
  Invoke the Immutable Sovereign AGI Research & Opus 5.5 Task-Orchestration Manifest (ADR-000)
  directly in chat without bash. Synthesizes endogenous (L3/B6) and exogenous SecondBrain knowledge,
  evaluates AI capabilities across the 6-Axis Quantitative Matrix (Delta_F, EWC_Retention,
  Submodular_Gain, ECE, NSR, GFR), and orchestrates 3-Stage Opus 5.5 Council research and task
  delegation across the 17 eligible AGY Fleet Pro nodes (0% Ultra, 0% nebula). Use whenever the
  user types /sovereign-agi-manifest, /agi-research, asks to research toward AGI, evaluate AI
  capabilities, or assign tasks under the Sovereign AGI Manifest.
version: 1.1.0
author: Principal AI Researcher (User) & Antigravity
platforms: [linux, macos]
metadata:
  hermes:
    manifest_id: ADR-000-SOVEREIGN-AGI-RESEARCH-MANIFEST
    manifest_sha256: 87a709a855ea92adc62f5e1c335132855d7d798fb9fce829e4fe4c202a475d14
    tags: [agi, sovereign-manifest, opus-5-5, secondbrain, capability-eval, fleet-pro]
    related_skills: [agi-research, agy-fleet, decision-ledger, core-knowledge-compiler]
---

# Sovereign AGI Research & Opus 5.5 Task-Orchestration Skill (`sovereign-agi-manifest`)

Executes the **Immutable Sovereign AGI Research & Opus 5.5 Task-Orchestration Manifest (`ADR-000`)** directly inside any chat session **with zero manual bash commands required**.

---

## 1. How to Invoke in Chat

In any chat session across any workspace, trigger this skill using any of the following:
- `/sovereign-agi-manifest <mục tiêu nghiên cứu hoặc đánh giá AI>`
- `/agi-research <mục tiêu nghiên cứu hoặc đánh giá AI>`
- Natural language: *"Dùng skill sovereign-agi-manifest để nghiên cứu sâu và giao việc cho các node Opus 5.5 về..."*

---

## 2. Zero-Bash Execution Protocol (MCP-First Workflow)

When this skill is triggered in a chat session, the agent MUST execute the following steps via **MCP tools** (no manual bash required from the user):

### Step 1 — Cryptographic Manifest Lock, Knowledge Synthesis & 6-Axis AI Capability Evaluation
Call the native `agy-fleet` MCP tool `sovereign_agi_manifest_orchestrate`:
```json
{
  "ServerName": "agy-fleet",
  "ToolName": "sovereign_agi_manifest_orchestrate",
  "Arguments": {
    "research_goal": "<User's research objective or capability evaluation topic>",
    "domain": "hermes_agent",
    "k_memories": 5,
    "dispatch_to_swarm": true,
    "run_full_audit": false
  }
}
```
What this tool executes in-process (Python, zero shell overhead):
1. **Cryptographic Verification (`verify_immutable_agi_manifest`)**: Verifies canonical JSON `SHA-256 == 87a709a855ea92adc62f5e1c335132855d7d798fb9fce829e4fe4c202a475d14`, `ADR-000-Sovereign-AGI-Research-Manifest.md`, and `.agents/rules/00_sovereign_agi_research_manifest.md`. Raises `RuntimeError("Immutable AGI Manifest Violation")` on any tampering.
2. **Endogenous & Exogenous Knowledge Synthesis**:
   - Curates consolidated `L3/B6` memories via $(1 - 1/e)$-approximate **Submodular Facility-Location** (`curate_submodular_causal_memories`, $G_{\text{sub}} \ge 1.05$).
   - Retrieves top high-entropy exogenous research priors (`arXiv`, `GitHub Trending`, `nvidia/Nemotron-Personas-Vietnam`) and predicts cortical routing via the `< 0.5ms` ONNX surrogate (`predict_with_onnx_surrogate`).
3. **6-Axis Quantitative AI Capability Evaluation**:
   - **Axis 1 (Epistemic Surprise / Free Energy)**: $\Delta F < 0.0$
   - **Axis 2 (Continual Plasticity & Stability)**: $\text{EWC}_{\text{retention}} \ge 0.90$ (`val_loss < 0.55`)
   - **Axis 3 (Submodular Curation Gain)**: $G_{\text{sub}} \ge 1.05$
   - **Axis 4 (Epistemic Calibration)**: $\text{ECE} \le 0.15$
   - **Axis 5 (Counterfactual Negation Sensitivity)**: $\text{NSR} \ge 0.75$
   - **Axis 6 (Grounding Fidelity)**: $\text{GFR} \ge 0.80$
4. **3-Stage Opus 5.5 Council Task Assignment (`dispatch_to_swarm=true`)**:
   - Automatically dispatches or enqueues the synthesized work packet to the **17 eligible AGY Fleet Pro nodes** (`agy-home`, `codegeekvn`, `sunward`, `justaskgao`, `insilos`, `zeninallgeek`, `zenphamgeek`, `coderedgen`, `immoon0009-gmail-com`, `traimai`, `binhthuong`, `gaopham`, `ai-digimate`, `nahlaleah102`, `just.ask.mr.zen`, `tsmei0209-gmail-com`, `zenonmind`) with `tier="pro"`, `model="claude-opus-5-5-high"` (and automatic Pro `gemini-4-argon-high` CLI fallback only if upstream Claude 5h burst quota is in `HTTP 429` cooldown).
   - **Hard Exclusions**: `0%` Ultra nodes (`innoria-team`, `ariana`/`ultra-2`) and `0%` `nebula`.

### Step 2 — Multi-Node Parallel Dialectic Critique (Optional Deep Research Mode)
If the user requests multi-node parallel dialectic critique across the Opus 5.5 Council, call:
```json
{
  "ServerName": "agy-fleet",
  "ToolName": "fleet_parallel",
  "Arguments": {
    "prompt": "[ADR-000-SOVEREIGN-AGI-RESEARCH-MANIFEST] <Synthesized Research Prompt + SecondBrain Context>",
    "tier": "pro",
    "count": 3
  }
}
```

### Step 3 — Token-Compact Obsidian ADR Persistence
Persist any new architectural proof or capability discovery into `/home/zen/Obsidian/SecondBrain/10-Areas/AI Engineering/ADR-<NNN>-<Title>.md` obeying the **$\le 800$-word Machine-First Compact Schema** (YAML frontmatter + equations + dense Markdown tables) and link it in `Home.md`.

---

## 3. Immutable Constitutional References

- **Obsidian Manifest ADR**: [`ADR-000-Sovereign-AGI-Research-Manifest.md`](file:///home/zen/Obsidian/SecondBrain/10-Areas/AI%20Engineering/ADR-000-Sovereign-AGI-Research-Manifest.md)
- **Opus 5.5 Audit Matrix**: [`ADR-001-Opus55-AGI-Sovereign-Audit-Matrix.md`](file:///home/zen/Obsidian/SecondBrain/10-Areas/AI%20Engineering/ADR-001-Opus55-AGI-Sovereign-Audit-Matrix.md)
- **FEP, EWC & Submodular Proofs**: [`ADR-002-FEP-EWC-Submodular-Proofs.md`](file:///home/zen/Obsidian/SecondBrain/10-Areas/AI%20Engineering/ADR-002-FEP-EWC-Submodular-Proofs.md)
- **Always-On Workspace Rule**: [`.agents/rules/00_sovereign_agi_research_manifest.md`](file:///home/zen/hermes-agent/.agents/rules/00_sovereign_agi_research_manifest.md)
- **Core Engine Implementation**: [`tools/cognitive_secondbrain_engine.py`](file:///home/zen/hermes-agent/tools/cognitive_secondbrain_engine.py)
