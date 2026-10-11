#!/usr/bin/env python3
"""
Intelligent Stock News Memory & Semantic Deduplication Engine.
Maintains persistent SQLite storage to detect and cluster duplicate corporate news
across multiple Vietnamese financial newspapers (CafeF, Vietstock, VnEconomy, etc.).
"""

import os
import re
import json
import sqlite3
import hashlib
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))
DEFAULT_DB_PATH = HERMES_HOME / "stock_news_memory.sqlite"

# Common financial corporate event keywords for semantic clustering
EVENT_KEYWORDS = [
    "trái phiếu", "cổ tức", "bctc", "báo cáo tài chính", "lợi nhuận", "doanh thu",
    "lỗ", "lãi", "tăng vốn", "phát hành", "chào bán", "hoán đổi nợ", "trúng thầu",
    "đại hội cổ đông", "đhcđ", "chủ tịch", "tổng giám đốc", "bổ nhiệm", "miễn nhiệm",
    "tạm hoãn xuất cảnh", "khởi tố", "thanh tra", "bán giải chấp", "mua lại", "thoái vốn",
    "nâng hạng", "ftse", "msci", "esop", "cổ phiếu quỹ", "sáp nhập", "m&a", "cao tốc",
    "dự án", "đấu thầu", "giải ngân", "nợ xấu", "thâu tóm", "cổ đông lớn"
]

STOP_WORDS = {
    "và", "của", "cho", "với", "về", "trong", "được", "các", "những", "này", "đó",
    "khi", "tại", "theo", "đến", "từ", "là", "có", "sẽ", "đã", "đang", "bị", "bởi",
    "ông", "bà", "sau", "trước", "vừa", "sắp", "ngày", "tháng", "năm", "hôm", "nay",
    "cafef", "vietstock", "vneconomy", "tin nhanh chứng khoán", "báo thanh niên",
    "dnse", "nguoiquansat.vn", "tuổi trẻ", "vnexpress", "dân trí", "baodautu"
}


def normalize_text(text: str) -> str:
    """Normalize Vietnamese text by stripping punctuation and common noise."""
    t = text.lower()
    t = re.sub(r'https?://\S+', '', t)
    t = re.sub(r'[^\w\s\d]', ' ', t)
    tokens = [w for w in t.split() if w not in STOP_WORDS and len(w) > 1]
    return " ".join(tokens)


def extract_event_signature(symbol: str, title: str, summary: str = "") -> Tuple[str, List[str], List[str]]:
    """
    Extract (signature_hash, matched_keywords, numbers) to identify core corporate event.
    """
    combined = f"{title} {summary}".lower()
    
    # 1. Match domain keywords
    matched_kws = [kw for kw in EVENT_KEYWORDS if kw in combined]
    
    # 2. Extract numbers (e.g. 6.720 tỷ, 14.5%, 67,2 triệu, 100%, 270 tỷ)
    numbers = re.findall(r'\d+(?:[.,]\d+)?(?:\s*(?:tỷ|triệu|ngàn tỷ|%|năm|đồng|đ))?', combined)
    clean_nums = list(set([n.strip() for n in numbers if len(n.strip()) > 1]))[:5]

    # 3. Create stable signature
    kw_str = "-".join(sorted(matched_kws))
    num_str = "-".join(sorted(clean_nums))
    sig_raw = f"{symbol.upper()}:{kw_str}:{num_str}"
    sig_hash = hashlib.md5(sig_raw.encode("utf-8")).hexdigest()[:16]

    return sig_hash, matched_kws, clean_nums


def compute_title_similarity(t1: str, t2: str) -> float:
    """Compute semantic text overlap and sequence similarity between 2 news titles."""
    n1 = normalize_text(t1)
    n2 = normalize_text(t2)
    
    # Sequence ratio
    seq_ratio = SequenceMatcher(None, n1, n2).ratio()
    
    # Jaccard word set overlap
    w1 = set(n1.split())
    w2 = set(n2.split())
    jaccard = len(w1 & w2) / max(len(w1 | w2), 1)
    
    return max(seq_ratio, jaccard)


