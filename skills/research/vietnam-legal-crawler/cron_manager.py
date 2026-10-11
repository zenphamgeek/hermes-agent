#!/usr/bin/env python3
"""
Hourly Cron Manager for Vietnam Legal Documents Crawler
Integrates with Hermes Cron Engine (~/.hermes/cron/jobs.json) and local daemon runners.
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

SKILL_DIR = Path(__file__).resolve().parent
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))
CRON_JOBS_FILE = HERMES_HOME / "cron" / "jobs.json"
DEFAULT_OUTPUT_DIR = Path("/home/zen/hermes-agent/output_legal_docs")

CRAWLER_SCRIPT = SKILL_DIR / "crawler.py"


def load_cron_jobs() -> Dict[str, Any]:
    """Load existing Hermes cron jobs from ~/.hermes/cron/jobs.json."""
    if CRON_JOBS_FILE.exists():
        try:
            with open(CRON_JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "jobs" in data and isinstance(data["jobs"], list):
                    return data
        except Exception as e:
            print(f"[*] Warning reading cron jobs: {e}", file=sys.stderr)
    return {"jobs": [], "updated_at": datetime.now(timezone.utc).isoformat()}


def save_cron_jobs(data: Dict[str, Any]) -> bool:
    """Persist Hermes cron jobs to ~/.hermes/cron/jobs.json."""
    CRON_JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(CRON_JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[!] Failed to save cron jobs: {e}", file=sys.stderr)
        return False


def install_hourly_cron(notify: bool = True, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Register hourly cron job (0 * * * *) in Hermes Cron System."""
    data = load_cron_jobs()
    job_id = "job_vietnam_legal_hourly"
    out_dir = output_dir or str(DEFAULT_OUTPUT_DIR)
    
    cmd = f"python3 {CRAWLER_SCRIPT} -o {out_dir}"
    if notify:
        cmd += " --notify"

    job_def = {
        "id": job_id,
        "name": "vietnam-legal-hourly-sync",
        "prompt": f"Chạy đồng bộ tự động văn bản quy phạm pháp luật Việt Nam hàng giờ bằng lệnh: {cmd}. Tải toàn văn và file đính kèm PDF/DOCX có chữ ký số về kho tri thức, kiểm tra văn bản mới và gửi cảnh báo Telegram.",
        "skills": ["vietnam-legal-crawler", "sync-hs-knowledge", "sync-hse-knowledge"],
        "skill": "vietnam-legal-crawler",
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
            "display": "0 * * * * (Hourly sync)"
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

    # Remove existing job with same ID if exists
    jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]
    jobs_list.append(job_def)
    data["jobs"] = jobs_list

    save_cron_jobs(data)

    return {
        "status": "installed",
        "job_id": job_id,
        "schedule": "0 * * * * (Hourly - Mỗi 60 phút)",
        "command": cmd
    }


def uninstall_hourly_cron() -> Dict[str, Any]:
    """Remove legal hourly cron job from Hermes Cron System."""
    data = load_cron_jobs()
    job_id = "job_vietnam_legal_hourly"
    orig_len = len(data.get("jobs", []))
    data["jobs"] = [j for j in data.get("jobs", []) if j.get("id") != job_id]
    
    if len(data["jobs"]) < orig_len:
        save_cron_jobs(data)
        return {"status": "uninstalled", "job_id": job_id}
    return {"status": "not_found", "job_id": job_id}


