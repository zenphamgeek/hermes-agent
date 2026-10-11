#!/usr/bin/env python3
"""Poll a value source and gate a cron agent on a threshold condition.

Prints a single JSON line; the cron scheduler wakes the agent only when
``wakeAgent`` is true:

    {"wakeAgent": true, "value": 12.3, "previous": 14.1, "message": "..."}

Usage:
  poll_threshold.py <name> \\
      [--url URL --field a.b.c | --command "shell cmd" | --file path] \\
      [--lt N | --gt N | --drop-pct N | --rise-pct N]

Sources (pick one):
  --url URL       GET a JSON endpoint, read ``--field`` (dotted path).
  --command CMD   Run a shell command; parse the last stdout line as float.
  --file PATH     Read a file whose content is a number.

Conditions (pick one):
  --lt N / --gt N   Compare the current value against a fixed threshold.
  --drop-pct N      Fire when value fell N% vs the previous poll.
  --rise-pct N      Fire when value rose N% vs the previous poll.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

STATE_DIR = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "cron" / "data-triggers"


def _get_json_field(obj, field: str):
    """Resolve dotted field path like ``data.price.usd``."""
    parts = field.split(".")
    for p in parts:
        if isinstance(obj, dict):
            obj = obj.get(p)
        else:
            return None
    return obj


def _read_url(url: str, field: str | None) -> tuple[bool, float | str]:
    try:
        resp = urllib.request.urlopen(url, timeout=30)
        data = json.loads(resp.read().decode())
        if field:
            val = _get_json_field(data, field)
        else:
            val = data
        if val is None:
            return False, f"Field {field!r} not found in response"
        return True, float(val)
    except (urllib.error.URLError, ValueError, TypeError, KeyError) as e:
        return False, str(e)


def _read_command(cmd: str) -> tuple[bool, float | str]:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False, f"Command exited {result.returncode}: {result.stderr.strip()}"
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        if not lines:
            return False, "Command produced no output"
        return True, float(lines[-1])
    except (subprocess.TimeoutExpired, ValueError) as e:
        return False, str(e)


def _read_file(path: str) -> tuple[bool, float | str]:
    try:
        raw = Path(path).read_text().strip()
        return True, float(raw)
    except (OSError, ValueError) as e:
        return False, str(e)


def _load_state(name: str) -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = STATE_DIR / f"{name}.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(name: str, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / f"{name}.json").write_text(json.dumps(state))


def _check_condition(current: float, previous: float | None, args) -> tuple[bool, str]:
    if args.gt is not None:
        return current > args.gt, f"current={current} > {args.gt}"
    if args.lt is not None:
        return current < args.lt, f"current={current} < {args.lt}"
    if args.drop_pct is not None and previous is not None and previous != 0:
        pct = (previous - current) / previous * 100
        return pct > args.drop_pct, f"dropped {pct:.1f}% (threshold {args.drop_pct}%)"
    if args.rise_pct is not None and previous is not None and previous != 0:
        pct = (current - previous) / previous * 100
        return pct > args.rise_pct, f"rose {pct:.1f}% (threshold {args.rise_pct}%)"
    # First poll in relative modes — no previous, no fire.
    return False, f"first poll (seeding baseline at {current})"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Poll a value and gate a cron agent on a threshold condition.",
        epilog="Exactly one source and one condition flag are required.",
    )
    ap.add_argument("name", help="Trigger name (used for state file)")
    ap.add_argument("--url", help="HTTP(S) URL to fetch")
    ap.add_argument("--field", help="Dotted JSON path (e.g. data.price)")
    ap.add_argument("--command", help="Shell command to run")
    ap.add_argument("--file", help="Path to a file with a numeric value")
    ap.add_argument("--lt", type=float, help="Fire when value < N")
    ap.add_argument("--gt", type=float, help="Fire when value > N")
    ap.add_argument("--drop-pct", type=float, help="Fire when value dropped N%% vs previous")
    ap.add_argument("--rise-pct", type=float, help="Fire when value rose N%% vs previous")
    args = ap.parse_args()

    # Resolve source
    sources = [bool(args.url), bool(args.command), bool(args.file)]
    if sum(sources) != 1:
        print(json.dumps({"wakeAgent": False, "error": "Exactly one of --url, --command, --file required"}))
        return 1
    conditions = [args.lt is not None, args.gt is not None, args.drop_pct is not None, args.rise_pct is not None]
    if sum(conditions) != 1:
        print(json.dumps({"wakeAgent": False, "error": "Exactly one of --lt, --gt, --drop-pct, --rise-pct required"}))
        return 1

    if args.url:
        ok, value = _read_url(args.url, args.field)
    elif args.command:
        ok, value = _read_command(args.command)
    else:
        ok, value = _read_file(args.file)

    if not ok:
        print(json.dumps({"wakeAgent": False, "error": str(value)}))
        return 1  # visible failure for a broken source

    state = _load_state(args.name)
    previous = state.get("previous")
    fire, reason = _check_condition(value, previous, args)

    # Always persist the latest value so the next poll has a baseline.
    state["previous"] = value
    _save_state(args.name, state)

    msg = {
        "wakeAgent": fire,
        "value": value,
        "previous": previous,
        "message": reason,
    }
    print(json.dumps(msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())