class StockNewsMemory:
    """Persistent SQLite Memory for Vietnamese Stock News & Corporate Events."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS corporate_events (
                    event_id TEXT PRIMARY KEY,
                    symbol TEXT,
                    event_signature TEXT,
                    canonical_title TEXT,
                    summary TEXT,
                    matched_keywords_json TEXT,
                    sources_json TEXT,
                    first_seen_at TEXT,
                    last_updated_at TEXT,
                    analyzed INTEGER DEFAULT 0,
                    analysis_result TEXT,
                    sentiment TEXT,
                    alert_sent INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS raw_articles (
                    url_hash TEXT PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    source_name TEXT,
                    symbol TEXT,
                    published_at TEXT,
                    event_id TEXT,
                    crawled_at TEXT,
                    FOREIGN KEY (event_id) REFERENCES corporate_events(event_id)
                )
            """)
            conn.commit()

    def check_and_cluster_article(
        self,
        symbol: str,
        title: str,
        url: str,
        source_name: str,
        published_at: str,
        summary: str = "",
        similarity_threshold: float = 0.55
    ) -> Tuple[bool, str, bool]:
        """
        Check if article is new or duplicate of an existing corporate event.
        Returns:
            (is_duplicate: bool, event_id: str, is_new_event: bool)
        """
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        now_iso = datetime.now(timezone.utc).isoformat()
        
        sig_hash, matched_kws, numbers = extract_event_signature(symbol, title, summary)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Check if exact URL already ingested
            cursor.execute("SELECT event_id FROM raw_articles WHERE url_hash = ?", (url_hash,))
            row = cursor.fetchone()
            if row:
                return True, row["event_id"], False

            # 2. Check recent events (last 5 days) for the same symbol
            time_cutoff = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
            cursor.execute("""
                SELECT * FROM corporate_events 
                WHERE symbol = ? AND first_seen_at >= ?
                ORDER BY first_seen_at DESC
            """, (symbol.upper(), time_cutoff))
            recent_events = [dict(r) for r in cursor.fetchall()]

            matched_event_id = None

            for ev in recent_events:
                # Check exact signature match if keywords were found
                if matched_kws and ev["event_signature"] == sig_hash:
                    matched_event_id = ev["event_id"]
                    break

                # Check title similarity
                sim = compute_title_similarity(title, ev["canonical_title"])
                if sim >= similarity_threshold:
                    matched_event_id = ev["event_id"]
                    break

            if matched_event_id:
                # Duplicate / Follow-up article of an already recorded event
                # Update sources list
                cursor.execute("SELECT sources_json FROM corporate_events WHERE event_id = ?", (matched_event_id,))
                src_row = cursor.fetchone()
                sources = json.loads(src_row["sources_json"]) if src_row and src_row["sources_json"] else []
                if source_name not in sources:
                    sources.append(source_name)
                    cursor.execute("""
                        UPDATE corporate_events 
                        SET sources_json = ?, last_updated_at = ? 
                        WHERE event_id = ?
                    """, (json.dumps(sources, ensure_ascii=False), now_iso, matched_event_id))

                # Insert raw article reference
                cursor.execute("""
                    INSERT INTO raw_articles (url_hash, url, title, source_name, symbol, published_at, event_id, crawled_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (url_hash, url, title, source_name, symbol.upper(), published_at, matched_event_id, now_iso))
                conn.commit()

                return True, matched_event_id, False

            else:
                # Genuinely brand new corporate event!
                new_event_id = f"ev_{symbol.upper()}_{int(datetime.now().timestamp())}_{sig_hash[:6]}"
                cursor.execute("""
                    INSERT INTO corporate_events (
                        event_id, symbol, event_signature, canonical_title, summary,
                        matched_keywords_json, sources_json, first_seen_at, last_updated_at,
                        analyzed, alert_sent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
                """, (
                    new_event_id,
                    symbol.upper(),
                    sig_hash,
                    title,
                    summary,
                    json.dumps(matched_kws, ensure_ascii=False),
                    json.dumps([source_name], ensure_ascii=False),
                    now_iso,
                    now_iso
                ))

                cursor.execute("""
                    INSERT INTO raw_articles (url_hash, url, title, source_name, symbol, published_at, event_id, crawled_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (url_hash, url, title, source_name, symbol.upper(), published_at, new_event_id, now_iso))
                conn.commit()

                return False, new_event_id, True

    def record_analysis_result(
        self,
        event_id: str,
        analysis_result: str,
        sentiment: str = "NEUTRAL",
        alert_sent: bool = True
    ):
        """Save the deep LLM analysis and mark the event as alerted."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE corporate_events 
                SET analyzed = 1,
                    analysis_result = ?,
                    sentiment = ?,
                    alert_sent = ?
                WHERE event_id = ?
            """, (analysis_result, sentiment, 1 if alert_sent else 0, event_id))
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_articles")
            total_articles = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM corporate_events")
            total_events = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM corporate_events WHERE analyzed = 1")
            analyzed_events = cursor.fetchone()[0]

            cursor.execute("""
                SELECT symbol, COUNT(*) as cnt 
                FROM corporate_events 
                GROUP BY symbol ORDER BY cnt DESC
            """)
            by_symbol = {r[0]: r[1] for r in cursor.fetchall()}

            return {
                "total_articles_scanned": total_articles,
                "unique_corporate_events": total_events,
                "analyzed_events": analyzed_events,
                "duplicate_articles_merged": max(0, total_articles - total_events),
                "events_by_symbol": by_symbol
            }
