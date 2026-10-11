#!/usr/bin/env python3
"""
Market Data Collector for Vietnam Stock Daily Briefing
Fetches global market quotes (US, Asia, Commodities, FX) and domestic market news.
"""

import sys
import ssl
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

SKILL_DIR = Path(__file__).resolve().parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))


def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_quote_yahoo(symbol: str) -> Dict[str, Any]:
    """Fetch recent price and change for a symbol via Yahoo Finance chart API."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?interval=1d&range=5d"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8, context=get_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data.get("chart", {}).get("result", [])
            if not result:
                return {}
            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice", 0.0)
            prev = meta.get("previousClose") or meta.get("chartPreviousClose") or price
            change = price - prev if prev else 0.0
            change_pct = (change / prev * 100) if prev and prev != 0 else 0.0
            return {
                "symbol": symbol,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "currency": meta.get("currency", "USD"),
            }
    except Exception as e:
        print(f"[*] Yahoo quote warning for {symbol}: {e}", file=sys.stderr)
        return {}


def fetch_global_markets() -> Dict[str, Any]:
    """Fetch global market indicators across US, Asia, Commodities and FX."""
    symbols = {
        "S&P 500": "^GSPC",
        "Nasdaq Composite": "^IXIC",
        "Dow Jones": "^DJI",
        "Nikkei 225 (Nhật Bản)": "^N225",
        "Hang Seng (Hồng Kông)": "^HSI",
        "Shanghai Composite (Thượng Hải)": "000001.SS",
        "Dầu WTI (Crude Oil)": "CL=F",
        "Dầu Brent (Brent Oil)": "BZ=F",
        "Vàng Thế giới (Gold Spot)": "GC=F",
        "Tỷ giá USD/VND": "USDVND=X",
    }

    quotes = {}
    for name, sym in symbols.items():
        q = fetch_quote_yahoo(sym)
        if q:
            quotes[name] = q
    return quotes


def fetch_vietnam_news(limit: int = 8) -> List[Dict[str, str]]:
    """Fetch latest Vietnam financial & stock news from CafeF RSS."""
    rss_urls = [
        ("Thị trường Chứng khoán", "https://cafef.vn/thi-truong-chung-khoan.rss"),
        ("Doanh nghiệp", "https://cafef.vn/doanh-nghiep.rss"),
        ("Vĩ mô - Ngân hàng", "https://cafef.vn/tai-chinh-ngan-hang.rss"),
    ]

    news_items = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for cat_name, url in rss_urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8, context=get_ssl_context()) as resp:
                root = ET.fromstring(resp.read())
                items = root.findall(".//item")
                for it in items[:4]:
                    title_elem = it.find("title")
                    link_elem = it.find("link")
                    pub_elem = it.find("pubDate")
                    desc_elem = it.find("description")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    pub = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                    desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

                    if title:
                        news_items.append({
                            "category": cat_name,
                            "title": title,
                            "link": link,
                            "pubDate": pub,
                            "summary": desc[:180]
                        })
        except Exception as e:
            print(f"[*] RSS warning for {cat_name}: {e}", file=sys.stderr)

    return news_items[:limit]


def fetch_watchlist_quotes(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Fetch recent price, change %, 5-day range and volume for watched Vietnam stocks."""
    if symbols is None:
        try:
            from watchlist_manager import get_watchlist
            symbols = get_watchlist()
        except Exception:
            symbols = ["FPT", "HPG", "SSI", "MWG", "TCB"]

    quotes = {}
    for raw_sym in symbols:
        clean_sym = raw_sym.strip().upper().replace(".VN", "")
        if not clean_sym:
            continue
        yahoo_sym = f"{clean_sym}.VN"
        q = fetch_quote_yahoo(yahoo_sym)
        if q:
            quotes[clean_sym] = {
                "symbol": clean_sym,
                "price": q["price"],
                "change": q["change"],
                "change_pct": q["change_pct"],
                "currency": "VND"
            }
        else:
            quotes[clean_sym] = {
                "symbol": clean_sym,
                "price": 0.0,
                "change": 0.0,
                "change_pct": 0.0,
                "currency": "VND"
            }
    return quotes


def get_consolidated_market_payload(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Assemble all raw market data for LLM analysis, including active stock watchlist."""
    return {
        "global_markets": fetch_global_markets(),
        "vietnam_news": fetch_vietnam_news(limit=7),
        "watchlist_stocks": fetch_watchlist_quotes(symbols=symbols)
    }


if __name__ == "__main__":
    data = get_consolidated_market_payload()
    print("=== GLOBAL INDICATORS ===")
    for k, v in data["global_markets"].items():
        print(f"{k}: {v['price']} ({v['change_pct']:+.2f}%)")
    print(f"\n=== VIETNAM NEWS ({len(data['vietnam_news'])} items) ===")
    for n in data["vietnam_news"]:
        print(f"[{n['category']}] {n['title']}")
    print(f"\n=== WATCHLIST STOCKS ({len(data['watchlist_stocks'])} items) ===")
    for sym, item in data["watchlist_stocks"].items():
        print(f"{sym}: {item['price']:,.0f} VND ({item['change_pct']:+.2f}%)")

