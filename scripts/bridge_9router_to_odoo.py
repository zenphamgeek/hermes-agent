#!/usr/bin/env python3
"""
scripts/bridge_9router_to_odoo.py
==================================
Sovereign Sync Bridge: 9Router SQLite -> Odoo 20 GPU Fleet Manager
- Reads 9Router usage analytics from SQLite (~/.9router/db/data.sqlite)
- Aggregates daily telemetry by provider & date into `gpu.usage.daily`
- Synchronizes individual execution logs from `usageHistory` into `gpu.task.log`
- Ensures multi-provider hierarchy in `gpu.provider` (B.AI, Codex, OpenRouter, Modal, Thapsang)
- Enforces database idempotency with PostgreSQL ON CONFLICT handling
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [9Router-Odoo-Bridge] %(message)s"
)
logger = logging.getLogger("bridge_9router_to_odoo")

def _resolve_odoo_db_pass() -> str:
    env_pw = os.environ.get("ODOO_DB_PASS")
    if env_pw:
        return env_pw
    try:
        import importlib.util
        from pathlib import Path
        vpath = Path(__file__).resolve().parents[1] / "skills" / "security" / "account-vault" / "scripts" / "vault.py"
        spec = importlib.util.spec_from_file_location("vault", vpath)
        if spec and spec.loader:
            vmod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vmod)
            entry = vmod.AccountVault().get("odoo20_db")
            if entry and entry.get("password"):
                return entry["password"]
    except Exception:
        pass
    return ""


SQLITE_PATH = os.path.expanduser("~/.9router/db/data.sqlite")
DB_HOST = os.environ.get("ODOO_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("ODOO_DB_PORT", "5434"))
DB_NAME = os.environ.get("ODOO_DB_NAME", "odoo20_dev")
DB_USER = os.environ.get("ODOO_DB_USER", "odoo")
DB_PASS = _resolve_odoo_db_pass()

PROVIDER_DEFINITIONS = {
    "codex": {
        "name": "OpenAI Codex Gateway",
        "code": "codex",
        "provider_type": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "api_prefix": "cx",
        "priority": 5,
        "description": "OpenAI / Codex OAuth and Direct Token Connection Cluster",
    },
    "bai": {
        "name": "B.AI Multi-Key Engine",
        "code": "bai",
        "provider_type": "openai_compatible",
        "base_url": "https://api.b.ai/v1",
        "api_prefix": "bai",
        "priority": 2,
        "description": "B.AI 16-Key High-Concurrency Fallback Engine",
    },
    "openrouter": {
        "name": "OpenRouter Gateway",
        "code": "openrouter",
        "provider_type": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_prefix": "openrouter",
        "priority": 8,
        "description": "OpenRouter Multi-Model Unified Routing Hub",
    },
    "modal": {
        "name": "Modal Sovereign Fleet",
        "code": "modal",
        "provider_type": "modal",
        "base_url": "http://localhost:8099",
        "api_prefix": "modal",
        "priority": 1,
        "description": "Modal 20-Workspace Compute Fleet",
    },
    "thapsang": {
        "name": "Thapsang Sovereign AI Engine",
        "code": "thapsang",
        "provider_type": "custom",
        "base_url": "http://localhost:8099/v1",
        "api_prefix": "thapsang",
        "priority": 0,
        "description": "Local ThinkPad P15 RTX 5000 & Sovereign Hub",
    },
}


def connect_sqlite(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"9Router SQLite database not found at {path}")
    uri = f"file:{os.path.abspath(path)}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def connect_pg():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def ensure_providers(pg_cur):
    """Ensure all 9Router providers exist in gpu_provider."""
    provider_map = {}
    now = datetime.now(timezone.utc)

    for code, info in PROVIDER_DEFINITIONS.items():
        pg_cur.execute("SELECT id FROM gpu_provider WHERE code = %s", (code,))
        row = pg_cur.fetchone()
        if row:
            provider_map[code] = row[0]
        else:
            pg_cur.execute("""
                INSERT INTO gpu_provider (name, code, provider_type, base_url, api_prefix, priority, status, description, create_date, write_date, create_uid, write_uid)
                VALUES (%s, %s, %s, %s, %s, %s, 'active', %s, %s, %s, 1, 1)
                RETURNING id
            """, (info["name"], info["code"], info["provider_type"], info["base_url"], info["api_prefix"], info["priority"], info["description"], now, now))
            provider_map[code] = pg_cur.fetchone()[0]
            logger.info("Created missing gpu_provider: %s (code: %s, ID: %d)", info["name"], code, provider_map[code])

    # Default fallback provider
    pg_cur.execute("SELECT id FROM gpu_provider ORDER BY priority asc LIMIT 1")
    default_id = pg_cur.fetchone()[0]
    provider_map["_default"] = default_id
    return provider_map


def get_default_workspace(pg_cur):
    """Retrieve primary default workspace for unassigned requests."""
    pg_cur.execute("SELECT id FROM gpu_workspace ORDER BY priority asc, headroom_score desc LIMIT 1")
    row = pg_cur.fetchone()
    if row:
        return row[0]
    pg_cur.execute("SELECT id FROM gpu_workspace LIMIT 1")
    row = pg_cur.fetchone()
    return row[0] if row else None


def sync_daily_usage(sqlite_cur, pg_cur, provider_map, default_workspace_id):
    """Sync 9Router usageDaily table into gpu_usage_daily."""
    sqlite_cur.execute("SELECT dateKey, data FROM usageDaily ORDER BY dateKey ASC")
    rows = sqlite_cur.fetchall()
    synced_count = 0
    now = datetime.now(timezone.utc)

    for date_key, data_raw in rows:
        try:
            data = json.loads(data_raw) if data_raw else {}
        except Exception:
            continue

        by_provider = data.get("byProvider", {})
        if not by_provider:
            # Single aggregate entry
            prov_code = "_default"
            prov_id = provider_map.get(prov_code)
            reqs = int(data.get("requests", 0))
            cost = float(data.get("cost", 0.0))
            p_tokens = int(data.get("promptTokens", 0))
            c_tokens = int(data.get("completionTokens", 0))
            comp_hours = round((p_tokens + c_tokens) / 1000000.0 * 0.08, 4)

            upsert_daily_record(
                pg_cur, date_key, default_workspace_id, prov_id,
                reqs, cost, comp_hours, json.dumps(data), now
            )
            synced_count += 1
        else:
            for prov_name, p_data in by_provider.items():
                prov_code = prov_name.lower().strip()
                prov_id = provider_map.get(prov_code, provider_map["_default"])
                reqs = int(p_data.get("requests", 0))
                cost = float(p_data.get("cost", 0.0))
                p_tokens = int(p_data.get("promptTokens", 0))
                c_tokens = int(p_data.get("completionTokens", 0))
                comp_hours = round((p_tokens + c_tokens) / 1000000.0 * 0.08, 4)

                upsert_daily_record(
                    pg_cur, date_key, default_workspace_id, prov_id,
                    reqs, cost, comp_hours, json.dumps(p_data), now
                )
                synced_count += 1

    logger.info("Synchronized %d daily usage records into gpu_usage_daily.", synced_count)
    return synced_count


def upsert_daily_record(pg_cur, date_str, ws_id, prov_id, reqs, cost, comp_hours, breakdown_json, now):
    name = f"Daily Usage {date_str}"
    pg_cur.execute("""
        INSERT INTO gpu_usage_daily (
            name, date, workspace_id, provider_id, total_requests, successful_requests, failed_requests,
            cost, compute_hours, avg_latency_ms, cache_hit_rate, service_breakdown,
            create_date, write_date, create_uid, write_uid
        )
        VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s, 120.0, 0.0, %s, %s, %s, 1, 1)
        ON CONFLICT (date, workspace_id, provider_id)
        DO UPDATE SET
            total_requests = EXCLUDED.total_requests,
            successful_requests = EXCLUDED.successful_requests,
            cost = EXCLUDED.cost,
            compute_hours = EXCLUDED.compute_hours,
            service_breakdown = EXCLUDED.service_breakdown,
            write_date = EXCLUDED.write_date
    """, (name, date_str, ws_id, prov_id, reqs, reqs, cost, comp_hours, breakdown_json, now, now))


def sync_task_logs(sqlite_cur, pg_cur, default_workspace_id, limit=1000):
    """Sync recent execution logs from usageHistory into gpu_task_log."""
    sqlite_cur.execute("""
        SELECT id, timestamp, provider, model, endpoint, cost, status, promptTokens, completionTokens
        FROM usageHistory
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = sqlite_cur.fetchall()
    inserted_count = 0
    now = datetime.now(timezone.utc)

    for r in rows:
        row_id, ts_str, provider, model, endpoint, cost, status, p_tokens, c_tokens = r
        request_id = f"9r-{row_id}"
        model_name = f"{provider}/{model}" if provider and model else (model or "unknown")
        task_name = f"{request_id} ({model_name})"
        exec_status = "completed" if str(status).lower() in ("ok", "success", "200") else "failed"
        cost_val = float(cost or 0.0)

        # Parse timestamp
        try:
            # Handles ISO format: 2026-09-29T01:03:42.160Z
            clean_ts = ts_str.replace("Z", "+00:00")
            exec_dt = datetime.fromisoformat(clean_ts)
        except Exception:
            exec_dt = now

        duration_est = round(((p_tokens or 0) + (c_tokens or 0)) / 1000.0 * 0.25, 3)
        if duration_est <= 0:
            duration_est = 0.500

        pg_cur.execute("""
            INSERT INTO gpu_task_log (
                name, request_id, endpoint, model_template, status,
                micro_cost, duration_seconds, execution_timestamp,
                workspace_id, create_date, write_date, create_uid, write_uid
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1)
            ON CONFLICT (request_id) DO NOTHING
        """, (
            task_name, request_id, endpoint or "/v1/chat/completions",
            model_name, exec_status, cost_val, duration_est, exec_dt,
            default_workspace_id, now, now
        ))
        if pg_cur.rowcount > 0:
            inserted_count += 1

    logger.info("Synchronized %d new task logs into gpu_task_log (scanned last %d records).", inserted_count, limit)
    return inserted_count


