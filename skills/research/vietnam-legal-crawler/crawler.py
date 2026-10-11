#!/usr/bin/env python3
"""
Vietnam Legal Document Crawler & Ingestion Engine
Crawls official Vietnamese legal documents (vanban.chinhphu.vn, vbpl.vn),
extracts metadata, downloads signed PDF attachments, and maintains SQLite manifest.
"""

import os
import sys
import ssl
import json
import time
import hashlib
import sqlite3
import argparse
import urllib.request
import urllib.parse
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = Path("/home/zen/hermes-agent/output_legal_docs")
DEFAULT_HERMES_ENV = Path("/home/zen/.hermes/.env")


def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_browser_headers() -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }


def load_hermes_env() -> Dict[str, str]:
    """Load Telegram token & chat ID from ~/.hermes/.env."""
    env_vars = {}
    if DEFAULT_HERMES_ENV.exists():
        with open(DEFAULT_HERMES_ENV, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


def send_telegram_alert(doc_meta: Dict[str, Any]) -> bool:
    """Send immediate Telegram notification when a new legal document is indexed."""
    env = load_hermes_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    so_hieu = doc_meta.get("so_hieu", "N/A")
    loai_vb = doc_meta.get("loai_van_ban", "Văn bản pháp luật")
    co_quan = doc_meta.get("co_quan_ban_hanh", "Chính phủ")
    ngay_bh = doc_meta.get("ngay_ban_hanh", "N/A")
    nguoi_ky = doc_meta.get("nguoi_ky", "N/A")
    trich_yeu = doc_meta.get("trich_yeu", "")
    attach_count = len(doc_meta.get("attachments", []))

    text = (
        f"📜 <b>VĂN BẢN PHÁP LUẬT MỚI CẬP NHẬT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Số hiệu:</b> <code>{so_hieu}</code>\n"
        f"🏛️ <b>Cơ quan:</b> {co_quan}\n"
        f"📑 <b>Loại văn bản:</b> {loai_vb}\n"
        f"✍️ <b>Người ký:</b> {nguoi_ky} | 🗓️ <b>Ngày BH:</b> {ngay_bh}\n"
        f"📎 <b>File đính kèm:</b> {attach_count} file (PDF/DOCX đã lưu)\n\n"
        f"📝 <b>Trích yếu:</b>\n"
        f"<i>{trich_yeu}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <i>Hermes Legal Intelligence • Hourly Sync</i>"
    )

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
        with urllib.request.urlopen(req, timeout=15, context=get_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception as e:
        print(f"[!] Failed to send Telegram alert for {so_hieu}: {e}", file=sys.stderr)
        return False


class LegalDatabase:
    """Manages SQLite storage for legal documents metadata, crawl history, and checkpoints."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS legal_documents (
                    doc_id TEXT PRIMARY KEY,
                    source TEXT,
                    so_hieu TEXT,
                    loai_van_ban TEXT,
                    co_quan_ban_hanh TEXT,
                    nguoi_ky TEXT,
                    ngay_ban_hanh TEXT,
                    ngay_hieu_luc TEXT,
                    tinh_trang TEXT,
                    trich_yeu TEXT,
                    url TEXT,
                    attachments_json TEXT,
                    content_sha256 TEXT,
                    clean_text_path TEXT,
                    crawled_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS crawl_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT,
                    completed_at TEXT,
                    source TEXT,
                    discovered_count INTEGER,
                    downloaded_count INTEGER,
                    status TEXT,
                    error_message TEXT
                )
            """)
            conn.commit()

    def get_existing_doc_ids(self) -> set:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT doc_id FROM legal_documents")
            return {row[0] for row in cursor.fetchall()}

    def record_document(self, doc_meta: Dict[str, Any]):
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO legal_documents (
                    doc_id, source, so_hieu, loai_van_ban, co_quan_ban_hanh,
                    nguoi_ky, ngay_ban_hanh, ngay_hieu_luc, tinh_trang,
                    trich_yeu, url, attachments_json, content_sha256,
                    clean_text_path, crawled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_meta["doc_id"],
                doc_meta.get("source", "VN_GOV_LEGAL"),
                doc_meta.get("so_hieu", ""),
                doc_meta.get("loai_van_ban", ""),
                doc_meta.get("co_quan_ban_hanh", ""),
                doc_meta.get("nguoi_ky", ""),
                doc_meta.get("ngay_ban_hanh", ""),
                doc_meta.get("ngay_hieu_luc", ""),
                doc_meta.get("tinh_trang", "Còn hiệu lực"),
                doc_meta.get("trich_yeu", ""),
                doc_meta.get("url", ""),
                json.dumps(doc_meta.get("attachments", []), ensure_ascii=False),
                doc_meta.get("content_sha256", ""),
                doc_meta.get("clean_text_path", ""),
                now_str
            ))
            conn.commit()

    def record_run(self, run_id: str, started_at: str, source: str, discovered: int, downloaded: int, status: str = "completed", error: str = ""):
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO crawl_runs (
                    run_id, started_at, completed_at, source,
                    discovered_count, downloaded_count, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (run_id, started_at, now_str, source, discovered, downloaded, status, error))
            conn.commit()


