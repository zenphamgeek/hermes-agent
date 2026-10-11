#!/usr/bin/env python3
"""
Stock Watchlist Manager for Vietnam Stock Daily Briefing
Manages persistent watchlist of stock tickers to track for morning briefings.
"""

import os
import sys
import json
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_HERMES_ENV = Path("/home/zen/.hermes/.env")
USER_WATCHLIST_PATH = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes")) / "stock_watchlist.json"
FALLBACK_WATCHLIST_PATH = SKILL_DIR / "watchlist.json"

DEFAULT_INITIAL_SYMBOLS = ["FPT", "HPG", "SSI", "MWG", "TCB"]


def load_hermes_env() -> Dict[str, str]:
    """Load API credentials from ~/.hermes/.env."""
    env_vars = {}
    if DEFAULT_HERMES_ENV.exists():
        with open(DEFAULT_HERMES_ENV, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


def get_watchlist_file_path() -> Path:
    """Get active watchlist JSON file path."""
    if USER_WATCHLIST_PATH.parent.exists():
        return USER_WATCHLIST_PATH
    return FALLBACK_WATCHLIST_PATH


def load_watchlist_data() -> Dict[str, Any]:
    """Load raw watchlist data dict from disk."""
    p = get_watchlist_file_path()
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "symbols" in data:
                    return data
                elif isinstance(data, list):
                    return {
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "symbols": [s.upper().replace(".VN", "") for s in data if isinstance(s, str)],
                        "notes": {}
                    }
        except Exception as e:
            print(f"[*] Warning reading watchlist file {p}: {e}", file=sys.stderr)

    # Return default initial state
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "symbols": list(DEFAULT_INITIAL_SYMBOLS),
        "notes": {
            "FPT": "Đầu ngành công nghệ, tăng trưởng AI & Cloud",
            "HPG": "Đầu ngành thép, dự án Dung Quất 2",
            "SSI": "Đầu ngành chứng khoán, thanh khoản & nâng hạng",
            "MWG": "Bán lẻ phục hồi, Bách Hóa Xanh có lãi",
            "TCB": "Ngân hàng tư nhân top đầu, Casa cao"
        }
    }


def save_watchlist_data(data: Dict[str, Any]) -> bool:
    """Save watchlist data dict to disk."""
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    p = get_watchlist_file_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[!] Error saving watchlist to {p}: {e}", file=sys.stderr)
        return False


def get_watchlist() -> List[str]:
    """Get list of active stock ticker symbols."""
    data = load_watchlist_data()
    return data.get("symbols", list(DEFAULT_INITIAL_SYMBOLS))


def sanitize_symbol(sym: str) -> str:
    """Clean and normalize stock symbol (e.g. 'fpt.vn' -> 'FPT', '+HPG' -> 'HPG')."""
    s = sym.strip().upper()
    s = s.lstrip("+:-#/")
    s = s.replace(".VN", "").replace(".HO", "").replace(".HA", "")
    return s.strip()


def add_symbols(symbols: List[str], note: Optional[str] = None) -> Dict[str, Any]:
    """Add one or more symbols to the watchlist."""
    data = load_watchlist_data()
    current_symbols = data.get("symbols", [])
    notes = data.get("notes", {})

    added = []
    already_exists = []

    for raw in symbols:
        # Support comma or space separated input
        parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
        for p in parts:
            clean = sanitize_symbol(p)
            if clean and len(clean) >= 3:
                if clean not in current_symbols:
                    current_symbols.append(clean)
                    added.append(clean)
                    if note:
                        notes[clean] = note
                else:
                    already_exists.append(clean)

    data["symbols"] = current_symbols
    data["notes"] = notes
    save_watchlist_data(data)

    return {
        "status": "success",
        "added": added,
        "already_exists": already_exists,
        "total_symbols": current_symbols,
        "count": len(current_symbols)
    }


def remove_symbols(symbols: List[str]) -> Dict[str, Any]:
    """Remove one or more symbols from the watchlist."""
    data = load_watchlist_data()
    current_symbols = data.get("symbols", [])
    notes = data.get("notes", {})

    removed = []
    not_found = []

    for raw in symbols:
        parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
        for p in parts:
            clean = sanitize_symbol(p)
            if clean in current_symbols:
                current_symbols.remove(clean)
                removed.append(clean)
                if clean in notes:
                    del notes[clean]
            else:
                not_found.append(clean)

    data["symbols"] = current_symbols
    data["notes"] = notes
    save_watchlist_data(data)

    return {
        "status": "success",
        "removed": removed,
        "not_found": not_found,
        "total_symbols": current_symbols,
        "count": len(current_symbols)
    }


