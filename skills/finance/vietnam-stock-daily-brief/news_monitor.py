#!/usr/bin/env python3
"""
Hourly Stock News Monitor & Real-Time Financial Intelligence Alert.
Monitors watchlist tickers (CII, HBC, REE, FPT, HPG, etc.), applies intelligent
semantic deduplication to ignore repetitive articles, performs deep dive analysis
on genuinely new events, and alerts via Telegram.
"""

import os
import re
import sys
import ssl
import json
import time
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_DIR))

from watchlist_manager import get_watchlist
from news_memory import StockNewsMemory

HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))
DEFAULT_HERMES_ENV = HERMES_HOME / ".env"


def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_browser_headers() -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }


def load_hermes_env() -> Dict[str, str]:
    env_vars = {}
    if DEFAULT_HERMES_ENV.exists():
        with open(DEFAULT_HERMES_ENV, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


def send_telegram_alert(message_html: str) -> bool:
    """Send immediate Telegram notification."""
    env = load_hermes_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15, context=get_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception as e:
        print(f"[!] Failed to send Telegram news alert: {e}", file=sys.stderr)
        return False


def fetch_news_for_symbol(symbol: str, days: int = 4) -> List[Dict[str, Any]]:
    """Search latest financial news for a specific stock ticker."""
    query = f"{symbol} chứng khoán"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}+when:{days}d&hl=vi&gl=VN&ceid=VN:vi"
    
    headers = get_browser_headers()
    articles = []

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=get_ssl_context()) as resp:
            root = ET.fromstring(resp.read())
            items = root.findall(".//item")
            for it in items[:12]:
                title_elem = it.find("title")
                link_elem = it.find("link")
                pub_elem = it.find("pubDate")
                src_elem = it.find("source")
                desc_elem = it.find("description")

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                source = src_elem.text.strip() if src_elem is not None and src_elem.text else "Báo chí tài chính"
                desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

                # Strip HTML tags from description
                desc_clean = re.sub(r'<[^>]+>', ' ', desc).strip()

                if title and link:
                    articles.append({
                        "symbol": symbol.upper(),
                        "title": title,
                        "url": link,
                        "source": source,
                        "published_at": pub,
                        "summary": desc_clean[:250]
                    })
    except Exception as e:
        print(f"[!] Error fetching news for {symbol}: {e}", file=sys.stderr)

    return articles


