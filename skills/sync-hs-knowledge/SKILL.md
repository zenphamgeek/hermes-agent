---
name: sync-hs-knowledge
description: Sync and query HS codes and Vietnam customs tariff.
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
    - hs-code
    - customs
    - tariff
    - vietnam
    - trade
    related_skills:
    - sync-hse-knowledge
---
# HS Knowledge Sync Skill (`sync-hs-knowledge`)

Orchestration skill for managing, synchronizing, querying, and auditing the local Harmonized System (HS), AHTN, and Vietnam National Tariff & Classification Knowledge Base.

All operations execute deterministically through the bundled `hs-sync` CLI / scripts. Do not write ad-hoc scrapers or bypass policy controls.

## When to Use

Use this skill when:
- The user asks to lookup, search, or verify HS codes, commodity descriptions, or import/export tariff rates for Vietnam.
- The user asks to synchronize, update, or plan customs ruling / tariff database sync (`plan`, `run`, `resume`, `reparse`).
- The user requests temporal tariff lookups (`--as-of "YYYY-MM-DD"`).
- The user asks to check customs rulings, legal citations, or source acquisition health.

Do NOT use for general unscheduled web scraping of unauthorized customs portals.

## Operational Discipline & Principles

1. **Deterministic Core**: All fetch, parse, normalize, and indexing steps are handled by verified Python pipelines. LLM assistance is strictly advisory (`machine_suggested`) and never overrides verified legal facts.
2. **Official-First & Evidence-First**: Every normalized legal entity, tariff rate, and ruling links back to an immutable raw artifact, SHA-256 hash, source URL, page citation, and effective dates (`valid_from` / `valid_to`).
3. **No Circumvention / Unattended by Design**: No CAPTCHA solving, stealth browser spoofing, or proxy evasion. When managed challenges are encountered, the engine automatically falls back to sanctioned mirrors or quarantines the source with `MACHINE_ACCESS_REQUIRED`.
4. **License & Entitlement Gated**: WCO and proprietary sources remain `PENDING_ENTITLEMENT` / metadata-only until valid entitlements are approved.

---

## Command Reference

Run commands via the local Python entrypoint with `--json` for structured, machine-readable output:

```bash
# General Syntax
python3 skills/sync-hs-knowledge/scripts/hs_sync.py <command> [options] --json
```

### 1. Source Registry & Health
- **List sources and current policy**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py sources list --json
  ```
- **Validate registry YAML integrity**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py sources validate --json
  ```
- **Check source acquisition health & circuit breaker**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py acquisition status --source VN_CUSTOMS_RULINGS --json
  ```

### 2. Synchronization & Ingestion
- **Plan dry-run (preview scope, counts, policy decisions without mutating DB)**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py plan --source VN_CUSTOMS_RULINGS --mode incremental --json
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py plan --scope vietnam-core --mode full --json
  ```
- **Execute Sync Run**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py run --source VN_CUSTOMS_RULINGS --mode incremental --json
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py run --scope vietnam-core --mode full --json
  ```
- **Resume interrupted run from checkpoint**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py resume <RUN_ID> --json
  ```
- **Reparse existing raw artifacts with updated parser version (no re-download)**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py reparse --parser pdf --from-version 1.0 --to-version 1.1 --json
  ```

### 3. On-Demand Targeted Crawling & Real-Time Sync
- **Trigger on-demand crawl by HS code, chapter, or keyword**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py on-demand "8471.30.20" --scope vietnam-core --json
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py on-demand "máy tính xách tay" --sources VN_CUSTOMS_RULINGS,VN_CUSTOMS_TARIFF --json
  ```

### 4. Search & Temporal (`as_of`) Querying
- **Hybrid lookup (Lexical + Vector + Temporal Filter)**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py search "bộ điều khiển lập trình PLC" --as-of "2026-08-20" --json
  ```
- **Inspect HS Code Node Hierarchy & Rates**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py hs get "8471.30.20" --edition "2022" --as-of "2026-08-20" --json
  ```

### 5. Quality, License & Audit
- **Check pending license readiness**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py license readiness --json
  ```
- **List data quality review queue**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py quality list --severity high --json
  ```
- **Infrastructure Health & Migration**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py health --json
  ```

### 6. Webhooks & Real-Time Subscriber Event Hub
- **Register subscriber (e.g. ERP, Odoo, Customs Clearance API)**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py webhook add odoo-erp "https://erp.internal/webhook" --events "hs.ruling.published,hs.tariff.changed" --secret "my-token-secret" --json
  ```
- **List registered subscribers**:
  ```bash
  python3 skills/sync-hs-knowledge/scripts/hs_sync.py webhook list --active-only --json
  ```

---

## Agent Response Workflow

When a user requests HS synchronization or data lookup:
1. **Analyze Intent**:
   - If broad/uncertain sync: default scope is `vietnam-core`. Run `plan` first.
   - If lookup: run `search` or `hs get` with explicit `--as-of` date (defaulting to current date).
2. **Execute via CLI**: Run the corresponding script with `--json`.
3. **Present Audit Summary**:
   - Status, Scope, Sources run.
   - Discovered, Downloaded, Unchanged, Parsed, Normalized counts.
   - Citation info (Source URL, Artifact SHA-256, Page/Section, Effective dates).
