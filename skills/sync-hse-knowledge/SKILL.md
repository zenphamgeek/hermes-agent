---
name: sync-hse-knowledge
description: Sync, version, and evaluate HSE knowledge and standards.
version: 1.0.0
author: hermes-community
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - hse
    - safety
    - environment
    - standards
    - vietnam
    related_skills:
    - sync-hs-knowledge
---
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

- **Authority Hierarchy & Precedence**: [`references/authority-model.md`](references/authority-model.md)
- **Data Model & Temporal Schema**: [`references/data-model.md`](references/data-model.md)
- **Applicability Rule DSL**: [`references/applicability-dsl.md`](references/applicability-dsl.md)
- **Chemical, SDS & GHS Normalization**: [`references/chemical-sds-ghs.md`](references/chemical-sds-ghs.md)
- **Hazard & Hierarchy of Controls**: [`references/hazard-control-taxonomy.md`](references/hazard-control-taxonomy.md)
- **License & Copyright Gating**: [`references/license-policy.md`](references/license-policy.md)
- **Privacy & Medical Data Boundary**: [`references/privacy-boundary.md`](references/privacy-boundary.md)
- **Operations & Run Lifecycles**: [`references/operations.md`](references/operations.md)
- **OpenAPI Endpoints**: [`references/api-specs.md`](references/api-specs.md)