def run_bridge_sync(limit_history=1000):
    logger.info("Initiating 9Router to Odoo 20 Usage Sync Bridge...")
    sq_conn = connect_sqlite(SQLITE_PATH)
    pg_conn = connect_pg()

    try:
        sq_cur = sq_conn.cursor()
        pg_cur = pg_conn.cursor()

        # 1. Ensure providers
        provider_map = ensure_providers(pg_cur)

        # 2. Get default workspace
        default_ws_id = get_default_workspace(pg_cur)
        if not default_ws_id:
            logger.error("No gpu.workspace found in Odoo! Please run fleet server sync first.")
            return {"success": False, "error": "No workspaces found in Odoo"}

        # 3. Sync Daily Usage
        daily_count = sync_daily_usage(sq_cur, pg_cur, provider_map, default_ws_id)

        # 4. Sync Task Logs
        tasks_count = sync_task_logs(sq_cur, pg_cur, default_ws_id, limit=limit_history)

        pg_conn.commit()

        # 5. Fetch Summary
        pg_cur.execute("SELECT count(*), coalesce(sum(cost), 0) FROM gpu_usage_daily")
        total_days, total_cost = pg_cur.fetchone()

        pg_cur.execute("SELECT count(*) FROM gpu_task_log WHERE request_id LIKE '9r-%'")
        total_9r_tasks = pg_cur.fetchone()[0]

        summary = {
            "success": True,
            "daily_records_synced": daily_count,
            "new_task_logs_inserted": tasks_count,
            "total_daily_records_in_odoo": total_days,
            "total_historical_spend_usd": round(float(total_cost), 4),
            "total_9router_tasks_in_odoo": total_9r_tasks,
        }
        logger.info("Sync Bridge complete: %s", json.dumps(summary))
        return summary

    except Exception as e:
        pg_conn.rollback()
        logger.exception("Sync Bridge failed with error: %s", e)
        return {"success": False, "error": str(e)}
    finally:
        sq_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="9Router SQLite to Odoo 20 Usage Sync Bridge")
    parser.add_argument("--limit-history", type=int, default=1000, help="Number of recent usageHistory rows to sync")
    args = parser.parse_args()

    result = run_bridge_sync(limit_history=args.limit_history)
    print(json.dumps(result, indent=2))
    if not result.get("success"):
        sys.exit(1)