class VietnamLegalCrawler:
    """Official Vietnam Government Legal Document Crawler (vanban.chinhphu.vn)."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        download_attachments: bool = True,
        notify_telegram: bool = False,
        limit: Optional[int] = None
    ):
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.raw_dir = self.output_dir / "raw"
        self.clean_dir = self.output_dir / "clean_text"
        self.download_attachments = download_attachments
        self.notify_telegram = notify_telegram
        self.limit = limit

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.clean_dir.mkdir(parents=True, exist_ok=True)

        self.db = LegalDatabase(self.output_dir / "history.sqlite")

    def discover_recent_documents(self) -> List[Dict[str, str]]:
        """Scrape the latest legal document index from vanban.chinhphu.vn."""
        url = "https://vanban.chinhphu.vn/he-thong-van-ban"
        headers = get_browser_headers()
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15, context=get_ssl_context()) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[!] Error fetching ChinhPhu legal index: {e}", file=sys.stderr)
            return []

        doc_links = re.findall(r'href=[\"\'](/[^\"\']*docid=(\d+)[^\"\']*)[\"\']', html)
        seen = set()
        discovered = []

        for rel_url, doc_id in doc_links:
            if doc_id in seen:
                continue
            seen.add(doc_id)
            full_url = f"https://vanban.chinhphu.vn{rel_url}" if rel_url.startswith("/") else rel_url
            discovered.append({
                "doc_id": doc_id,
                "url": full_url,
                "source": "VN_GOV_LEGAL"
            })

        print(f"[*] Discovered {len(discovered)} recent documents on vanban.chinhphu.vn")
        return discovered

    def fetch_and_parse_document(self, doc_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Fetch detail page of a document, extract table metadata and attachment links."""
        doc_id = doc_info["doc_id"]
        url = doc_info["url"]
        headers = get_browser_headers()
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15, context=get_ssl_context()) as resp:
                raw_bytes = resp.read()
                html = raw_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[!] Error fetching document {doc_id} ({url}): {e}", file=sys.stderr)
            return None

        # Extract table cells
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', html, re.DOTALL)]
        
        meta = {
            "doc_id": doc_id,
            "source": doc_info.get("source", "VN_GOV_LEGAL"),
            "url": url,
            "so_hieu": "",
            "loai_van_ban": "",
            "co_quan_ban_hanh": "",
            "ngay_ban_hanh": "",
            "ngay_hieu_luc": "",
            "nguoi_ky": "",
            "trich_yeu": "",
            "tinh_trang": "Còn hiệu lực",
            "attachments": [],
            "content_sha256": hashlib.sha256(raw_bytes).hexdigest()
        }

        # Parse key-value pairs from cells
        for i in range(len(cells) - 1):
            lbl = cells[i].lower()
            val = cells[i + 1]
            if "số ký hiệu" in lbl:
                meta["so_hieu"] = val
            elif "loại văn bản" in lbl:
                meta["loai_van_ban"] = val
            elif "cơ quan ban hành" in lbl:
                meta["co_quan_ban_hanh"] = val
            elif "ngày ban hành" in lbl:
                meta["ngay_ban_hanh"] = val
            elif "ngày có hiệu lực" in lbl or "ngày hiệu lực" in lbl:
                meta["ngay_hieu_luc"] = val
            elif "người ký" in lbl:
                meta["nguoi_ky"] = val
            elif "trích yếu" in lbl:
                meta["trich_yeu"] = val

        # Fallback if trich_yeu empty
        if not meta["trich_yeu"] and cells:
            for c in cells:
                if len(c) > 40 and "Chính phủ" in c:
                    meta["trich_yeu"] = c
                    break

        # Extract attachments (PDF, DOC, DOCX)
        attach_urls = re.findall(r'href=[\"\']([^\"\']+\.(?:pdf|doc|docx))[\"\']', html, re.IGNORECASE)
        for att in set(attach_urls):
            att_full = att if att.startswith("http") else f"https://vanban.chinhphu.vn{att}"
            meta["attachments"].append(att_full)

        return meta

    def download_attachments_for_doc(self, doc_meta: Dict[str, Any], doc_dir: Path) -> List[str]:
        """Download raw attachment files (PDF/DOCX) into document raw directory."""
        saved_files = []
        headers = get_browser_headers()

        for att_url in doc_meta.get("attachments", []):
            fname = urllib.parse.unquote(Path(att_url).name)
            local_att_path = doc_dir / fname
            if local_att_path.exists() and local_att_path.stat().st_size > 0:
                saved_files.append(local_att_path.name)
                continue

            try:
                time.sleep(0.5)  # respectful delay
                req = urllib.request.Request(att_url, headers=headers)
                with urllib.request.urlopen(req, timeout=30, context=get_ssl_context()) as resp:
                    data = resp.read()
                    with open(local_att_path, "wb") as f:
                        f.write(data)
                    saved_files.append(local_att_path.name)
                    print(f"  [✓] Downloaded attachment: {fname} ({len(data)} bytes)")
            except Exception as e:
                print(f"  [!] Failed to download attachment {att_url}: {e}", file=sys.stderr)

        return saved_files

    def process_and_save(self, doc_meta: Dict[str, Any]) -> bool:
        """Save raw folder, metadata.json, clean text for search/RAG, and database record."""
        doc_id = doc_meta["doc_id"]
        doc_dir = self.raw_dir / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        # 1. Download attachments
        if self.download_attachments:
            self.download_attachments_for_doc(doc_meta, doc_dir)

        # 2. Save metadata.json
        with open(doc_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(doc_meta, f, ensure_ascii=False, indent=2)

        # 3. Create clean text document
        clean_text = (
            f"SỐ HIỆU: {doc_meta.get('so_hieu')}\n"
            f"LOẠI VĂN BẢN: {doc_meta.get('loai_van_ban')}\n"
            f"CƠ QUAN BAN HÀNH: {doc_meta.get('co_quan_ban_hanh')}\n"
            f"NGÀY BAN HÀNH: {doc_meta.get('ngay_ban_hanh')}\n"
            f"NGÀY HIỆU LỰC: {doc_meta.get('ngay_hieu_luc')}\n"
            f"NGƯỜI KÝ: {doc_meta.get('nguoi_ky')}\n"
            f"TÌNH TRẠNG: {doc_meta.get('tinh_trang')}\n"
            f"TRÍCH YẾU:\n{doc_meta.get('trich_yeu')}\n\n"
            f"NGUỒN TRUY CẬP: {doc_meta.get('url')}\n"
        )
        safe_so_hieu = re.sub(r'[/\\:*?"<>|]', '_', doc_meta.get("so_hieu", doc_id))
        clean_file_path = self.clean_dir / f"{doc_id}_{safe_so_hieu}.txt"
        with open(clean_file_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        doc_meta["clean_text_path"] = str(clean_file_path.relative_to(self.output_dir))

        # 4. Record to SQLite database
        self.db.record_document(doc_meta)
        return True

    def run_crawl_cycle(self) -> Dict[str, Any]:
        """Execute one complete incremental crawl cycle."""
        start_time = datetime.now(timezone.utc).isoformat()
        run_id = f"run_{int(time.time())}"
        print(f"=== Starting Legal Documents Crawl Cycle [{run_id}] ===")

        discovered = self.discover_recent_documents()
        existing_ids = self.db.get_existing_doc_ids()

        pending = [d for d in discovered if d["doc_id"] not in existing_ids]
        if self.limit and self.limit > 0:
            pending = pending[:self.limit]

        print(f"[*] Discovered: {len(discovered)} | Already Indexed: {len(existing_ids)} | Pending: {len(pending)}")

        downloaded_count = 0
        newly_indexed = []

        for idx, doc_info in enumerate(pending, 1):
            print(f"[{idx}/{len(pending)}] Crawling document ID {doc_info['doc_id']}...")
            meta = self.fetch_and_parse_document(doc_info)
            if meta:
                self.process_and_save(meta)
                downloaded_count += 1
                newly_indexed.append(meta)
                print(f" [✓] Indexed: {meta.get('so_hieu', 'N/A')} - {meta.get('trich_yeu', '')[:80]}...")

                if self.notify_telegram:
                    send_telegram_alert(meta)

            time.sleep(1.0)  # Rate-limit safety

        self.db.record_run(
            run_id=run_id,
            started_at=start_time,
            source="VN_GOV_LEGAL",
            discovered=len(discovered),
            downloaded=downloaded_count,
            status="completed"
        )
        self._export_json_manifest()

        print(f"=== Crawl Cycle Completed: {downloaded_count} new documents ingested ===")
        return {
            "run_id": run_id,
            "discovered": len(discovered),
            "downloaded": downloaded_count,
            "newly_indexed": newly_indexed
        }

    def _export_json_manifest(self):
        """Export high-level manifest.json with real-time statistics."""
        with sqlite3.connect(self.output_dir / "history.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM legal_documents ORDER BY crawled_at DESC")
            docs = [dict(r) for r in cursor.fetchall()]

        manifest_data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_documents": len(docs),
            "sources": ["VN_GOV_LEGAL", "vanban.chinhphu.vn"],
            "documents_sample": docs[:20]
        }
        with open(self.output_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Vietnam Legal Documents Hourly Crawler.")
    parser.add_argument("-o", "--output-dir", help="Output directory (default: ./output_legal_docs)")
    parser.add_argument("--limit", type=int, help="Limit max documents to crawl per cycle")
    parser.add_argument("--no-attachments", action="store_true", help="Skip downloading PDF/DOCX attachments")
    parser.add_argument("--notify", action="store_true", help="Send Telegram alerts for new documents")
    parser.add_argument("--loop", action="store_true", help="Run continuously in hourly cron loop")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds between crawl cycles (default: 3600s = 1 hour)")
    args = parser.parse_args()

    crawler = VietnamLegalCrawler(
        output_dir=args.output_dir,
        download_attachments=not args.no_attachments,
        notify_telegram=args.notify,
        limit=args.limit
    )

    if args.loop:
        print(f"[*] Running in Scheduled Loop mode (Checking every {args.interval}s)... Press Ctrl+C to stop.")
        while True:
            try:
                crawler.run_crawl_cycle()
                print(f"[*] Cycle finished. Sleeping for {args.interval}s until next hourly crawl...")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n[!] Hourly crawler stopped by user.")
                break
            except Exception as e:
                print(f"[!] Error in crawl cycle: {e}. Retrying in {args.interval}s...", file=sys.stderr)
                time.sleep(args.interval)
    else:
        crawler.run_crawl_cycle()


if __name__ == "__main__":
    main()