def get_cron_status(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Inspect current cron status, execution statistics, and database stats."""
    out_dir = output_dir or DEFAULT_OUTPUT_DIR
    db_path = out_dir / "history.sqlite"
    
    total_docs = 0
    recent_runs = []
    latest_docs = []

    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM legal_documents")
                total_docs = cursor.fetchone()[0]

                cursor.execute("SELECT * FROM crawl_runs ORDER BY completed_at DESC LIMIT 5")
                recent_runs = [dict(r) for r in cursor.fetchall()]

                cursor.execute("SELECT doc_id, so_hieu, loai_van_ban, co_quan_ban_hanh, ngay_ban_hanh, trich_yeu FROM legal_documents ORDER BY crawled_at DESC LIMIT 5")
                latest_docs = [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[*] Warning querying DB: {e}", file=sys.stderr)

    cron_data = load_cron_jobs()
    is_installed = any(j.get("id") == "job_vietnam_legal_hourly" for j in cron_data.get("jobs", []))

    return {
        "is_installed": is_installed,
        "schedule": "0 * * * * (Mỗi giờ một lần)",
        "output_dir": str(out_dir),
        "total_documents": total_docs,
        "recent_runs": recent_runs,
        "latest_docs": latest_docs
    }


def format_status_telegram_message(status: Dict[str, Any]) -> str:
    """Format status report for Telegram."""
    installed_icon = "🟢 Đang hoạt động" if status["is_installed"] else "⚪ Chưa đăng ký (Chạy thủ công)"
    total_docs = status["total_documents"]
    
    latest_items = []
    for d in status.get("latest_docs", []):
        so_hieu = d.get("so_hieu") or d.get("doc_id")
        loai = d.get("loai_van_ban") or "VB"
        trich = d.get("trich_yeu", "")[:70]
        latest_items.append(f"• <b>{so_hieu}</b> ({loai}): <i>{trich}...</i>")
    
    latest_block = "\n".join(latest_items) if latest_items else "<i>(Chưa có văn bản nào trong kho dữ liệu)</i>"

    return (
        f"⚖️ <b>HỆ THỐNG CRAWL VĂN BẢN PHÁP LUẬT TỰ ĐỘNG (HOURLY CRON)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ <b>Trạng thái Lập lịch:</b> {installed_icon}\n"
        f"⏰ <b>Tần suất:</b> <code>0 * * * *</code> (Hourly Sync - Mỗi 60 phút)\n"
        f"📚 <b>Tổng số văn bản đã thu thập:</b> <b>{total_docs}</b> văn bản\n\n"
        f"📑 <b>VĂN BẢN MỚI THU THẬP GẦN ĐÂY:</b>\n"
        f"{latest_block}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>Lệnh thao tác nhanh:</b>\n"
        f"• Thu thập ngay: <code>/legal_crawl</code>\n"
        f"• Xem trạng thái: <code>/legal_cron_status</code>\n"
        f"• Tìm kiếm văn bản: <code>/legal_search [từ khóa]</code>"
    )


def main():
    parser = argparse.ArgumentParser(description="Manage Hourly Cron for Vietnam Legal Document Crawler.")
    subparsers = parser.add_subparsers(dest="command", help="Cron actions")

    install_p = subparsers.add_parser("install", help="Register hourly cron job")
    install_p.add_argument("--no-notify", action="store_true", help="Disable Telegram alerts on new documents")
    install_p.add_argument("-o", "--output-dir", help="Target output folder")

    subparsers.add_parser("uninstall", help="Remove hourly cron job")
    
    status_p = subparsers.add_parser("status", help="Check cron and database status")
    status_p.add_argument("-o", "--output-dir", help="Target output folder")
    status_p.add_argument("--telegram", action="store_true", help="Format and print for Telegram")

    run_p = subparsers.add_parser("run-now", help="Execute one crawl run immediately")
    run_p.add_argument("-o", "--output-dir", help="Target output folder")
    run_p.add_argument("--notify", action="store_true", help="Send Telegram alerts")

    args = parser.parse_args()

    if args.command == "install":
        res = install_hourly_cron(notify=not args.no_notify, output_dir=args.output_dir)
        print(f"[✓] Successfully registered hourly cron job: {res['job_id']} -> {res['schedule']}")

    elif args.command == "uninstall":
        res = uninstall_hourly_cron()
        print(f"[✓] Cron job status: {res['status']}")

    elif args.command == "status" or not args.command:
        out_p = Path(args.output_dir) if getattr(args, "output_dir", None) else None
        st = get_cron_status(output_dir=out_p)
        if getattr(args, "telegram", False):
            print(format_status_telegram_message(st))
        else:
            print(f"=== Vietnam Legal Crawler Hourly Cron Status ===")
            print(f"Installed in Hermes Cron: {st['is_installed']}")
            print(f"Schedule: {st['schedule']}")
            print(f"Output Folder: {st['output_dir']}")
            print(f"Total Documents in DB: {st['total_documents']}")
            if st["latest_docs"]:
                print("\nRecent Documents:")
                for d in st["latest_docs"]:
                    print(f" - [{d['so_hieu']}] {d['loai_van_ban']}: {d['trich_yeu'][:80]}")

    elif args.command == "run-now":
        from crawler import VietnamLegalCrawler
        crawler = VietnamLegalCrawler(
            output_dir=args.output_dir,
            download_attachments=True,
            notify_telegram=args.notify
        )
        crawler.run_crawl_cycle()


if __name__ == "__main__":
    main()