def call_llm_news_analysis(symbol: str, title: str, summary: str, source: str) -> Dict[str, Any]:
    """
    Call LM Studio at 10.123.214.1:1234 (with fallback) to produce deep financial impact analysis.
    """
    prompt = f"""Bạn là Chuyên gia Cao cấp Phân tích Đầu tư Chứng khoán Việt Nam (CFA Charterholder).
Hãy phân tích chuyên sâu tác động của tin tức mới nhất về mã cổ phiếu {symbol}:

[THÔNG TIN SỰ KIỆN]
- Mã cổ phiếu: {symbol}
- Tiêu đề: {title}
- Nguồn: {source}
- Tóm tắt: {summary}

Yêu cầu phân tích ngắn gọn, súc tích, thực chiến theo cấu trúc:
1. Bản chất sự kiện: Cốt lõi tin tức là gì?
2. Tác động Cơ bản & Tài chính: Tích cực / Tiêu cực / Trung tính đến doanh thu, lợi nhuận, chi phí nợ vay, tiến độ dự án?
3. Tác động Kỹ thuật & Tâm lý Dòng tiền: Phản ứng giá T+ ngắn hạn và xu hướng trung hạn?
4. Khuyến nghị Hành động: Vị thế khuyến nghị (Mua gom / Nắm giữ / Chốt lời từng phần / Quan sát quản trị rủi ro)?

Trả về định dạng HTML ngắn gọn để gửi Telegram (dùng <b>, <i>, <code>). Không dùng markdown # hoặc **."""

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": "Bạn là Chuyên gia Phân tích Chứng khoán Việt Nam sắc bén, súc tích và thực chiến."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 800
    }

    try:
        req = urllib.request.Request(
            "http://10.123.214.1:1234/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12, context=get_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            
            # Determine sentiment
            content_lower = content.lower()
            if any(k in content_lower for k in ["tích cực", "mua gom", "bứt phá", "tăng trưởng", "bullish"]):
                sentiment = "TÍCH CỰC (BULLISH)"
            elif any(k in content_lower for k in ["tiêu cực", "rủi ro", "thận trọng", "bán", "bearish"]):
                sentiment = "TIÊU CỰC (BEARISH)"
            else:
                sentiment = "TRUNG TÍNH (NEUTRAL)"

            return {
                "analysis_text": content,
                "sentiment": sentiment
            }
    except Exception as e:
        print(f"[*] LLM offline or timeout ({e}), using rule-based financial analysis engine.")

    # Rule-based fallback analysis
    title_lower = title.lower()
    if any(k in title_lower for k in ["trúng thầu", "lãi", "tăng trưởng", "mua lại", "cổ tức", "được duyệt", "hợp đồng"]):
        sentiment = "TÍCH CỰC (BULLISH)"
        eval_text = "Tin tức hỗ trợ tâm lý tích cực, củng cố triển vọng doanh thu và dòng tiền kỳ tới."
        action = "Ưu tiên nắm giữ hoặc canh gia tăng tỷ trọng khi có nhịp điều chỉnh lành mạnh."
    elif any(k in title_lower for k in ["hoãn xuất cảnh", "lỗ", "khởi tố", "thanh tra", "bán giải chấp", "phạt", "giảm sâu"]):
        sentiment = "TIÊU CỰC (BEARISH)"
        eval_text = "Rủi ro pháp lý/tài chính ngắn hạn tăng cao, áp lực bán có thể gia tăng."
        action = "Hạ tỷ trọng margin, canh nhịp hồi kỹ thuật để cơ cấu bảo toàn vốn."
    else:
        sentiment = "TRUNG TÍNH (NEUTRAL)"
        eval_text = "Sự kiện nằm trong lộ trình kế hoạch hoạt động của doanh nghiệp, thị trường đã chiết khấu một phần."
        action = "Tiếp tục theo dõi phản ứng cung cầu tại các vùng hỗ trợ/kháng cự then chốt."

    fallback_analysis = (
        f"<b>1. Bản chất sự kiện:</b> {title}\n"
        f"<b>2. Đánh giá Tác động:</b> {eval_text}\n"
        f"<b>3. Tâm lý Dòng tiền:</b> Kỳ vọng phân hóa, dòng tiền thông minh sẽ kiểm định thanh khoản.\n"
        f"<b>4. Khuyến nghị:</b> {action}"
    )

    return {
        "analysis_text": fallback_analysis,
        "sentiment": sentiment
    }


def format_news_telegram_alert(symbol: str, title: str, source: str, published_at: str, analysis: Dict[str, Any], all_sources: List[str]) -> str:
    """Format deep dive financial news analysis for Telegram HTML."""
    sentiment = analysis.get("sentiment", "TRUNG TÍNH")
    if "TÍCH CỰC" in sentiment:
        sent_icon = "🟢 <b>ĐÁNH GIÁ: TÍCH CỰC (BULLISH)</b>"
    elif "TIÊU CỰC" in sentiment:
        sent_icon = "🔴 <b>ĐÁNH GIÁ: TIÊU CỰC (BEARISH)</b>"
    else:
        sent_icon = "🟡 <b>ĐÁNH GIÁ: TRUNG TÍNH (NEUTRAL)</b>"

    src_text = ", ".join(all_sources) if all_sources else source

    return (
        f"🚨 <b>CẬP NHẬT TIN MỚI DOANH NGHIỆP: {symbol}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📰 <b>Tiêu đề:</b> {title}\n"
        f"🏛️ <b>Nguồn tin:</b> {src_text} | ⏰ <i>{published_at}</i>\n"
        f"{sent_icon}\n\n"
        f"🔍 <b>PHÂN TÍCH CHUYÊN SÂU TÁC ĐỘNG:</b>\n"
        f"{analysis.get('analysis_text')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Hermes News Intelligence • Đã tự động lọc bỏ tin trùng lặp giữa các báo.</i>"
    )


def scan_watchlist_news(symbols: Optional[List[str]] = None, notify: bool = True) -> Dict[str, Any]:
    """
    Main scan execution: Fetches news, filters duplicates via SQLite memory,
    runs deep analysis on new corporate events, and sends Telegram alerts.
    """
    target_symbols = symbols or get_watchlist()
    memory = StockNewsMemory()
    
    print(f"=== Starting Hourly Stock News Scan for {len(target_symbols)} tickers: {target_symbols} ===")
    
    scanned_count = 0
    new_events_found = 0
    duplicate_articles_count = 0
    alerts_sent = []

    for sym in target_symbols:
        print(f"[*] Scanning news for {sym}...")
        articles = fetch_news_for_symbol(sym)
        scanned_count += len(articles)

        for art in articles:
            is_dup, event_id, is_new_event = memory.check_and_cluster_article(
                symbol=art["symbol"],
                title=art["title"],
                url=art["url"],
                source_name=art["source"],
                published_at=art["published_at"],
                summary=art["summary"]
            )

            if is_dup:
                duplicate_articles_count += 1
                # Already analyzed or duplicate report across newspapers - skip duplicate analysis!
                continue

            if is_new_event:
                new_events_found += 1
                print(f"  [⚡ Genuinely New Event] {sym}: {art['title']}")

                # Perform deep financial LLM analysis
                analysis = call_llm_news_analysis(
                    symbol=sym,
                    title=art["title"],
                    summary=art["summary"],
                    source=art["source"]
                )

                # Format Telegram message
                msg = format_news_telegram_alert(
                    symbol=sym,
                    title=art["title"],
                    source=art["source"],
                    published_at=art["published_at"],
                    analysis=analysis,
                    all_sources=[art["source"]]
                )

                # Send Telegram alert if requested
                sent_ok = False
                if notify:
                    sent_ok = send_telegram_alert(msg)
                    if sent_ok:
                        print(f"  [✓] Sent Telegram alert for {sym}")

                # Record analysis in memory database so duplicate articles won't trigger again
                memory.record_analysis_result(
                    event_id=event_id,
                    analysis_result=analysis["analysis_text"],
                    sentiment=analysis["sentiment"],
                    alert_sent=sent_ok
                )

                alerts_sent.append({
                    "symbol": sym,
                    "title": art["title"],
                    "event_id": event_id,
                    "sentiment": analysis["sentiment"]
                })

                time.sleep(1.0)  # Rate limiting

    stats = memory.get_stats()
    print(f"\n=== Scan Completed: {scanned_count} articles scanned | {new_events_found} new events analyzed | {duplicate_articles_count} duplicates merged ===")
    return {
        "scanned_articles": scanned_count,
        "new_events_analyzed": new_events_found,
        "duplicates_merged": duplicate_articles_count,
        "alerts_sent": alerts_sent,
        "memory_stats": stats
    }


def install_hourly_cron(notify: bool = True) -> Dict[str, Any]:
    """Register hourly stock news scan job (0 * * * *) in Hermes Cron System."""
    cron_file = HERMES_HOME / "cron" / "jobs.json"
    data = {"jobs": [], "updated_at": datetime.now(timezone.utc).isoformat()}
    
    if cron_file.exists():
        try:
            with open(cron_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict) and "jobs" in d and isinstance(d["jobs"], list):
                    data = d
        except Exception as e:
            print(f"[*] Warning reading cron jobs: {e}", file=sys.stderr)

    job_id = "job_stock_news_hourly"
    cmd = f"python3 {Path(__file__).resolve()} --scan"
    if notify:
        cmd += " --notify"

    job_def = {
        "id": job_id,
        "name": "vietnam-stock-news-hourly-monitor",
        "prompt": f"Chạy quét tin tức doanh nghiệp hàng giờ cho các mã cổ phiếu trong Watchlist (CII, HBC, REE, FPT, HPG,...) bằng lệnh: {cmd}. Lọc bỏ tin trùng lặp giữa các báo, phân tích chuyên sâu tác động tài chính/giá cổ phiếu và gửi cảnh báo về Telegram.",
        "skills": ["vietnam-stock-daily-brief", "vietnam-stock-watchlist"],
        "skill": "vietnam-stock-daily-brief",
        "model": None,
        "provider": None,
        "provider_snapshot": "custom",
        "model_snapshot": "cx/gpt-5.6-luna",
        "base_url": None,
        "script": None,
        "no_agent": False,
        "schedule": {
            "kind": "cron",
            "expr": "0 * * * *",
            "display": "0 * * * * (Hourly news monitor)"
        },
        "schedule_display": "0 * * * *",
        "repeat": {
            "times": None,
            "completed": 0
        },
        "enabled": True,
        "state": "scheduled",
        "paused_at": None,
        "paused_reason": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "next_run_at": None,
        "last_run_at": None,
        "last_status": None,
        "last_error": None,
        "deliver": "local",
        "origin": None,
        "command": cmd
    }

    jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]
    jobs_list.append(job_def)
    data["jobs"] = jobs_list
    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    cron_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cron_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "status": "installed",
        "job_id": job_id,
        "schedule": "0 * * * * (Hourly news scan)",
        "command": cmd
    }


