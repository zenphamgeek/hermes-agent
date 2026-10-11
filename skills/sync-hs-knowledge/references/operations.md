# Operations and Maintenance

## Run Modes
- `plan`: Dry-run mode. Evaluates source reachability, policy decisions, and item count estimation without DB mutation.
- `incremental`: Syncs only items added or modified since the last successful checkpoint cursor.
- `full`: Complete sync across the target jurisdiction / scope with checkpoint tracking.
- `reparse`: Re-runs document parsers on existing stored raw artifacts without re-downloading files.
- `reconcile`: Compares database items against source catalogs to detect missing or tombstoned entries.

---

## Hermes Agent Automated Crawl Schedule

The following 4 automated cron jobs are registered in Hermes Agent (`hermes cron list`):

| Job ID | Job Name | Schedule (ICT) | Scope / Target Sources | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `e68251d4cfb6` | `hs-sync-daily-vietnam` | `0 2 * * *` (02:00 Daily) | `vietnam-core` (VN_GOV, VBPL, Tariff, Rulings, VNTR) | Daily incremental sync of new legal docs, rulings, and tariff notices |
| `9eb1fc252aa4` | `hs-sync-weekly-regional` | `0 2 * * 0` (02:00 Sun) | `ASEAN_AHTN`, `WCO_PUBLIC_META` | Weekly synchronization of regional AHTN and WCO metadata |
| `c309d95152a5` | `hs-sync-monthly-reconcile` | `0 3 1 * *` (03:00 1st of month) | `vietnam-core` + All active sources | Full database reconciliation, hierarchy integrity audit & coverage manifest export |
| `2d8207fcc4e9` | `hs-sync-daily-health` | `0 6 * * *` (06:00 Daily) | All sources & Infrastructure | Connectivity, circuit breaker health probe, and license entitlement readiness |

---

## Manual Operational Commands

### 1. On-Demand Targeted Taxonomy Crawling
```bash
# Trigger on-demand crawl for specific 8-digit HS code
hs-sync on-demand "8471.30.20" --scope vietnam-core --json

# Trigger on-demand crawl by commodity keyword or chapter
hs-sync on-demand "máy tính xách tay" --sources VN_CUSTOMS_RULINGS,VN_CUSTOMS_TARIFF --json

# Asynchronous execution via Celery Task
python3 -c "from service.pipeline.tasks import sync_taxonomy_task; res = sync_taxonomy_task.delay('8471.30.20'); print(res.id)"
```

### 2. Batch & Scope Synchronization
```bash
# Sync specific source
hs-sync run --source VN_CUSTOMS_RULINGS --mode incremental --json

# Sync entire Vietnam scope
hs-sync run --scope vietnam-core --mode incremental --json

# Dry-run plan preview
hs-sync plan --scope vietnam-core --json
```

### 3. Resume & Reparse
```bash
# Resume an interrupted crawl run
hs-sync resume <RUN_ID> --json

# Reparse all stored artifacts after HTML/PDF parser updates
python3 -c "from service.db.session import get_db_session; from service.pipeline.orchestrator import SyncOrchestrator; orch=SyncOrchestrator(db=next(get_db_session())); print(orch.reparse_all())"
```

### 4. Inspection & Auditing
```bash
# Check infrastructure health
hs-sync health --json

# View license readiness
hs-sync license readiness --json

# Run offline WAF resilience simulation
hs-sync resilience-lab run --scenario challenge-matrix --json

# Export coverage manifest report
python3 skills/sync-hs-knowledge/scripts/export_coverage.py --json
```

---

### 4. Webhook Subscriber Management

```bash
# Register a subscriber (e.g. ERP, Odoo)
hs-sync webhook add erp-connector "https://erp.internal/webhook" --events "hs.ruling.published,hs.tariff.changed" --secret "token-12345"

# List active subscriptions
hs-sync webhook list --active-only

# Send reachability test ping
hs-sync webhook test <subscription_id>

# Manually trigger event delivery
hs-sync webhook deliver "hs.tariff.changed" '{"chapter": "84", "notes": "Tariff Decree updated"}'

# Remove a subscriber
hs-sync webhook remove <subscription_id>
```

