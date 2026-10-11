#!/usr/bin/env python3
"""
Daily Stock Market Reporter for Hermes Agent
Gathers data, invokes LLM analysis, and delivers the 08:00 AM briefing to Telegram.
"""

import sys
import time
import json
import html
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

# Ensure local skill directory is in sys.path
SKILL_DIR = Path(__file__).resolve().parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

DEFAULT_HERMES_ENV = Path("/home/zen/.hermes/.env")


def load_hermes_env():
    env_vars = {}
    if DEFAULT_HERMES_ENV.exists():
        with open(DEFAULT_HERMES_ENV, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


def markdown_to_telegram_html(text: str) -> str:
    """Convert standard markdown (bold, lists) to safe Telegram HTML."""
    escaped = html.escape(text)
    # Convert bold **text** to <b>text</b>
    import re
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)
    escaped = re.sub(r'`(.+?)`', r'<code>\1</code>', escaped)
    return escaped


def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Send text message to Telegram chat via Bot API using HTML format."""
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
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                print("[✓] Stock briefing message sent to Telegram successfully.")
                return True
            else:
                print(f"[!] Telegram API error: {data}", file=sys.stderr)
    except Exception as e:
        print(f"[!] Failed to send HTML message to Telegram: {e}", file=sys.stderr)
        # Fallback to plain text if HTML parsing has issues
        try:
            payload["parse_mode"] = ""
            payload["text"] = text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("ok", False)
        except Exception as e2:
            print(f"[!] Plain text fallback failed: {e2}", file=sys.stderr)
    return False


def run_daily_stock_report(dry_run: bool = False, symbols: list = None) -> bool:
    """Execute full data gathering, LLM reasoning, and dispatch report."""
    from market_data import get_consolidated_market_payload
    from analyst import generate_market_analysis
    from watchlist_manager import get_watchlist

    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M")

    print(f"[*] Starting Daily Vietnam Stock Market Briefing for {date_str} {time_str}...")
    
    # 1. Collect live data
    target_symbols = symbols or get_watchlist()
    print(f"[*] Fetching global market quotes, domestic news, and {len(target_symbols)} watchlist stocks: {target_symbols}...")
    market_payload = get_consolidated_market_payload(symbols=target_symbols)
    
    # 2. Run LLM Strategic Analysis
    print("[*] Running financial LLM intermarket analysis, VN-Index forecasting & watchlist insights...")
    analysis_text = generate_market_analysis(market_payload, date_str)

    # 3. Format header & key indicators table
    global_markets = market_payload.get("global_markets", {})
    indicators_list = []
    for name, item in global_markets.items():
        chg = item.get("change_pct", 0)
        icon = "🟢" if chg > 0 else ("🔴" if chg < 0 else "⚪")
        indicators_list.append(f"{icon} <b>{html.escape(name)}</b>: <code>{item.get('price')}</code> ({chg:+.2f}%)")
    indicators_block = "\n".join(indicators_list)

    # 4. Format watchlist quick price table
    watchlist_stocks = market_payload.get("watchlist_stocks", {})
    wl_list = []
    for sym, item in watchlist_stocks.items():
        p = item.get("price", 0)
        chg = item.get("change_pct", 0)
        icon = "🟢" if chg > 0 else ("🔴" if chg < 0 else "⚪")
        p_str = f"{p:,.0f} VND" if p > 0 else "N/A"
        wl_list.append(f"{icon} <b>{sym}</b>: <code>{p_str}</code> ({chg:+.2f}%)")
    wl_block = "\n".join(wl_list) if wl_list else "<i>(Chưa có mã cổ phiếu trong danh mục theo dõi)</i>"

    formatted_analysis = markdown_to_telegram_html(analysis_text)

    final_report = (
        f"📊 <b>BẢN TIN ĐẦU NGÀY CHỨNG KHOÁN & DỰ BÁO VN-INDEX</b>\n"
        f"🗓️ <b>Ngày</b>: {date_str} | ⏰ <b>Giờ phát hành</b>: {time_str} (GMT+7)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 <b>CHỈ SỐ QUỐC TẾ & NGOẠI HỐI:</b>\n"
        f"{indicators_block}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>DANH MỤC CỔ PHIẾU THEO DÕI (WATCHLIST):</b>\n"
        f"{wl_block}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{formatted_analysis}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Gõ /stock_add [MÃ] để thêm mã cần phân tích mỗi sáng.</i>\n"
        f"🤖 <i>Hermes Financial Intelligence • Chúc bạn một ngày giao dịch thành công!</i>"
    )

    if dry_run:
        print("\n" + "="*50)
        print(final_report)
        print("="*50 + "\n")
        return True

    # 5. Dispatch to Telegram
    env = load_hermes_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    print(f"[*] Sending report to Telegram chat {chat_id}...")
    if len(final_report) > 4000:
        parts = [final_report[i:i+3800] for i in range(0, len(final_report), 3800)]
        for p in parts:
            send_telegram_message(token, chat_id, p)
            time.sleep(0.5)
        return True
    else:
        return send_telegram_message(token, chat_id, final_report)


def main():
    parser = argparse.ArgumentParser(description="Vietnam Stock Daily Briefing Reporter.")
    parser.add_argument("--dry-run", action="store_true", help="Print report to console without sending to Telegram")
    parser.add_argument("--stocks", help="Comma-separated stock symbols for one-off report (e.g. FPT,HPG)")
    parser.add_argument("--add", nargs="+", help="Add stock tickers to daily watchlist (e.g. --add FPT HPG)")
    parser.add_argument("--remove", nargs="+", help="Remove stock tickers from daily watchlist")
    parser.add_argument("--list", action="store_true", help="List active stock watchlist")
    args = parser.parse_args()

    from watchlist_manager import add_symbols, remove_symbols, get_watchlist, format_watchlist_telegram_message, send_telegram_notification

    if args.add:
        res = add_symbols(args.add)
        msg = format_watchlist_telegram_message(action_result=res)
        print(msg)
        if not args.dry_run:
            send_telegram_notification(msg)
        return

    if args.remove:
        res = remove_symbols(args.remove)
        msg = format_watchlist_telegram_message(action_result=res)
        print(msg)
        if not args.dry_run:
            send_telegram_notification(msg)
        return

    if args.list:
        msg = format_watchlist_telegram_message()
        print(msg)
        if not args.dry_run:
            send_telegram_notification(msg)
        return

    custom_symbols = [s.strip().upper() for s in args.stocks.split(",")] if args.stocks else None
    run_daily_stock_report(dry_run=args.dry_run, symbols=custom_symbols)


if __name__ == "__main__":
    main()