def uninstall_hourly_cron() -> Dict[str, Any]:
    """Remove hourly stock news scan job from Hermes Cron System."""
    cron_file = HERMES_HOME / "cron" / "jobs.json"
    if not cron_file.exists():
        return {"status": "not_found"}
    try:
        with open(cron_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        job_id = "job_stock_news_hourly"
        orig_len = len(data.get("jobs", []))
        data["jobs"] = [j for j in data.get("jobs", []) if j.get("id") != job_id]
        if len(data["jobs"]) < orig_len:
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            with open(cron_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return {"status": "uninstalled", "job_id": job_id}
    except Exception as e:
        print(f"[!] Error uninstalling cron: {e}", file=sys.stderr)
    return {"status": "not_found"}


def main():
    parser = argparse.ArgumentParser(description="Hourly Stock News Monitor & Intelligence Alert.")
    parser.add_argument("--scan", action="store_true", help="Execute one news scan cycle across watchlist")
    parser.add_argument("--symbol", help="Target specific stock symbol (e.g. CII, HBC, REE)")
    parser.add_argument("--notify", action="store_true", help="Send Telegram alerts for new events")
    parser.add_argument("--loop", action="store_true", help="Run continuously in hourly loop")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds (default: 3600s)")
    parser.add_argument("--status", action="store_true", help="Show news memory database statistics")
    parser.add_argument("--install-cron", action="store_true", help="Register hourly cron job in Hermes Cron")
    parser.add_argument("--uninstall-cron", action="store_true", help="Remove hourly cron job from Hermes Cron")
    args = parser.parse_args()

    if args.install_cron:
        res = install_hourly_cron(notify=True)
        print(f"[✓] Installed hourly stock news cron job: {res['job_id']} -> {res['schedule']}")
        return

    if args.uninstall_cron:
        res = uninstall_hourly_cron()
        print(f"[✓] Cron job status: {res['status']}")
        return

    if args.status:
        memory = StockNewsMemory()
        st = memory.get_stats()
        print("=== Stock News Memory & Deduplication Status ===")
        print(f"Total Articles Scanned: {st['total_articles_scanned']}")
        print(f"Unique Corporate Events: {st['unique_corporate_events']}")
        print(f"Analyzed Events: {st['analyzed_events']}")
        print(f"Duplicate Articles Filtered/Merged: {st['duplicate_articles_merged']}")
        print(f"Events by Symbol: {st['events_by_symbol']}")
        return

    syms = [args.symbol.upper()] if args.symbol else None

    if args.loop:
        print(f"[*] Starting Hourly Stock News Monitor Daemon (Interval: {args.interval}s)...")
        while True:
            try:
                scan_watchlist_news(symbols=syms, notify=args.notify)
                print(f"[*] Cycle completed. Sleeping for {args.interval}s until next hourly scan...")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n[!] News monitor stopped by user.")
                break
            except Exception as e:
                print(f"[!] Error in scan loop: {e}", file=sys.stderr)
                time.sleep(args.interval)
    else:
        scan_watchlist_news(symbols=syms, notify=args.notify)


if __name__ == "__main__":
    main()