def clear_watchlist() -> Dict[str, Any]:
    """Clear all symbols from watchlist."""
    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "symbols": [],
        "notes": {}
    }
    save_watchlist_data(data)
    return {"status": "success", "count": 0, "total_symbols": []}


def format_watchlist_telegram_message(action_result: Optional[Dict[str, Any]] = None) -> str:
    """Format watchlist into a sleek, readable Telegram HTML message."""
    data = load_watchlist_data()
    symbols = data.get("symbols", [])
    notes = data.get("notes", {})
    
    header_extra = ""
    if action_result:
        if action_result.get("added"):
            added_str = ", ".join(f"<b>{s}</b>" for s in action_result["added"])
            header_extra = f"✅ <b>Đã thêm thành công:</b> {added_str}\n\n"
        elif action_result.get("removed"):
            rem_str = ", ".join(f"<b>{s}</b>" for s in action_result["removed"])
            header_extra = f"🗑️ <b>Đã xóa khỏi danh mục:</b> {rem_str}\n\n"

    items_list = []
    if symbols:
        for idx, sym in enumerate(symbols, 1):
            n = notes.get(sym, "")
            note_part = f" — <i>{n}</i>" if n else ""
            items_list.append(f"{idx}. 📌 <b>{sym}</b>{note_part}")
        body = "\n".join(items_list)
    else:
        body = "<i>(Hiện chưa có mã cổ phiếu nào trong danh mục theo dõi)</i>"

    msg = (
        f"{header_extra}"
        f"📋 <b>DANH MỤC CỔ PHIẾU NHẬN INSIGHT MỖI SÁNG (08:00 AM)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Tổng số mã đang theo dõi:</b> {len(symbols)}\n\n"
        f"{body}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>Lệnh thao tác nhanh:</b>\n"
        f"• Thêm mã: <code>/stock_add FPT SSI HPG</code>\n"
        f"• Xóa mã: <code>/stock_remove VNM</code>\n"
        f"• Xem danh mục: <code>/stock_list</code>\n"
        f"• Lấy insight ngay: <code>/vietnam_stock_daily_brief</code>"
    )
    return msg


def send_telegram_notification(text: str) -> bool:
    """Dispatch Telegram notification to user chat."""
    env = load_hermes_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception as e:
        print(f"[!] Failed to send Telegram notification: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Manage Vietnam Stock Watchlist for Daily Briefings.")
    subparsers = parser.add_subparsers(dest="command", help="Watchlist action commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add stock symbols to watchlist")
    add_parser.add_argument("symbols", nargs="+", help="Stock ticker symbols (e.g. FPT HPG SSI)")
    add_parser.add_argument("--note", help="Optional note or thesis for the stock")
    add_parser.add_argument("--notify", action="store_true", help="Send confirmation message to Telegram")

    # Remove command
    rem_parser = subparsers.add_parser("remove", help="Remove stock symbols from watchlist")
    rem_parser.add_argument("symbols", nargs="+", help="Stock ticker symbols to remove")
    rem_parser.add_argument("--notify", action="store_true", help="Send confirmation message to Telegram")

    # List command
    list_parser = subparsers.add_parser("list", help="List all tracked stock symbols")
    list_parser.add_argument("--notify", action="store_true", help="Send list to Telegram")

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear all stock symbols")
    clear_parser.add_argument("--notify", action="store_true", help="Send notification to Telegram")

    args = parser.parse_args()

    if args.command == "add":
        res = add_symbols(args.symbols, note=args.note)
        print(f"[✓] Added: {res['added']} | Total Watchlist ({res['count']}): {res['total_symbols']}")
        msg = format_watchlist_telegram_message(action_result=res)
        print("\n" + msg)
        if args.notify:
            send_telegram_notification(msg)

    elif args.command == "remove":
        res = remove_symbols(args.symbols)
        print(f"[✓] Removed: {res['removed']} | Total Watchlist ({res['count']}): {res['total_symbols']}")
        msg = format_watchlist_telegram_message(action_result=res)
        print("\n" + msg)
        if args.notify:
            send_telegram_notification(msg)

    elif args.command == "list" or not args.command:
        symbols = get_watchlist()
        print(f"[*] Active Watchlist ({len(symbols)}): {symbols}")
        msg = format_watchlist_telegram_message()
        print("\n" + msg)
        if getattr(args, "notify", False):
            send_telegram_notification(msg)

    elif args.command == "clear":
        res = clear_watchlist()
        print("[✓] Watchlist cleared.")
        msg = format_watchlist_telegram_message(action_result={"removed": ["ALL"]})
        print("\n" + msg)
        if args.notify:
            send_telegram_notification(msg)


if __name__ == "__main__":
    main()
