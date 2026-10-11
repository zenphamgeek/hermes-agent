---
title: "Sync Hse Knowledge — Sync, version, and evaluate HSE knowledge and standards"
sidebar_label: "Sync Hse Knowledge"
description: "Sync, version, and evaluate HSE knowledge and standards"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Sync Hse Knowledge

Sync, version, and evaluate HSE knowledge and standards.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/sync-hse-knowledge` |
| Version | `1.0.0` |
| Author | hermes-community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `hse`, `safety`, `environment`, `standards`, `vietnam` |
| Related skills | [`sync-hs-knowledge`](/docs/user-guide/skills/bundled/sync-hs-knowledge/sync-hs-knowledge-sync-hs-knowledge) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Deterministic HSE Knowledge Platform & Sync Skill

This skill synchronizes, parses, versions, indexes, and evaluates Health, Safety, and Environment (HSE) knowledge across Vietnamese laws, QCVN technical regulations, international standards, and chemical SDS data.

## When to Use

Use this skill when:
- The user asks to lookup, search, or evaluate HSE regulations, QCVN standards, environmental laws, or occupational exposure limits (OELs).
- The user requests chemical safety data, SDS/GHS sheets, or CAS number lookups.
- The user requests facility applicability checks or legal register evaluation.
- The user asks to synchronize or update HSE knowledge sources (`sources list`, `sync`, `plan`).

Do NOT use for general health advice or unverified medical diagnosis.

## Quick CLI Reference (`hse-knowledge`)

All commands support `--json` for structured machine output.

```bash
# 1. Source Discovery & Validation
hse-knowledge sources list
hse-knowledge sources validate
hse-knowledge sources readiness

# 2. Sync Planning & Execution
hse-knowledge plan --scope vietnam-core --mode incremental
hse-knowledge sync --scope vietnam-core --mode incremental
hse-knowledge sync --scope vietnam-core --mode full
hse-knowledge resume <run_id>
hse-knowledge reparse --parser sds --version 1.0.0

# 3. Real-Time On-Demand Taxonomy & Topic Crawling
hse-knowledge on-demand "acetone" --scope vietnam-core
hse-knowledge on-demand "QCVN 05:2023/BTNMT" --callback-url https://erp.internal/callback

# 4. Applicability & Legal Registers
hse-knowledge applicability evaluate --facility FAC_ID --as-of 2026-08-21
hse-knowledge rules validate
hse-knowledge rules test --suite vietnam-core

# 5. Hybrid Search & Temporal Lookups
hse-knowledge search "giới hạn nồng độ bụi trong không khí" --as-of 2026-08-21
hse-knowledge chemicals get --cas 67-64-1
hse-knowledge oels get --substance "toluene"

# 6. Webhooks Management
hse-knowledge webhook add odoo-erp https://erp.internal/webhooks/hse-events --secret sec_hse_2026
hse-knowledge webhook list
hse-knowledge webhook test <subscription_id>

# 7. Health & Resilience Lab
hse-knowledge health
hse-knowledge resilience-lab run --scenario challenge-matrix
```

## Progressive Disclosure & Reference Links

- **Authority Hierarchy & Precedence**: [`references/authority-model.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/authority-model.md)
- **Data Model & Temporal Schema**: [`references/data-model.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/data-model.md)
- **Applicability Rule DSL**: [`references/applicability-dsl.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/applicability-dsl.md)
- **Chemical, SDS & GHS Normalization**: [`references/chemical-sds-ghs.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/chemical-sds-ghs.md)
- **Hazard & Hierarchy of Controls**: [`references/hazard-control-taxonomy.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/hazard-control-taxonomy.md)
- **License & Copyright Gating**: [`references/license-policy.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/license-policy.md)
- **Privacy & Medical Data Boundary**: [`references/privacy-boundary.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/privacy-boundary.md)
- **Operations & Run Lifecycles**: [`references/operations.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/operations.md)
- **OpenAPI Endpoints**: [`references/api-specs.md`](https://github.com/NousResearch/hermes-agent/blob/main/skills/sync-hse-knowledge/references/api-specs.md)
