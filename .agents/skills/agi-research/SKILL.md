---
name: agi-research
description: >-
  Short alias for sovereign-agi-manifest. Run deep AI research, 6-axis AI capability evaluation
  (Delta_F, EWC_Retention, Submodular_Gain, ECE, NSR, GFR), and Opus 5.5 Council task orchestration
  across the 14 eligible AGY Fleet Pro nodes under ADR-000 directly in chat without bash.
version: 1.0.0
author: Principal AI Researcher (User) & Antigravity
platforms: [linux, macos]
metadata:
  hermes:
    manifest_id: ADR-000-SOVEREIGN-AGI-RESEARCH-MANIFEST
    manifest_sha256: 8bf5906aa3789c95756ba142547f9864c184754865a06a60b4dd55564bad32c2
    tags: [agi, research, opus-5-5, capability-evaluation, secondbrain]
    related_skills: [sovereign-agi-manifest, agy-fleet]
---

# AGI Research & Opus 5.5 Capability Evaluation Skill (`agi-research`)

Direct chat shortcut for [`sovereign-agi-manifest`](file:///home/zen/hermes-agent/.agents/skills/sovereign-agi-manifest/SKILL.md) under the **Immutable Sovereign AGI Research Manifest (`ADR-000`)**.

## How to Use in Chat (Zero Bash Required)

Simply type in any chat session:
- `/agi-research <chủ đề nghiên cứu chuyên sâu hoặc đánh giá năng lực AI>`
- `/sovereign-agi-manifest <chủ đề nghiên cứu chuyên sâu hoặc đánh giá năng lực AI>`

## Agent Execution Action

When activated, immediately invoke the native `agy-fleet` MCP tool `sovereign_agi_manifest_orchestrate`:
```json
{
  "ServerName": "agy-fleet",
  "ToolName": "sovereign_agi_manifest_orchestrate",
  "Arguments": {
    "research_goal": "<User's research topic or AI capability evaluation query>",
    "domain": "hermes_agent",
    "k_memories": 5,
    "dispatch_to_swarm": true,
    "run_full_audit": false
  }
}
```
Follow all invariants in [`sovereign-agi-manifest/SKILL.md`](file:///home/zen/hermes-agent/.agents/skills/sovereign-agi-manifest/SKILL.md) and [`ADR-000-Sovereign-AGI-Research-Manifest.md`](file:///home/zen/Obsidian/SecondBrain/10-Areas/AI%20Engineering/ADR-000-Sovereign-AGI-Research-Manifest.md).
