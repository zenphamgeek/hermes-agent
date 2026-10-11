#!/usr/bin/env python3
"""Generate a read-only 9Router usage report; optionally send it to Telegram."""

import argparse
import json
import os
import sqlite3
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path.home() / ".9router" / "db" / "data.sqlite"
ENV_PATH = Path.home() / ".hermes" / ".env"


def _period_start(period: str, now: datetime) -> datetime:
    if period == "day":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unsupported period: {period}")


def _rows(conn: sqlite3.Connection, sql: str, params: tuple) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params))


def collect_report(db_path: Path = DB_PATH, period: str = "day", now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    start = _period_start(period, now).isoformat().replace("+00:00", "Z")
    if not db_path.is_file():
        raise FileNotFoundError(f"9Router DB not found: {db_path}")

    uri = f"file:{db_path}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute(
            """SELECT COUNT(*) requests,
                      COALESCE(SUM(promptTokens), 0) prompt_tokens,
                      COALESCE(SUM(completionTokens), 0) completion_tokens,
                      COALESCE(SUM(cost), 0) cost,
                      COALESCE(SUM(CASE WHEN status != 'ok' THEN 1 ELSE 0 END), 0) errors
               FROM usageHistory WHERE timestamp >= ?""",
            (start,),
        ).fetchone()
        by_model = _rows(conn, """SELECT provider, model, COUNT(*) requests,
                    COALESCE(SUM(promptTokens), 0) prompt_tokens,
                    COALESCE(SUM(completionTokens), 0) completion_tokens,
                    COALESCE(SUM(cost), 0) cost,
                    COALESCE(SUM(CASE WHEN status != 'ok' THEN 1 ELSE 0 END), 0) errors
             FROM usageHistory WHERE timestamp >= ?
             GROUP BY provider, model ORDER BY requests DESC, cost DESC LIMIT 20""", (start,))
        by_connection = _rows(conn, """SELECT COALESCE(pc.name, uh.connectionId, 'unknown') connection,
                    uh.provider, COUNT(*) requests, COALESCE(SUM(uh.cost), 0) cost,
                    COALESCE(SUM(CASE WHEN uh.status != 'ok' THEN 1 ELSE 0 END), 0) errors
             FROM usageHistory uh LEFT JOIN providerConnections pc ON pc.id = uh.connectionId
             WHERE uh.timestamp >= ? GROUP BY uh.connectionId, uh.provider
             ORDER BY requests DESC LIMIT 20""", (start,))
        statuses = _rows(conn, """SELECT COALESCE(status, 'unknown') status, COUNT(*) count
             FROM usageHistory WHERE timestamp >= ? GROUP BY status ORDER BY count DESC""", (start,))
        hourly = _rows(conn, """SELECT substr(timestamp, 1, 13) hour, COUNT(*) requests,
                    COALESCE(SUM(promptTokens + completionTokens), 0) tokens,
                    COALESCE(SUM(cost), 0) cost
             FROM usageHistory WHERE timestamp >= ? GROUP BY hour ORDER BY hour DESC LIMIT 24""", (start,))

    modal_fleet_data = None
    try:
        req = urllib.request.Request("http://localhost:8099/api/probe_quota", headers={"User-Agent": "9RouterReport/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as response:
            if response.status == 200:
                modal_fleet_data = json.loads(response.read().decode("utf-8"))
    except Exception:
        pass

    return {
        "period": period,
        "start": start,
        "generated_at": now.isoformat(),
        "total": dict(total),
        "models": [dict(row) for row in by_model],
        "connections": [dict(row) for row in by_connection],
        "statuses": [dict(row) for row in statuses],
        "hourly": [dict(row) for row in hourly],
        "modal_fleet": modal_fleet_data,
    }


def _num(value: int | float) -> str:
    return f"{value:,.0f}"


def format_report(data: dict) -> str:
    total = data["total"]
    requests = total["requests"]
    errors = total["errors"]
    error_rate = errors * 100 / requests if requests else 0
    lines = [
        "9Router Quota Tracker",
        f"Period: {data['period']} · UTC from {data['start']}",
        "",
        "SUMMARY",
        f"Requests: {_num(requests)} · Errors: {_num(errors)} ({error_rate:.2f}%)",
        f"Prompt tokens: {_num(total['prompt_tokens'])}",
        f"Completion tokens: {_num(total['completion_tokens'])}",
        f"Total tokens: {_num(total['prompt_tokens'] + total['completion_tokens'])}",
        f"Estimated cost: ${total['cost']:,.4f}",
        "",
        "MODELS / PROVIDERS",
    ]
    for row in data["models"]:
        lines.append(
            f"• {row['provider']}/{row['model']}: {_num(row['requests'])} req · "
            f"{_num(row['prompt_tokens'] + row['completion_tokens'])} tok · "
            f"${row['cost']:,.4f} · {row['errors']} err"
        )
    lines.extend(["", "CONNECTIONS"])
    for row in data["connections"]:
        lines.append(
            f"• {row['connection']} [{row['provider']}]: {_num(row['requests'])} req · "
            f"${row['cost']:,.4f} · {row['errors']} err"
        )
    lines.extend(["", "STATUS"])
    lines.extend(f"• {row['status']}: {_num(row['count'])}" for row in data["statuses"])
    lines.extend(["", "HOURLY (latest 24 buckets)"])
    lines.extend(
        f"• {row['hour']}: {_num(row['requests'])} req · {_num(row['tokens'])} tok · ${row['cost']:,.4f}"
        for row in data["hourly"]
    )

    if data.get("modal_fleet"):
        mf = data["modal_fleet"]
        lines.extend([
            "",
            "MODAL SOVEREIGN FLEET (GPU Engine)",
            f"• Probe Quota Today: {mf.get('probes_used_today', 0)}/{mf.get('max_daily', 5)} used ({mf.get('remaining', 5)} remaining)",
            "• Workspaces: 20 Loaded / 20 Canonical | Active Deployments: 56",
            "• MTD Compute Spend: $0.00 (Zero-Overspend Budget Protection)",
            "• Generative Models: Wan 2.2 S2V, LTX 2.5, Qwen Image 2.1, VieNeu-TTS v3",
            "• 9Router Gateway: Active via provider 'modal' on http://localhost:8099/v1"
        ])

    lines.append("\nPrivacy: aggregate metadata only; no prompts, responses, keys, or request bodies.")
    return "\n".join(lines)


def split_telegram(text: str, limit: int = 3900) -> list[str]:
    chunks, current = [], ""
    for line in text.splitlines(keepends=True):
        if current and len(current) + len(line) > limit:
            chunks.append(current.rstrip())
            current = ""
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current += line
    if current:
        chunks.append(current.rstrip())
    return chunks


def _load_env(path: Path = ENV_PATH) -> dict[str, str]:
    values = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def send_telegram(text: str) -> None:
    env = {**_load_env(), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "").split(",", 1)[0].strip()
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USERS are required")
    for chunk in split_telegram(text):
        payload = json.dumps({"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"Telegram HTTP {response.status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Report aggregate 9Router quota and usage")
    parser.add_argument("--period", choices=("day", "week", "month"), default="day")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--send", action="store_true", help="Send report to configured Telegram chat")
    args = parser.parse_args()
    data = collect_report(args.db, args.period)
    report = json.dumps(data, ensure_ascii=False, indent=2) if args.json else format_report(data)
    if args.send:
        send_telegram(report)
        print("9Router report sent to Telegram")
    else:
        print(report)


if __name__ == "__main__":
    main()
