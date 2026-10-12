#!/usr/bin/env python3
"""
Hermes Agent - 24/7 Hourly Digest Report & Anomaly Monitor.

Components:
1. CronAnomalyDetector: Detects clogged runs (>=3 consecutive failures), drift-skips,
   overdue schedules, auth failures, rate limits, and ticker freshness.
2. EntropyDegradationDetector: Monitors the 5 external entropy streams:
   - Stock News Feed (stock_news_memory.sqlite)
   - Legal & Regulatory Crawler (output_legal_docs)
   - Media Asset Bank 24/7 Producer (daily_media_production.json)
   - Median-0 Math Sync (median_hourly_sync.log)
   - AGY Fleet & Clef Mesh (http://localhost:7777/api/fleet/summary & /council)
3. CompositeHealthCalculator: Computes overall weighted health score (0-100) and severity.
4. HermesTelegramNotifier: Sends rich HTML alerts and executive hourly digests to Telegram.
5. SelfHealingManager: Automatically un-wedges drift-skipped cron jobs and triggers entropy recovery.

CLI:
  python3 tools/hourly_digest_monitor.py --scan
  python3 tools/hourly_digest_monitor.py --notify
  python3 tools/hourly_digest_monitor.py --alert-only
  python3 tools/hourly_digest_monitor.py --self-heal
"""

import argparse
import hashlib
import json
import logging
import os
import re
import shlex
import sqlite3
import ssl
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hourly_digest_monitor")

# Default paths
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_EXECUTIONS_DB = HERMES_HOME / "cron" / "executions.db"
DEFAULT_JOBS_JSON = HERMES_HOME / "cron" / "jobs.json"
DEFAULT_TICKER_HEARTBEAT = HERMES_HOME / "cron" / "ticker_heartbeat"

DEFAULT_STOCK_DB = HERMES_HOME / "stock_news_memory.sqlite"
DEFAULT_LEGAL_DIR = REPO_ROOT / "output_legal_docs"
DEFAULT_MEDIA_JSON = HERMES_HOME / "daily_media_production.json"
DEFAULT_MEDIAN_LOG = REPO_ROOT / "assets" / "scripts_video" / "logs" / "median_hourly_sync.log"

DEFAULT_ENV_FILE = HERMES_HOME / ".env"
DEFAULT_CHAT_ID = "1431349185"

FLEET_SUMMARY_URL = "http://localhost:7777/api/fleet/summary"
FLEET_COUNCIL_URL = "http://localhost:7777/api/fleet/council"


def get_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def parse_timestamp(val: Any) -> Optional[datetime]:
    """Parse various timestamp representations into timezone-aware UTC datetime."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)
    if isinstance(val, str):
        val = val.strip()
        try:
            # Handle float string
            ts = float(val)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except ValueError:
            pass

        # Try ISO 8601
        try:
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

        # Try standard formats: e.g. 2026/10/12 16:33:15
        for fmt in (
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
        ):
            try:
                dt = datetime.strptime(val, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue
    return None


# ==============================================================================
# 1. CronAnomalyDetector
# ==============================================================================
class CronAnomalyDetector:
    """Audits Hermes cron scheduler state, executions database, and ticker heartbeat."""

    def __init__(
        self,
        db_path: Path = DEFAULT_EXECUTIONS_DB,
        jobs_path: Path = DEFAULT_JOBS_JSON,
        heartbeat_path: Path = DEFAULT_TICKER_HEARTBEAT,
        grace_period_seconds: int = 300,
    ):
        self.db_path = Path(db_path)
        self.jobs_path = Path(jobs_path)
        self.heartbeat_path = Path(heartbeat_path)
        self.grace_period_seconds = grace_period_seconds

    def load_jobs_map(self) -> Dict[str, Dict[str, Any]]:
        """Load jobs from jobs.json indexed by job_id."""
        if not self.jobs_path.exists():
            return {}
        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            jobs = data.get("jobs", []) if isinstance(data, dict) else data
            return {j.get("id"): j for j in jobs if isinstance(j, dict) and j.get("id")}
        except Exception as e:
            logger.warning("Failed loading jobs.json: %s", e)
            return {}

    def check_clogged_jobs(self, min_failures: int = 3) -> List[Dict[str, Any]]:
        """Detect jobs with >= min_failures consecutive failed executions."""
        if not self.db_path.exists():
            return []

        jobs_map = self.load_jobs_map()
        clogged = []

        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT job_id FROM executions")
            job_ids = [row[0] for row in cursor.fetchall() if row[0]]

            for jid in job_ids:
                cursor.execute(
                    "SELECT status, error, claimed_at FROM executions WHERE job_id = ? ORDER BY rowid DESC LIMIT 100",
                    (jid,),
                )
                runs = cursor.fetchall()
                consecutive = 0
                last_error = ""
                last_claimed = ""

                for status, error, claimed_at in runs:
                    if status in ("failed", "error"):
                        consecutive += 1
                        if not last_error and error:
                            last_error = error
                        if not last_claimed and claimed_at:
                            last_claimed = claimed_at
                    else:
                        break

                if consecutive >= min_failures:
                    job_info = jobs_map.get(jid, {})
                    clogged.append(
                        {
                            "job_id": jid,
                            "job_name": job_info.get("name") or jid,
                            "consecutive_failures": consecutive,
                            "last_error": last_error,
                            "last_claimed_at": last_claimed,
                        }
                    )
            conn.close()
        except Exception as e:
            logger.error("Failed checking clogged jobs in %s: %s", self.db_path, e)

        return clogged

    def check_drift_skipped_jobs(self) -> List[Dict[str, Any]]:
        """Detect jobs currently skipped or alerted due to model/provider drift."""
        jobs_map = self.load_jobs_map()
        drifted = []

        for jid, job in jobs_map.items():
            last_err = str(job.get("last_error") or "")
            drift_alerted = bool(job.get("drift_alerted"))
            is_drift_error = "[drift_skip" in last_err

            if drift_alerted or is_drift_error:
                drifted.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "drift_alerted": drift_alerted,
                        "last_error": last_err,
                        "model_snapshot": job.get("model_snapshot"),
                        "provider_snapshot": job.get("provider_snapshot"),
                        "pinned_model": job.get("model"),
                        "pinned_provider": job.get("provider"),
                    }
                )

        return drifted

    def check_overdue_jobs(self, now_utc: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Detect enabled jobs where next_run_at is overdue past the grace period."""
        jobs_map = self.load_jobs_map()
        overdue = []
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        for jid, job in jobs_map.items():
            if not job.get("enabled"):
                continue
            next_run_str = job.get("next_run_at")
            if not next_run_str:
                continue
            nra_dt = parse_timestamp(next_run_str)
            if not nra_dt:
                continue

            overdue_secs = (now_utc - nra_dt).total_seconds()
            if overdue_secs > self.grace_period_seconds:
                overdue.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "next_run_at": next_run_str,
                        "overdue_seconds": round(overdue_secs, 1),
                    }
                )

        return overdue

    def check_auth_failed_jobs(self) -> List[Dict[str, Any]]:
        """Detect jobs whose last execution or configured error indicates authentication failure."""
        jobs_map = self.load_jobs_map()
        auth_failed = []
        auth_regex = re.compile(r"(?i)\b(auth|401|403|invalid_grant|unauthorized)\b")

        for jid, job in jobs_map.items():
            last_err = str(job.get("last_error") or "")
            if auth_regex.search(last_err):
                auth_failed.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "last_error": last_err,
                    }
                )

        return auth_failed

    def check_rate_limited_jobs(self) -> List[Dict[str, Any]]:
        """Detect jobs whose last execution or configured error indicates rate limiting."""
        jobs_map = self.load_jobs_map()
        rate_limited = []
        rl_regex = re.compile(r"(?i)\b(429|rate\s*limit|usage\s*limit|quota\s*exceeded)\b")

        for jid, job in jobs_map.items():
            last_err = str(job.get("last_error") or "")
            if rl_regex.search(last_err):
                rate_limited.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "last_error": last_err,
                    }
                )

        return rate_limited

    def check_ticker_stale(
        self, max_age_seconds: float = 120.0, now_utc: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Check whether the cron ticker heartbeat is fresh."""
        if not self.heartbeat_path.exists():
            return {
                "exists": False,
                "is_stale": True,
                "age_seconds": 99999.0,
                "timestamp": None,
            }

        try:
            with open(self.heartbeat_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            ts_dt = parse_timestamp(content)
            if not ts_dt:
                ts_dt = datetime.fromtimestamp(self.heartbeat_path.stat().st_mtime, tz=timezone.utc)

            if now_utc is None:
                now_utc = datetime.now(timezone.utc)
            age = max(0.0, (now_utc - ts_dt).total_seconds())
            return {
                "exists": True,
                "is_stale": age > max_age_seconds,
                "age_seconds": round(age, 1),
                "timestamp": ts_dt.isoformat(),
            }
        except Exception as e:
            logger.error("Failed reading ticker heartbeat: %s", e)
            return {
                "exists": True,
                "is_stale": True,
                "age_seconds": 99999.0,
                "timestamp": None,
                "error": str(e),
            }

    def compute_cron_health_score(self, findings: Dict[str, Any]) -> int:
        """Compute cron subsystem health score (0-100%)."""
        score = 100

        # Heartbeat stale deduction
        if findings.get("ticker_heartbeat", {}).get("is_stale"):
            score -= 30

        # Clogged jobs deduction
        clogged = findings.get("clogged_jobs", [])
        score -= min(40, len(clogged) * 15)

        # Drift skipped deduction
        drifted = findings.get("drift_skipped_jobs", [])
        score -= min(40, len(drifted) * 15)

        # Auth failed deduction
        auth_failed = findings.get("auth_failed_jobs", [])
        score -= min(20, len(auth_failed) * 10)

        # Rate limited deduction
        rate_limited = findings.get("rate_limited_jobs", [])
        score -= min(20, len(rate_limited) * 10)

        # Overdue jobs deduction
        overdue = findings.get("overdue_jobs", [])
        score -= min(15, len(overdue) * 5)

        return max(0, min(100, score))

    def scan(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Perform comprehensive cron audit and return findings with health score."""
        clogged = self.check_clogged_jobs()
        drifted = self.check_drift_skipped_jobs()
        overdue = self.check_overdue_jobs(now_utc=now_utc)
        auth_failed = self.check_auth_failed_jobs()
        rate_limited = self.check_rate_limited_jobs()
        ticker = self.check_ticker_stale(now_utc=now_utc)

        findings = {
            "clogged_jobs": clogged,
            "drift_skipped_jobs": drifted,
            "overdue_jobs": overdue,
            "auth_failed_jobs": auth_failed,
            "rate_limited_jobs": rate_limited,
            "ticker_heartbeat": ticker,
        }
        findings["cron_health_score"] = self.compute_cron_health_score(findings)
        return findings


# ==============================================================================
# 2. EntropyDegradationDetector
# ==============================================================================
class EntropyDegradationDetector:
    """Monitors freshness and throughput of the 5 external entropy streams."""

    def __init__(
        self,
        stock_db_path: Path = DEFAULT_STOCK_DB,
        legal_dir_path: Path = DEFAULT_LEGAL_DIR,
        media_json_path: Path = DEFAULT_MEDIA_JSON,
        median_log_path: Path = DEFAULT_MEDIAN_LOG,
        fleet_summary_url: str = FLEET_SUMMARY_URL,
        fleet_council_url: str = FLEET_COUNCIL_URL,
    ):
        self.stock_db_path = Path(stock_db_path)
        self.legal_dir_path = Path(legal_dir_path)
        self.media_json_path = Path(media_json_path)
        self.median_log_path = Path(median_log_path)
        self.fleet_summary_url = fleet_summary_url
        self.fleet_council_url = fleet_council_url

    def check_stream_1_stock_news(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 1: Stock News Feed (stock_news_memory.sqlite)."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        if not self.stock_db_path.exists():
            return {
                "name": "Stock News Feed",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "articles_24h": 0,
                "unique_symbols": 0,
                "total_articles": 0,
                "total_events": 0,
                "error": "Database not found",
            }

        try:
            conn = sqlite3.connect(f"file:{self.stock_db_path}?mode=ro", uri=True)
            c = conn.cursor()

            c.execute("SELECT MAX(crawled_at) FROM raw_articles")
            max_crawled_raw = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM raw_articles")
            total_articles = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(DISTINCT symbol) FROM raw_articles")
            unique_symbols = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) FROM corporate_events")
            total_events = c.fetchone()[0] or 0

            hours_since_crawl = 9999.0
            articles_24h = 0

            if max_crawled_raw:
                dt_crawled = parse_timestamp(max_crawled_raw)
                if dt_crawled:
                    hours_since_crawl = max(0.0, (now_utc - dt_crawled).total_seconds() / 3600.0)

                # Count articles in last 24h
                c.execute("SELECT crawled_at FROM raw_articles")
                for row in c.fetchall():
                    dt = parse_timestamp(row[0])
                    if dt and (now_utc - dt).total_seconds() <= 86400:
                        articles_24h += 1

            conn.close()

            # Status classification
            if hours_since_crawl <= 2.0:
                status = "HEALTHY"
                score = 100
            elif hours_since_crawl <= 6.0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            return {
                "name": "Stock News Feed",
                "status": status,
                "score": score,
                "hours_since_crawl": round(hours_since_crawl, 1),
                "articles_24h": articles_24h,
                "unique_symbols": unique_symbols,
                "total_articles": total_articles,
                "total_events": total_events,
                "last_crawled_at": max_crawled_raw,
            }
        except Exception as e:
            logger.error("Stock news stream check failed: %s", e)
            return {
                "name": "Stock News Feed",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "articles_24h": 0,
                "unique_symbols": 0,
                "error": str(e),
            }

    def check_stream_2_legal_docs(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 2: Legal & Regulatory Crawler (output_legal_docs)."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        history_db = self.legal_dir_path / "history.sqlite"
        manifest_json = self.legal_dir_path / "manifest.json"

        if not self.legal_dir_path.exists() or (not history_db.exists() and not manifest_json.exists()):
            return {
                "name": "Legal & Regulatory Crawler",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "total_documents": 0,
                "error": "Directory or files not found",
            }

        hours_since_crawl = 9999.0
        total_docs = 0
        last_crawled_at = None

        try:
            if history_db.exists():
                conn = sqlite3.connect(f"file:{history_db}?mode=ro", uri=True)
                c = conn.cursor()
                c.execute("SELECT MAX(crawled_at), COUNT(*) FROM legal_documents")
                row = c.fetchone()
                if row and row[0]:
                    last_crawled_at = row[0]
                    total_docs = row[1] or 0
                conn.close()

            if (not last_crawled_at or total_docs == 0) and manifest_json.exists():
                with open(manifest_json, "r", encoding="utf-8") as f:
                    m = json.load(f)
                last_crawled_at = m.get("last_updated")
                total_docs = m.get("total_documents", total_docs)

            if last_crawled_at:
                dt_crawled = parse_timestamp(last_crawled_at)
                if dt_crawled:
                    hours_since_crawl = max(0.0, (now_utc - dt_crawled).total_seconds() / 3600.0)

            # Status classification
            if hours_since_crawl <= 24.0:
                status = "HEALTHY"
                score = 100
            elif hours_since_crawl <= 72.0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            return {
                "name": "Legal & Regulatory Crawler",
                "status": status,
                "score": score,
                "hours_since_crawl": round(hours_since_crawl, 1),
                "total_documents": total_docs,
                "last_crawled_at": last_crawled_at,
            }
        except Exception as e:
            logger.error("Legal docs stream check failed: %s", e)
            return {
                "name": "Legal & Regulatory Crawler",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "total_documents": 0,
                "error": str(e),
            }

    def check_stream_3_media_production(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 3: Media Asset Bank 24/7 Producer (daily_media_production.json)."""
        if now is None:
            now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_hour = now.hour

        if not self.media_json_path.exists():
            return {
                "name": "Media Asset Bank 24/7",
                "status": "CRITICAL",
                "score": 0,
                "completed_videos": 0,
                "target_videos": 24,
                "completed_photos": 0,
                "target_photos": 24,
                "current_hour_lag": 24,
                "error": "Tracker file not found",
            }

        try:
            with open(self.media_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            file_date = data.get("date", "")
            target_videos = data.get("target_videos", 24)
            target_photos = data.get("target_photos", 24)
            completed_videos = data.get("completed_videos", 0)
            completed_photos = data.get("completed_photos", 0)

            if file_date != today_str:
                lag = 24
            else:
                expected_so_far = min(24, current_hour)
                lag = max(0, expected_so_far - completed_videos)

            if completed_videos == 0 or lag > 4:
                status = "CRITICAL"
                score = 0
            elif lag >= 2:
                status = "DEGRADED"
                score = 50
            else:
                status = "HEALTHY"
                score = 100

            return {
                "name": "Media Asset Bank 24/7",
                "status": status,
                "score": score,
                "completed_videos": completed_videos,
                "target_videos": target_videos,
                "completed_photos": completed_photos,
                "target_photos": target_photos,
                "current_hour_lag": lag,
                "date": file_date,
            }
        except Exception as e:
            logger.error("Media production stream check failed: %s", e)
            return {
                "name": "Media Asset Bank 24/7",
                "status": "CRITICAL",
                "score": 0,
                "completed_videos": 0,
                "target_videos": 24,
                "completed_photos": 0,
                "target_photos": 24,
                "current_hour_lag": 24,
                "error": str(e),
            }

    def check_stream_4_median_sync(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 4: Median-0 Math Sync (median_hourly_sync.log)."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        if not self.median_log_path.exists():
            return {
                "name": "Median-0 Math Sync",
                "status": "CRITICAL",
                "score": 0,
                "minutes_since_sync": 9999.0,
                "exit_code": 1,
                "checks_count": 0,
                "error": "Log file not found",
            }

        try:
            # Read last 200 lines
            with open(self.median_log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-200:]
            content = "".join(lines)

            # Determine exit code
            exit_code = 0
            if "failed with exit code" in content or "Hourly Sync failed" in content:
                m = re.findall(r"failed with exit code (\d+)", content)
                exit_code = int(m[-1]) if m else 1

            # Checks count: take the latest Checks: N / M line, fallback to generated storyboards count
            checks_count = 0
            m_chk = re.findall(r"Checks:\s*(\d+)", content)
            if m_chk:
                checks_count = int(m_chk[-1])
            else:
                m_gen = re.findall(r"Generated (\d+) new Manim storyboards", content)
                if m_gen:
                    checks_count = int(m_gen[-1])

            # Timestamp: prefer log file mtime as true finish time
            sync_dt = datetime.fromtimestamp(self.median_log_path.stat().st_mtime, tz=timezone.utc)

            minutes_since_sync = max(0.0, (now_utc - sync_dt).total_seconds() / 60.0)

            if minutes_since_sync <= 75.0 and exit_code == 0:
                status = "HEALTHY"
                score = 100
            elif minutes_since_sync <= 180.0 and exit_code == 0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            return {
                "name": "Median-0 Math Sync",
                "status": status,
                "score": score,
                "minutes_since_sync": round(minutes_since_sync, 1),
                "exit_code": exit_code,
                "checks_count": checks_count,
                "last_sync_timestamp": sync_dt.isoformat(),
            }
        except Exception as e:
            logger.error("Median sync stream check failed: %s", e)
            return {
                "name": "Median-0 Math Sync",
                "status": "CRITICAL",
                "score": 0,
                "minutes_since_sync": 9999.0,
                "exit_code": 1,
                "checks_count": 0,
                "error": str(e),
            }

    def check_stream_5_fleet_mesh(self) -> Dict[str, Any]:
        """Stream 5: AGY Fleet & Clef Mesh (REST query to localhost:7777)."""
        active_nodes = 0
        total_nodes = 0
        consensus_score = 0.0
        sla_passed = False

        try:
            req_sum = urllib.request.Request(self.fleet_summary_url, headers={"User-Agent": "HourlyMonitor/1.0"})
            with urllib.request.urlopen(req_sum, timeout=10.0, context=get_ssl_context()) as resp:
                sum_data = json.loads(resp.read().decode("utf-8"))
                active_nodes = sum_data.get("online_nodes") or sum_data.get("active_nodes") or 0
                total_nodes = sum_data.get("total_nodes", 0)

            req_ccl = urllib.request.Request(self.fleet_council_url, headers={"User-Agent": "HourlyMonitor/1.0"})
            with urllib.request.urlopen(req_ccl, timeout=10.0, context=get_ssl_context()) as resp:
                ccl_data = json.loads(resp.read().decode("utf-8"))
                consensus_score = float(
                    ccl_data.get("composite_consensus_score")
                    or ccl_data.get("metrics", {}).get("consensus_score", 0.0)
                )
                sla_passed = bool(ccl_data.get("sla_passed", False))

            if active_nodes >= 15 and consensus_score >= 80.0 and sla_passed:
                status = "HEALTHY"
                score = int(consensus_score)
            elif active_nodes >= 10 and consensus_score >= 60.0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            return {
                "name": "AGY Fleet & Clef Mesh",
                "status": status,
                "score": score,
                "active_nodes": active_nodes,
                "total_nodes": total_nodes,
                "consensus_score": consensus_score,
                "sla_passed": sla_passed,
            }
        except Exception as e:
            logger.warning("Fleet mesh endpoint check failed (daemon may be offline/busy): %s", e)
            return {
                "name": "AGY Fleet & Clef Mesh",
                "status": "CRITICAL",
                "score": 0,
                "active_nodes": 0,
                "total_nodes": 0,
                "consensus_score": 0.0,
                "sla_passed": False,
                "error": str(e),
            }

    def compute_entropy_health_score(self, streams: List[Dict[str, Any]]) -> int:
        """Compute average health score of all 5 entropy streams."""
        if not streams:
            return 0
        total = sum(s.get("score", 0) for s in streams)
        return int(total / len(streams))

    def scan(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Audit all 5 entropy streams and compute entropy health score."""
        s1 = self.check_stream_1_stock_news(now_utc=now_utc)
        s2 = self.check_stream_2_legal_docs(now_utc=now_utc)
        s3 = self.check_stream_3_media_production(now=now_utc)
        s4 = self.check_stream_4_median_sync(now_utc=now_utc)
        s5 = self.check_stream_5_fleet_mesh()

        streams = [s1, s2, s3, s4, s5]
        return {
            "streams": streams,
            "entropy_health_score": self.compute_entropy_health_score(streams),
        }


# ==============================================================================
# 3. CompositeHealthCalculator
# ==============================================================================
class CompositeHealthCalculator:
    """Computes overall weighted health score and severity categorization."""

    @staticmethod
    def calculate(
        cron_score: int,
        entropy_score: int,
        mesh_score: int,
        ticker_score: int,
    ) -> Tuple[int, str]:
        """
        overall_health_score = int(0.35 * cron + 0.35 * entropy + 0.15 * mesh + 0.15 * ticker)
        Severity:
          HEALTHY: >= 85
          WARNING: 60 - 84
          CRITICAL: < 60
        """
        raw = 0.35 * cron_score + 0.35 * entropy_score + 0.15 * mesh_score + 0.15 * ticker_score
        overall = max(0, min(100, int(round(raw))))

        if overall >= 85:
            severity = "HEALTHY"
        elif overall >= 60:
            severity = "WARNING"
        else:
            severity = "CRITICAL"

        return overall, severity


# ==============================================================================
# 4. HermesTelegramNotifier
# ==============================================================================
class HermesTelegramNotifier:
    """Delivers rich HTML alerts and executive hourly digests to Hermes Telegram."""

    def __init__(
        self,
        env_file: Path = DEFAULT_ENV_FILE,
        target_chat_id: str = DEFAULT_CHAT_ID,
        bot_token: Optional[str] = None,
    ):
        self.env_file = Path(env_file)
        self.target_chat_id = target_chat_id
        self.bot_token = bot_token or self._load_token()

    def _load_token(self) -> Optional[str]:
        """Load Telegram bot token from .env file or environment."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("CONTENT_FACTORY_BOT_TOKEN")
        if token:
            return token

        if self.env_file.exists():
            try:
                with open(self.env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k == "TELEGRAM_BOT_TOKEN" and v:
                                return v
                            if k == "CONTENT_FACTORY_BOT_TOKEN" and v and not token:
                                token = v
            except Exception as e:
                logger.error("Failed loading token from %s: %s", self.env_file, e)
        return token

    def _send_payload(self, text: str) -> bool:
        if not self.bot_token:
            logger.error("Cannot send Telegram message: Bot token is missing.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.target_chat_id,
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
                return bool(data.get("ok", False))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            logger.error("Telegram HTTP %s error: %s", e.code, err_body)
            return False
        except Exception as e:
            logger.error("Telegram delivery failed: %s", e)
            return False

    def send_alert(self, alert_text: str) -> bool:
        """Send urgent critical anomaly alert."""
        return self._send_payload(alert_text)

    def send_digest(self, digest_html: str) -> bool:
        """Send standard hourly executive digest."""
        return self._send_payload(digest_html)

    def format_urgent_alert(self, scan_result: Dict[str, Any]) -> str:
        """Format an urgent HTML alert message for CRITICAL anomalies."""
        overall = scan_result.get("overall_health_score", 0)
        severity = scan_result.get("severity", "CRITICAL")
        cron = scan_result.get("cron", {})
        entropy = scan_result.get("entropy", {})

        clogged = cron.get("clogged_jobs", [])
        drifted = cron.get("drift_skipped_jobs", [])
        auth_failed = cron.get("auth_failed_jobs", [])
        ticker = cron.get("ticker_heartbeat", {})

        stalled_streams = [
            s for s in entropy.get("streams", []) if s.get("status") in ("CRITICAL", "DEGRADED")
        ]

        lines = [
            "🚨 <b>[HERMES CRITICAL ALERT] Cron Clog & Entropy Degradation Detected</b>",
            f"<b>Overall Health:</b> <code>{overall}/100</code> [<b>{severity}</b>]",
            "",
        ]

        if clogged:
            lines.append(f"⛔ <b>Clogged Cron Jobs ({len(clogged)}):</b>")
            for c in clogged:
                err = (c.get("last_error") or "").replace("<", "&lt;").replace(">", "&gt;")[:120]
                lines.append(
                    f"• <code>{c.get('job_name')}</code>: {c.get('consecutive_failures')} fails. "
                    f"<i>{err}</i>"
                )
            lines.append("")

        if drifted:
            lines.append(f"⚠️ <b>Drift-Skipped Cron Jobs ({len(drifted)}):</b>")
            for d in drifted:
                lines.append(
                    f"• <code>{d.get('job_name')}</code>: snapshot={d.get('model_snapshot')} "
                    f"(unpinned, silent-skip)"
                )
            lines.append("")

        if auth_failed:
            lines.append(f"🔑 <b>Authentication Failures ({len(auth_failed)}):</b>")
            for a in auth_failed:
                err = (a.get("last_error") or "").replace("<", "&lt;").replace(">", "&gt;")[:100]
                lines.append(f"• <code>{a.get('job_name')}</code>: <i>{err}</i>")
            lines.append("")

        if ticker.get("is_stale"):
            lines.append(f"💓 <b>Stale Ticker Heartbeat:</b> Age <code>{ticker.get('age_seconds')}s</code> (>120s)")
            lines.append("")

        if stalled_streams:
            lines.append(f"🌪️ <b>Degraded / Stalled Entropy Streams ({len(stalled_streams)}):</b>")
            for s in stalled_streams:
                st = s.get("status")
                name = s.get("name")
                if "Stock" in name:
                    lines.append(f"• <b>{name}:</b> {st} ({s.get('hours_since_crawl')}h since crawl)")
                elif "Legal" in name:
                    lines.append(f"• <b>{name}:</b> {st} ({s.get('hours_since_crawl')}h since crawl)")
                elif "Media" in name:
                    lines.append(
                        f"• <b>{name}:</b> {st} ({s.get('completed_videos')}/24 vids, lag {s.get('current_hour_lag')}h)"
                    )
                elif "Median" in name:
                    lines.append(f"• <b>{name}:</b> {st} ({s.get('minutes_since_sync')}m ago, exit {s.get('exit_code')})")
                else:
                    lines.append(f"• <b>{name}:</b> {st}")
            lines.append("")

        lines.append("🛠️ <b>Action Recommended:</b>")
        lines.append("<code>python3 tools/hourly_digest_monitor.py --self-heal</code>")

        return "\n".join(lines)

    def format_hourly_digest(self, scan_result: Dict[str, Any]) -> str:
        """Format clean executive hourly digest dashboard HTML."""
        overall = scan_result.get("overall_health_score", 0)
        severity = scan_result.get("severity", "HEALTHY")
        cron = scan_result.get("cron", {})
        entropy = scan_result.get("entropy", {})

        cron_score = cron.get("cron_health_score", 0)
        entropy_score = entropy.get("entropy_health_score", 0)
        ticker = cron.get("ticker_heartbeat", {})
        ticker_status = "STALE ❌" if ticker.get("is_stale") else "FRESH ✅"

        status_emojis = {
            "HEALTHY": "🟢",
            "WARNING": "🟡",
            "DEGRADED": "🟡",
            "CRITICAL": "🔴",
        }

        sev_emoji = status_emojis.get(severity, "⚪")

        lines = [
            "⚡ <b>[HERMES AGENT] 24/7 Hourly System Digest</b>",
            f"🕒 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            "",
            f"📊 <b>Composite Health:</b> <code>{overall}/100</code> {sev_emoji} [<b>{severity}</b>]",
            f"• Cron Health: <code>{cron_score}%</code>",
            f"• Entropy Streams: <code>{entropy_score}%</code>",
            f"• Ticker Heartbeat: <code>{ticker_status}</code> (age {ticker.get('age_seconds', 0)}s)",
            "",
            "🛰️ <b>External Entropy Streams (5/5):</b>",
        ]

        streams = entropy.get("streams", [])
        for idx, s in enumerate(streams, 1):
            st = s.get("status", "UNKNOWN")
            emoji = status_emojis.get(st, "⚪")
            name = s.get("name")
            if "Stock" in name:
                detail = f"{s.get('hours_since_crawl')}h ago, {s.get('articles_24h')} art/24h, {s.get('unique_symbols')} sym"
            elif "Legal" in name:
                detail = f"{s.get('hours_since_crawl')}h ago, {s.get('total_documents')} docs"
            elif "Media" in name:
                detail = f"{s.get('completed_videos')}/24 vids, {s.get('completed_photos')}/24 photos, lag: {s.get('current_hour_lag')}h"
            elif "Median" in name:
                detail = f"{s.get('minutes_since_sync')}m ago, {s.get('checks_count')} chks, exit: {s.get('exit_code')}"
            elif "Fleet" in name:
                detail = f"{s.get('active_nodes')}/{s.get('total_nodes')} nodes, Clef {s.get('consensus_score')}%, SLA: {'PASS' if s.get('sla_passed') else 'FAIL'}"
            else:
                detail = ""
            lines.append(f"{idx}️⃣ <b>{name}:</b> {emoji} <b>{st}</b> ({detail})")

        lines.append("")
        lines.append("⚙️ <b>Cron Subsystem Diagnostics:</b>")
        lines.append(
            f"• Clogged: <code>{len(cron.get('clogged_jobs', []))}</code> | "
            f"Drift-Skipped: <code>{len(cron.get('drift_skipped_jobs', []))}</code> | "
            f"Overdue: <code>{len(cron.get('overdue_jobs', []))}</code>"
        )
        lines.append(
            f"• Auth Issues: <code>{len(cron.get('auth_failed_jobs', []))}</code> | "
            f"Rate Limits: <code>{len(cron.get('rate_limited_jobs', []))}</code>"
        )

        lines.append("")
        if severity == "HEALTHY":
            lines.append("✅ <b>Status:</b> All sovereign pipelines operating inside nominal bounds.")
        elif severity == "WARNING":
            lines.append("⚠️ <b>Status:</b> Moderate degradation observed. Self-healing advised.")
        else:
            lines.append("🚨 <b>Status:</b> Critical pipeline stall. Proactive intervention in progress.")

        return "\n".join(lines)


# ==============================================================================
# 5. SelfHealingManager
# ==============================================================================
class SelfHealingManager:
    """Automates resolution of drift skips and initiates recovery cycles for stalled streams."""

    def __init__(
        self,
        jobs_path: Path = DEFAULT_JOBS_JSON,
        repo_dir: Path = REPO_ROOT,
        python_bin: Optional[str] = None,
        scripts_dir: Optional[Path] = None,
    ):
        self.jobs_path = Path(jobs_path)
        self.repo_dir = Path(repo_dir)
        venv_py = self.repo_dir / ".venv" / "bin" / "python"
        self.python_bin = python_bin or (str(venv_py) if venv_py.exists() else sys.executable)
        self.scripts_dir = Path(scripts_dir) if scripts_dir else (HERMES_HOME / "scripts")

    def render_wrapper_content(self) -> Tuple[str, str]:
        """
        Renders the canonical bash wrapper content with strict shlex quoting (CWE-78 guard)
        and computes its SHA-256 digest for content-addressed verification.
        """
        repo_dir_q = shlex.quote(str(self.repo_dir))
        python_bin_q = shlex.quote(str(self.python_bin))
        local_bin_q = shlex.quote(str(Path.home() / ".local" / "bin"))

        wrapper_content = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n\n"
            f"REPO_DIR={repo_dir_q}\n"
            'cd "$REPO_DIR"\n'
            f'export PATH={local_bin_q}:"$PATH"\n\n'
            f'exec {python_bin_q} "$REPO_DIR/tools/hourly_digest_monitor.py" --notify --self-heal\n'
        )
        digest = hashlib.sha256(wrapper_content.encode("utf-8")).hexdigest()
        return wrapper_content, digest

    def ensure_wrapper_script(self) -> Tuple[Path, str]:
        """
        Authoritative wrapper creation & reconciliation (CWE-427 / CWE-367 / CWE-78):
        - Never blindly trusts a pre-existing file on disk.
        - Verifies ownership (st_uid == os.getuid()) and exact content match.
        - If stale, missing, or mismatched, atomically replaces with mode 0o700 via tempfile + os.replace.
        - Returns (wrapper_script_path, content_sha256).
        """
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        if not hasattr(os, "O_NOFOLLOW"):
            raise RuntimeError("O_NOFOLLOW unavailable on this platform; refusing to proceed with unprotected scripts_dir open")

        open_flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_DIRECTORY"):
            open_flags |= os.O_DIRECTORY
        if hasattr(os, "O_CLOEXEC"):
            open_flags |= os.O_CLOEXEC

        try:
            dir_fd = os.open(str(self.scripts_dir), open_flags)
        except OSError as exc:
            raise RuntimeError(f"scripts_dir open refused (symlink or non-dir): {self.scripts_dir}: {exc}")

        try:
            st_dir = os.fstat(dir_fd)
            if st_dir.st_uid != os.getuid():
                raise PermissionError(f"scripts_dir not owned by current user: {self.scripts_dir}")
            if st_dir.st_mode & 0o022:
                try:
                    if hasattr(os, "fchmod"):
                        os.fchmod(dir_fd, 0o700)
                    else:
                        os.chmod(self.scripts_dir, 0o700)
                except OSError as exc:
                    raise RuntimeError(f"failed to harden scripts_dir perms, refusing: {self.scripts_dir}: {exc}")
                if os.fstat(dir_fd).st_mode & 0o022:
                    raise RuntimeError(f"scripts_dir still group/world-writable after chmod: {self.scripts_dir}")

            wrapper_name = "hermes_hourly_digest.sh"
            wrapper_content, digest = self.render_wrapper_content()
            data = wrapper_content.encode("utf-8")

            needs_write = True
            try:
                check_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
                file_fd = os.open(wrapper_name, check_flags, dir_fd=dir_fd)
                try:
                    st = os.fstat(file_fd)
                    owned_by_us = (st.st_uid == os.getuid())
                    with open(file_fd, "r", encoding="utf-8", closefd=False) as fh:
                        existing_content = fh.read()
                    content_matches = (existing_content == wrapper_content)
                    needs_write = not (owned_by_us and content_matches)
                finally:
                    os.close(file_fd)
            except OSError:
                needs_write = True

            if needs_write:
                tmp_name = f".{wrapper_name}.tmp.{os.getpid()}_{time.time_ns()}"
                write_flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
                tmp_fd = os.open(tmp_name, write_flags, 0o700, dir_fd=dir_fd)
                try:
                    os.write(tmp_fd, data)
                    try:
                        os.fchmod(tmp_fd, 0o700)
                    except OSError:
                        pass
                    os.fsync(tmp_fd)
                finally:
                    os.close(tmp_fd)

                try:
                    os.replace(tmp_name, wrapper_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                    try:
                        os.fsync(dir_fd)
                    except OSError:
                        pass
                except Exception as exc:
                    try:
                        os.unlink(tmp_name, dir_fd=dir_fd)
                    except OSError:
                        pass
                    logger.error("wrapper self-heal failed for %s: %s", wrapper_name, exc)
                    raise

            wrapper_script = self.scripts_dir / wrapper_name
            return wrapper_script, digest
        finally:
            os.close(dir_fd)

    def self_heal_drift_skips(self) -> List[Dict[str, Any]]:
        """
        Un-wedges drift-skipped cron jobs:
        - Pins model: 'codex', provider: 'custom'
        - Pins model_snapshot: 'codex', provider_snapshot: 'custom'
        - Resets drift_alerted: False
        - Clears last_error if drift_skip
        - Reconciles canonical procedural wrapper script against disk
        """
        # Reconcile wrapper script against canonical procedural memory (CWE-427 / CWE-367)
        try:
            self.ensure_wrapper_script()
        except Exception as e:
            logger.warning("Failed reconciling wrapper script during self-heal: %s", e)

        if not self.jobs_path.exists():
            return []

        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            jobs = data.get("jobs", []) if isinstance(data, dict) else data
            healed = []

            for j in jobs:
                if not isinstance(j, dict):
                    continue
                last_err = str(j.get("last_error") or "")
                drift_alerted = bool(j.get("drift_alerted"))
                is_drift_error = "[drift_skip" in last_err

                # Check if job is unpinned or drifted
                if drift_alerted or is_drift_error or j.get("model_snapshot") == "cx/gpt-5.6-luna":
                    j["model"] = "codex"
                    j["provider"] = "custom"
                    j["model_snapshot"] = "codex"
                    j["provider_snapshot"] = "custom"
                    j["drift_alerted"] = False

                    if is_drift_error:
                        j["last_error"] = None
                        if j.get("last_status") == "error":
                            j["last_status"] = "scheduled"

                    healed.append(
                        {
                            "id": j.get("id"),
                            "name": j.get("name"),
                            "model": j["model"],
                            "provider": j["provider"],
                        }
                    )

            if healed:
                if isinstance(data, dict):
                    data["updated_at"] = datetime.now(timezone.utc).isoformat()
                # Atomic write
                tmp_path = self.jobs_path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                tmp_path.replace(self.jobs_path)
                logger.info("Successfully self-healed %d drift-skipped jobs.", len(healed))

            return healed
        except Exception as e:
            logger.error("Failed self-healing drift skips: %s", e)
            return []

    def trigger_entropy_recovery(self, stream: str) -> Dict[str, Any]:
        """Trigger on-demand execution cycle for stalled entropy sources."""
        results = {"stream": stream, "success": False, "returncode": -1, "output": ""}

        cmd: List[str] = []
        if stream == "stock_news":
            script = self.repo_dir / "skills" / "finance" / "vietnam-stock-daily-brief" / "news_monitor.py"
            cmd = [self.python_bin, str(script), "--scan"]
        elif stream == "legal_docs":
            script = self.repo_dir / "skills" / "research" / "vietnam-legal-crawler" / "crawler.py"
            out_dir = self.repo_dir / "output_legal_docs"
            cmd = [self.python_bin, str(script), "-o", str(out_dir), "--limit", "5", "--no-attachments"]
        elif stream == "media_production":
            script = self.repo_dir / "skills" / "creative" / "media-asset-bank" / "hourly_producer.py"
            cmd = [self.python_bin, str(script), "--run-once"]
        elif stream == "median_sync":
            script = self.repo_dir / "scripts" / "median_cron_hourly.sh"
            cmd = ["/usr/bin/env", "bash", str(script)]
        else:
            results["error"] = f"Unknown stream: {stream}"
            return results

        try:
            logger.info("Triggering recovery for stream '%s': %s", stream, " ".join(cmd))
            proc = subprocess.run(
                cmd,
                cwd=str(self.repo_dir),
                capture_output=True,
                text=True,
                timeout=180,
            )
            results["returncode"] = proc.returncode
            results["success"] = proc.returncode == 0
            results["output"] = (proc.stdout + "\n" + proc.stderr).strip()[-500:]
        except Exception as e:
            results["error"] = str(e)
            logger.error("Recovery execution failed for '%s': %s", stream, e)

        return results

    def install_hourly_cron(self) -> Dict[str, Any]:
        """Register the 24/7 hourly digest monitor in Hermes Cron."""
        if not self.jobs_path.exists():
            return {"status": "error", "error": "jobs.json not found"}

        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            job_id = "job_hermes_hourly_digest"
            jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]

            script_path = self.repo_dir / "tools" / "hourly_digest_monitor.py"
            cmd = f"{self.python_bin} {script_path} --notify --self-heal"

            # Ensure wrapper script in scripts dir exists and is verified
            wrapper_script, wrapper_sha256 = self.ensure_wrapper_script()

            digest_job = {
                "id": job_id,
                "name": "hermes-hourly-digest-and-entropy-monitor",
                "prompt": "",
                "skills": [],
                "skill": None,
                "model": "codex",
                "provider": "custom",
                "provider_snapshot": "custom",
                "model_snapshot": "codex",
                "base_url": None,
                "script": wrapper_script.name,
                "script_sha256": wrapper_sha256,
                "command": cmd,
                "workdir": str(self.repo_dir),
                "no_agent": True,
                "schedule": {
                    "kind": "cron",
                    "expr": "0 * * * *",
                    "display": "0 * * * * (Hourly 24/7 Digest & Anomaly Monitor)",
                },
                "schedule_display": "0 * * * *",
                "repeat": {"times": None, "completed": 0},
                "enabled": True,
                "state": "scheduled",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "next_run_at": datetime.now(timezone.utc).isoformat(),
                "last_status": "ok",
                "drift_alerted": False,
            }

            jobs_list.append(digest_job)
            data["jobs"] = jobs_list
            data["updated_at"] = datetime.now(timezone.utc).isoformat()

            tmp_path = self.jobs_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(self.jobs_path)

            return {
                "status": "installed",
                "job_id": job_id,
                "command": cmd,
                "script": wrapper_script.name,
                "script_sha256": wrapper_sha256,
            }
        except Exception as e:
            logger.error("Failed installing hourly digest cron: %s", e)
            return {"status": "error", "error": str(e)}

    def uninstall_hourly_cron(self) -> Dict[str, Any]:
        """Remove the 24/7 hourly digest monitor from Hermes Cron."""
        if not self.jobs_path.exists():
            return {"status": "error", "error": "jobs.json not found"}

        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            job_id = "job_hermes_hourly_digest"
            jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]
            data["jobs"] = jobs_list
            data["updated_at"] = datetime.now(timezone.utc).isoformat()

            tmp_path = self.jobs_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(self.jobs_path)

            return {"status": "uninstalled", "job_id": job_id}
        except Exception as e:
            logger.error("Failed uninstalling hourly digest cron: %s", e)
            return {"status": "error", "error": str(e)}


# ==============================================================================
# Main Orchestrator & CLI
# ==============================================================================
def run_full_scan(
    cron_detector: Optional[CronAnomalyDetector] = None,
    entropy_detector: Optional[EntropyDegradationDetector] = None,
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Execute complete system scan across Cron, Entropy streams, and Mesh."""
    cron_det = cron_detector or CronAnomalyDetector()
    entropy_det = entropy_detector or EntropyDegradationDetector()

    cron_findings = cron_det.scan(now_utc=now_utc)
    entropy_findings = entropy_det.scan(now_utc=now_utc)

    cron_score = cron_findings.get("cron_health_score", 0)
    entropy_score = entropy_findings.get("entropy_health_score", 0)

    # Mesh score from Stream 5
    mesh_stream = next(
        (s for s in entropy_findings.get("streams", []) if "Fleet" in s.get("name", "")),
        {},
    )
    mesh_score = mesh_stream.get("score", 0)

    # Ticker score
    ticker = cron_findings.get("ticker_heartbeat", {})
    ticker_score = 0 if ticker.get("is_stale") else 100

    overall_score, severity = CompositeHealthCalculator.calculate(
        cron_score=cron_score,
        entropy_score=entropy_score,
        mesh_score=mesh_score,
        ticker_score=ticker_score,
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_health_score": overall_score,
        "severity": severity,
        "cron": cron_findings,
        "entropy": entropy_findings,
        "mesh_score": mesh_score,
        "ticker_score": ticker_score,
    }


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent 24/7 Hourly Monitor & Anomaly Detector")
    parser.add_argument("--scan", action="store_true", help="Run full scan and output JSON summary")
    parser.add_argument("--notify", action="store_true", help="Send Telegram Hourly Digest Report")
    parser.add_argument("--alert-only", action="store_true", help="Send Telegram alert only if CRITICAL anomalies exist")
    parser.add_argument("--self-heal", action="store_true", help="Run automated self-healing for drift-skips")
    parser.add_argument("--recover-stream", type=str, help="Trigger on-demand recovery for a stalled entropy stream")
    parser.add_argument("--install-cron", action="store_true", help="Register 24/7 hourly digest monitor in Hermes Cron")
    parser.add_argument("--uninstall-cron", action="store_true", help="Remove 24/7 hourly digest monitor from Hermes Cron")
    args = parser.parse_args()

    notifier = HermesTelegramNotifier()
    healer = SelfHealingManager()

    if args.install_cron:
        res = healer.install_hourly_cron()
        print(f"[+] Install hourly cron result: {res}")
        return

    if args.uninstall_cron:
        res = healer.uninstall_hourly_cron()
        print(f"[+] Uninstall hourly cron result: {res}")
        return

    # Default action if no flags provided: scan
    if not (args.scan or args.notify or args.alert_only or args.self_heal or args.recover_stream):
        args.scan = True

    if args.self_heal:
        print("[*] Initiating Self-Healing for Drift-Skipped Cron Jobs...")
        healed = healer.self_heal_drift_skips()
        print(f"[+] Self-healed {len(healed)} jobs:")
        for h in healed:
            print(f"    - {h.get('name')} ({h.get('id')}) -> model={h.get('model')}, provider={h.get('provider')}")

    if args.recover_stream:
        print(f"[*] Triggering recovery for entropy stream: {args.recover_stream}...")
        rec = healer.trigger_entropy_recovery(args.recover_stream)
        print(f"[+] Result: success={rec.get('success')}, code={rec.get('returncode')}")

    scan_result = run_full_scan()

    if args.scan:
        print(json.dumps(scan_result, indent=2))

    if args.alert_only:
        if scan_result.get("severity") == "CRITICAL":
            alert_msg = notifier.format_urgent_alert(scan_result)
            print("[*] CRITICAL anomalies detected. Sending Urgent Alert to Telegram...")
            sent = notifier.send_alert(alert_msg)
            print(f"[+] Telegram alert delivery status: {'SUCCESS' if sent else 'FAILED'}")
        else:
            print(f"[*] Health is {scan_result.get('severity')}. No urgent alert needed.")

    if args.notify:
        digest_msg = notifier.format_hourly_digest(scan_result)
        print("[*] Sending Hourly Digest to Telegram...")
        sent = notifier.send_digest(digest_msg)
        print(f"[+] Telegram digest delivery status: {'SUCCESS' if sent else 'FAILED'}")


if __name__ == "__main__":
    main()
