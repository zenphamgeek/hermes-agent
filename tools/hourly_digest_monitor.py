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
from contextlib import contextmanager
import errno
try:
    import fcntl
except ImportError:
    fcntl = None
import hashlib
import html
import json
import logging
import math
import os
import re
import secrets
import shlex
import sqlite3
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hourly_digest_monitor")

def _safe_hermes_home() -> Path:
    env_h = os.environ.get("HERMES_HOME")
    if env_h:
        return Path(env_h)
    try:
        return Path.home() / ".hermes"
    except Exception:
        return Path(os.environ.get("HOME", "/tmp")) / ".hermes"

HERMES_HOME = _safe_hermes_home()
REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_EXECUTIONS_DB = HERMES_HOME / "cron" / "executions.db"
DEFAULT_JOBS_JSON = HERMES_HOME / "cron" / "jobs.json"
DEFAULT_TICKER_HEARTBEAT = HERMES_HOME / "cron" / "ticker_heartbeat"
DEFAULT_CIRCUIT_STATE_FILE = HERMES_HOME / "cron" / ".circuit_breaker.json"

DEFAULT_STOCK_DB = HERMES_HOME / "stock_news_memory.sqlite"
DEFAULT_LEGAL_DIR = REPO_ROOT / "output_legal_docs"
DEFAULT_MEDIA_JSON = HERMES_HOME / "daily_media_production.json"
DEFAULT_MEDIAN_LOG = REPO_ROOT / "assets" / "scripts_video" / "logs" / "median_hourly_sync.log"

DEFAULT_ENV_FILE = HERMES_HOME / ".env"
DEFAULT_CHAT_ID = "1431349185"

FLEET_SUMMARY_URL = "http://localhost:7777/api/fleet/summary"
FLEET_COUNCIL_URL = "http://localhost:7777/api/fleet/council"

_FATAL_TEMP_ERRNOS = frozenset({
    errno.ENOSPC,
    getattr(errno, "EDQUOT", 122),
    errno.EROFS,
    errno.EACCES,
    errno.EPERM,
    getattr(errno, "ENAMETOOLONG", 36),
    errno.EMFILE,
    errno.ENFILE,
    getattr(errno, "ELOOP", 40),
})


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

    _URL_CRED_PATTERN = re.compile(
        r"(?P<scheme>[a-z][a-z0-9+.\-]*://[^:@/\s]+:)(?:[^@/\s]+)(?P<at>@)",
        re.I,
    )
    _KV_SECRET_PATTERN = re.compile(
        r"(?i)\b(?P<k>password|passwd|secret|api[_-]?key|client[_-]?secret)(?P<sep>\s*[:=]\s*)(?:[\"']?[^\s,;'\"}]+[\"']?)"
    )
    _PEM_KEY_PATTERN = re.compile(
        r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"
    )
    _SECRET_PATTERNS = (
        re.compile(r"\bBearer\s+[A-Za-z0-9._\-/+=]{10,}", re.I),
        re.compile(r"\bya29\.[A-Za-z0-9._\-/+=]+", re.I),
        re.compile(r"\b1//[A-Za-z0-9._\-/+=]+", re.I),
        re.compile(r"\b[0-9]{6,}:[A-Za-z0-9_\-]{30,}\b"),
        re.compile(r"\b(?:access|refresh|id)[_-]?token\s*[:=]?\s*[A-Za-z0-9._\-/+=]+", re.I),
        re.compile(r"\beyJ[A-Za-z0-9._\-/+=]{20,}"),
        re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
        re.compile(r"\b(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b"),
        re.compile(r"\bxox[baprs]-[0-9A-Za-z]{10,48}\b"),
    )

    @classmethod
    def redact_secrets(cls, text: Any) -> str:
        """Best-effort redaction of bearer tokens, OAuth credentials, keys, passwords, and JWTs from error strings (CWE-532 / CWE-259)."""
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        if not text:
            return ""
        text = cls._PEM_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", text)
        text = cls._URL_CRED_PATTERN.sub(r"\g<scheme>[REDACTED]\g<at>", text)
        text = cls._KV_SECRET_PATTERN.sub(r"\g<k>\g<sep>[REDACTED]", text)
        for pat in cls._SECRET_PATTERNS:
            text = pat.sub("[REDACTED]", text)
        return text

    @classmethod
    def sanitize_error(cls, text: Any, limit: int = 120) -> str:
        """Sanitize error string: type-coerce, redact secrets, truncate, and HTML-escape (CWE-532 / CWE-116)."""
        if text is None:
            raw = ""
        elif not isinstance(text, str):
            raw = str(text)
        else:
            raw = text
        redacted = cls.redact_secrets(raw)
        truncated = redacted[:limit] if limit is not None and limit >= 0 else redacted
        return html.escape(truncated, quote=True)

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
            "🚨 <b>[HERMES CRITICAL ALERT] Cron Clog &amp; Entropy Degradation Detected</b>",
            f"<b>Overall Health:</b> <code>{overall}/100</code> [<b>{severity}</b>]",
            "",
        ]

        if clogged:
            lines.append(f"⛔ <b>Clogged Cron Jobs ({len(clogged)}):</b>")
            for c in clogged:
                job_name = html.escape(str(c.get("job_name", "")))
                err = self.sanitize_error(c.get("last_error"), limit=120)
                lines.append(
                    f"• <code>{job_name}</code>: {c.get('consecutive_failures')} fails. "
                    f"<i>{err}</i>"
                )
            lines.append("")

        if drifted:
            lines.append(f"⚠️ <b>Drift-Skipped Cron Jobs ({len(drifted)}):</b>")
            for d in drifted:
                job_name = html.escape(str(d.get("job_name", "")))
                snap = html.escape(str(d.get("model_snapshot", "")))
                lines.append(
                    f"• <code>{job_name}</code>: snapshot={snap} "
                    f"(unpinned, silent-skip)"
                )
            lines.append("")

        if auth_failed:
            lines.append(f"🔑 <b>Authentication Failures ({len(auth_failed)}):</b>")
            for a in auth_failed:
                job_name = html.escape(str(a.get("job_name", "")))
                err = self.sanitize_error(a.get("last_error"), limit=100)
                lines.append(f"• <code>{job_name}</code>: <i>{err}</i>")
            lines.append("")

        if ticker.get("is_stale"):
            lines.append(f"💓 <b>Stale Ticker Heartbeat:</b> Age <code>{ticker.get('age_seconds')}s</code> (>120s)")
            lines.append("")

        if stalled_streams:
            lines.append(f"🌪️ <b>Degraded / Stalled Entropy Streams ({len(stalled_streams)}):</b>")
            for s in stalled_streams:
                st = html.escape(str(s.get("status", "")))
                name = html.escape(str(s.get("name", "")))
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
            raw_st = s.get("status", "UNKNOWN")
            emoji = status_emojis.get(raw_st, "⚪")
            st = html.escape(str(raw_st))
            raw_name = str(s.get("name", ""))
            name = html.escape(raw_name)
            if "Stock" in raw_name:
                detail = f"{s.get('hours_since_crawl')}h ago, {s.get('articles_24h')} art/24h, {s.get('unique_symbols')} sym"
            elif "Legal" in raw_name:
                detail = f"{s.get('hours_since_crawl')}h ago, {s.get('total_documents')} docs"
            elif "Media" in raw_name:
                detail = f"{s.get('completed_videos')}/24 vids, {s.get('completed_photos')}/24 photos, lag: {s.get('current_hour_lag')}h"
            elif "Median" in raw_name:
                detail = f"{s.get('minutes_since_sync')}m ago, {s.get('checks_count')} chks, exit: {s.get('exit_code')}"
            elif "Fleet" in raw_name:
                detail = f"{s.get('active_nodes')}/{s.get('total_nodes')} nodes, Clef {s.get('consensus_score')}%, SLA: {'PASS' if s.get('sla_passed') else 'FAIL'}"
            else:
                detail = ""
            detail_escaped = html.escape(detail)
            lines.append(f"{idx}️⃣ <b>{name}:</b> {emoji} <b>{st}</b> ({detail_escaped})")

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

    _wrapper_failures: int = 0
    _wrapper_circuit_open_until: float = 0.0
    _wrapper_circuit_open_until_mono: float = 0.0
    _wrapper_circuit_reason: Optional[str] = None
    _ledger_epoch: int = 0
    _circuit_lock: threading.RLock = threading.RLock()
    _flock_depth: int = 0
    _flock_fd: Optional[int] = None
    _circuit_state_file: Optional[Path] = DEFAULT_CIRCUIT_STATE_FILE
    CIRCUIT_COOLDOWN_SECONDS: float = 300.0  # 5 minutes
    _MAX_CIRCUIT_WINDOW_S: float = 15.0 * 60.0  # 15 minutes max window (CWE-20/377 DoS defense)
    _CORRUPT_FAILSAFE_HOLD_S: float = 30.0  # 30 seconds conservative hold on corrupt ledger (CWE-20/754 defense)
    _MAX_QUARANTINE_ARTIFACTS: int = 5  # Bound quarantine set to prevent disk/inode exhaustion (CWE-400)
    _warned_no_fcntl: bool = False
    CIRCUIT_MAX_FAILURES: int = 3
    TEMP_MAX_RETRIES: int = 5

    @classmethod
    def _token_source(cls, nbytes: int = 16) -> str:
        """Cryptographically secure pseudorandom token generator (CSPRNG, CWE-330)."""
        return secrets.token_hex(nbytes)

    @classmethod
    def _epoch_marker_file(cls) -> Optional[Path]:
        """Returns path to persistent epoch marker file."""
        if cls._circuit_state_file:
            return cls._circuit_state_file.parent / f".{cls._circuit_state_file.name}.epoch"
        return None

    @classmethod
    def _sync_epoch_to_disk(cls) -> None:
        """Persists generation counter epoch to disk (atomic replace, mode 0o600)."""
        epoch_path = cls._epoch_marker_file()
        if not epoch_path:
            return
        try:
            epoch_path.parent.mkdir(parents=True, exist_ok=True)
            token = cls._token_source(6)
            tmp_epoch = epoch_path.parent / f".{epoch_path.name}.tmp.{token}"
            o_nofollow = getattr(os, "O_NOFOLLOW", 0) or 0
            o_cloexec = getattr(os, "O_CLOEXEC", 0) or 0
            write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | o_nofollow | o_cloexec
            fd = os.open(str(tmp_epoch), write_flags, 0o600)
            try:
                try:
                    os.fchmod(fd, 0o600)
                except OSError:
                    pass
                os.write(fd, str(cls._ledger_epoch).encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(str(tmp_epoch), str(epoch_path))
        except OSError:
            pass

    @classmethod
    def _load_epoch_from_disk(cls) -> None:
        """Loads generation counter epoch from disk if marker exists."""
        epoch_path = cls._epoch_marker_file()
        if epoch_path and epoch_path.exists():
            try:
                with open(epoch_path, "r", encoding="utf-8") as fh:
                    val = int(fh.read().strip())
                    if val > cls._ledger_epoch:
                        cls._ledger_epoch = val
            except (ValueError, OSError):
                pass

    @classmethod
    @contextmanager
    def _ledger_lock_ctx(cls):
        """
        Context manager for acquiring both in-process RLock and cross-process advisory fcntl.flock (CWE-362).
        Lock file is created with O_CREAT | os.O_RDWR | O_NOFOLLOW | O_CLOEXEC, mode 0o600.
        """
        with cls._circuit_lock:
            need_flock_close = False
            if fcntl is None:
                if not cls._warned_no_fcntl:
                    logger.warning(
                        json.dumps({
                            "event": "flock_unavailable",
                            "warning": "fcntl module unavailable on platform; cross-process ledger advisory flock is disabled (relying on atomic temp+replace and in-process RLock)",
                            "ts": time.time(),
                        })
                    )
                    cls._warned_no_fcntl = True
            elif cls._flock_depth == 0 and cls._circuit_state_file:
                lock_path = cls._circuit_state_file.parent / f"{cls._circuit_state_file.name}.lock"
                try:
                    cls._circuit_state_file.parent.mkdir(parents=True, exist_ok=True)
                    o_nofollow = getattr(os, "O_NOFOLLOW", 0) or 0
                    o_cloexec = getattr(os, "O_CLOEXEC", 0) or 0
                    open_flags = os.O_CREAT | os.O_RDWR | o_nofollow | o_cloexec
                    cls._flock_fd = os.open(str(lock_path), open_flags, 0o600)
                    try:
                        st = os.fstat(cls._flock_fd)
                        if st.st_mode & 0o022:
                            os.fchmod(cls._flock_fd, 0o600)
                    except OSError:
                        pass
                    fcntl.flock(cls._flock_fd, fcntl.LOCK_EX)
                    need_flock_close = True
                except OSError as exc:
                    logger.warning("Could not acquire advisory flock on %s: %s", lock_path, exc)
                    if cls._flock_fd is not None:
                        try:
                            os.close(cls._flock_fd)
                        except OSError:
                            pass
                        cls._flock_fd = None

            cls._flock_depth += 1
            try:
                yield
            finally:
                cls._flock_depth -= 1
                if cls._flock_depth == 0 and need_flock_close and cls._flock_fd is not None:
                    try:
                        fcntl.flock(cls._flock_fd, fcntl.LOCK_UN)
                    except OSError:
                        pass
                    try:
                        os.close(cls._flock_fd)
                    except OSError:
                        pass
                    cls._flock_fd = None

    @classmethod
    def _with_ledger_lock(cls, fn=None):
        """
        Executes fn under cross-process advisory flock and thread lock, or returns context manager.
        """
        ctx = cls._ledger_lock_ctx()
        if fn is None:
            return ctx
        with ctx:
            return fn()

    @classmethod
    def _quarantine_corrupt_ledger(cls, target: Path, now: float, reason_key: str, exc: Optional[Exception] = None) -> None:
        """
        Quarantines a corrupt or malformed circuit breaker ledger (CWE-20/CWE-754/CWE-400 DoS defense).
        - Content-addressed via SHA-256: collapses repeated identical corruptions to a single artifact.
        - Ring buffer eviction bounded by _MAX_QUARANTINE_ARTIFACTS to prevent disk/inode exhaustion.
        - Atomically renames target to .{name}.corrupt.{digest} so subsequent reads don't infinitely loop holds.
        """
        cls._ledger_epoch += 1
        cls._sync_epoch_to_disk()
        quarantined = False
        deduplicated = False
        quarantine_target = None

        poison_bytes = b""
        if target.exists():
            try:
                poison_bytes = target.read_bytes()
            except OSError:
                poison_bytes = str(now).encode("utf-8")

        digest = hashlib.sha256(poison_bytes).hexdigest()[:32]
        quarantine_target = target.with_name(f".{target.name}.corrupt.{digest}")

        try:
            if quarantine_target.exists():
                # Identical poison content already quarantined: dedup and unlink
                target.unlink(missing_ok=True)
                quarantined = True
                deduplicated = True
            else:
                os.replace(str(target), str(quarantine_target))
                try:
                    os.chmod(quarantine_target, 0o600)
                except OSError:
                    pass
                quarantined = True
        except OSError:
            try:
                target.unlink(missing_ok=True)
                quarantined = True
            except OSError:
                pass

        # Ring buffer eviction: bound total quarantine artifacts to _MAX_QUARANTINE_ARTIFACTS
        try:
            parent = target.parent
            prefix = f".{target.name}.corrupt."
            artifacts = [
                p for p in parent.iterdir()
                if p.is_file() and p.name.startswith(prefix)
            ]
            if len(artifacts) > cls._MAX_QUARANTINE_ARTIFACTS:
                artifacts.sort(key=lambda p: (p.stat().st_mtime, p.name))
                to_evict = artifacts[:-cls._MAX_QUARANTINE_ARTIFACTS]
                for old_art in to_evict:
                    try:
                        old_art.unlink(missing_ok=True)
                        logger.info(
                            json.dumps({
                                "event": "quarantine_evicted",
                                "evicted": str(old_art),
                                "max_artifacts": cls._MAX_QUARANTINE_ARTIFACTS,
                                "ts": now,
                            })
                        )
                    except OSError:
                        pass
        except OSError:
            pass

        logger.warning(
            json.dumps({
                "event": "circuit_ledger_corrupt",
                "target": str(target),
                "quarantined": quarantined,
                "deduplicated": deduplicated,
                "quarantine_target": str(quarantine_target) if quarantined else None,
                "error": type(exc).__name__ if exc else reason_key,
                "hold_s": cls._CORRUPT_FAILSAFE_HOLD_S,
                "epoch": cls._ledger_epoch,
                "ts": now,
            })
        )

    @classmethod
    def _load_circuit_ledger(cls, path: Optional[Path] = None, now: Optional[float] = None) -> Tuple[bool, float, int, Optional[str]]:
        """
        Loads and validates persistent circuit breaker ledger (CWE-20 / CWE-377 / CWE-754):
        - When file exists but is corrupt, unreadable, non-dict, or type-confused:
          Quarantines the corrupted file (atomic rename to .{name}.corrupt.{ts}.{token}) and
          applies a one-shot bounded conservative hold (_CORRUPT_FAILSAFE_HOLD_S = 30.0s).
          This prevents attackers from resetting active cooldowns AND prevents infinite rolling DoS (Finding 1).
        - Clamps circuit_open_until exceeding now + _MAX_CIRCUIT_WINDOW_S to prevent permanent DoS wedging.
        - Sanitizes reason field (CWE-117) to printable characters and max 256 bytes.
        - Rejects NaN, Inf, and non-numeric values via math.isfinite.
        - Tracks monotonically increasing epoch generation counter.
        - Returns (is_open, circuit_open_until, failures, reason).
        """
        target = Path(path) if path else cls._circuit_state_file
        if not target or not target.exists():
            return False, 0.0, 0, None

        if now is None:
            now = time.time()
        try:
            with open(target, "r", encoding="utf-8") as fh:
                state = json.load(fh)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            cls._quarantine_corrupt_ledger(target, now, type(exc).__name__, exc=exc)
            return True, now + cls._CORRUPT_FAILSAFE_HOLD_S, cls.CIRCUIT_MAX_FAILURES, f"corrupt_ledger_hold_{type(exc).__name__}"

        if not isinstance(state, dict):
            cls._quarantine_corrupt_ledger(target, now, "type_confusion_not_dict")
            return True, now + cls._CORRUPT_FAILSAFE_HOLD_S, cls.CIRCUIT_MAX_FAILURES, "type_confusion_hold_not_dict"

        raw_open = state.get("circuit_open_until")
        if not isinstance(raw_open, (int, float)) or isinstance(raw_open, bool) or not math.isfinite(raw_open):
            cls._quarantine_corrupt_ledger(target, now, "invalid_expiry")
            return True, now + cls._CORRUPT_FAILSAFE_HOLD_S, cls.CIRCUIT_MAX_FAILURES, "invalid_expiry_hold"

        ledger_epoch = state.get("epoch", 0)
        if isinstance(ledger_epoch, int) and ledger_epoch > cls._ledger_epoch:
            cls._ledger_epoch = ledger_epoch

        failures = state.get("failures", cls.CIRCUIT_MAX_FAILURES)
        if not isinstance(failures, int) or isinstance(failures, bool):
            failures = cls.CIRCUIT_MAX_FAILURES

        raw_open = float(raw_open)
        max_allowed = now + cls._MAX_CIRCUIT_WINDOW_S
        if raw_open > max_allowed:
            clamped = max_allowed
            logger.warning(
                json.dumps({
                    "event": "circuit_ledger_window_clamped",
                    "raw_open_until": raw_open,
                    "clamped_open_until": clamped,
                    "max_window_s": cls._MAX_CIRCUIT_WINDOW_S,
                    "ts": now,
                })
            )
            cooldown = clamped
        else:
            cooldown = raw_open

        # Sanitize reason field (CWE-117)
        raw_reason = str(state.get("reason", "unknown"))[:256]
        clean_reason = "".join(ch for ch in raw_reason if ch.isprintable()) or "unknown"

        if now < cooldown:
            return True, cooldown, failures, clean_reason

        return False, 0.0, failures, None

    @classmethod
    def set_circuit_state_file(cls, path: Optional[Path]) -> None:
        """Override persistent circuit breaker ledger path (for test isolation)."""
        with cls._with_ledger_lock():
            cls._circuit_state_file = Path(path) if path else None
            cls._load_epoch_from_disk()

    @classmethod
    def reset_circuit_breaker(cls) -> None:
        """Reset circuit breaker counters and cooldown (both in-memory and persistent ledger)."""
        with cls._with_ledger_lock():
            cls._wrapper_failures = 0
            cls._wrapper_circuit_open_until = 0.0
            cls._wrapper_circuit_open_until_mono = 0.0
            cls._wrapper_circuit_reason = None
            cls._ledger_epoch += 1
            cls._sync_epoch_to_disk()
            if cls._circuit_state_file and cls._circuit_state_file.exists():
                try:
                    cls._circuit_state_file.unlink()
                except OSError:
                    pass

    @classmethod
    def _trip_circuit_breaker(cls, reason: str, errno_val: Optional[int] = None) -> None:
        """Trip circuit breaker with persistent ledger (CWE-362 / cron-cadence DoS defense)."""
        with cls._with_ledger_lock():
            cls._ledger_epoch += 1
            cls._sync_epoch_to_disk()
            now = time.time()
            now_mono = time.monotonic()
            cls._wrapper_circuit_open_until = now + cls.CIRCUIT_COOLDOWN_SECONDS
            cls._wrapper_circuit_open_until_mono = now_mono + cls.CIRCUIT_COOLDOWN_SECONDS
            clean_reason = "".join(ch for ch in str(reason)[:256] if ch.isprintable()) or "unknown"
            cls._wrapper_circuit_reason = clean_reason
            if cls._circuit_state_file:
                try:
                    cls._circuit_state_file.parent.mkdir(parents=True, exist_ok=True)
                    state = {
                        "epoch": cls._ledger_epoch,
                        "tripped_at": now,
                        "circuit_open_until": cls._wrapper_circuit_open_until,
                        "failures": cls._wrapper_failures,
                        "errno": errno_val,
                        "reason": clean_reason,
                    }
                    # Atomic publish: temp file + os.replace to prevent partial-write corruption
                    token = cls._token_source(8)
                    tmp_state_file = cls._circuit_state_file.parent / f".{cls._circuit_state_file.name}.tmp.{token}"
                    o_nofollow = getattr(os, "O_NOFOLLOW", 0) or 0
                    o_cloexec = getattr(os, "O_CLOEXEC", 0) or 0
                    write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | o_nofollow | o_cloexec
                    fd = os.open(str(tmp_state_file), write_flags, 0o600)
                    try:
                        try:
                            os.fchmod(fd, 0o600)
                        except OSError:
                            pass
                        data = json.dumps(state).encode("utf-8")
                        os.write(fd, data)
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                    os.replace(str(tmp_state_file), str(cls._circuit_state_file))
                except OSError as exc:
                    logger.warning("Could not persist circuit breaker ledger: %s", exc)

    @classmethod
    def get_circuit_status(cls) -> Dict[str, Any]:
        """Thread-safe snapshot of circuit breaker status (checking memory and persistent ledger)."""
        with cls._with_ledger_lock():
            now = time.time()
            now_mono = time.monotonic()
            is_open_mono = (
                cls._wrapper_circuit_open_until_mono > 0.0
                and now_mono < cls._wrapper_circuit_open_until_mono
            )
            is_open_wall = (now < cls._wrapper_circuit_open_until)
            is_open = is_open_mono or is_open_wall
            reason = cls._wrapper_circuit_reason if is_open else None

            # Check persistent ledger
            if cls._circuit_state_file:
                l_open, l_cooldown, l_failures, l_reason = cls._load_circuit_ledger(cls._circuit_state_file, now=now)
                if l_open:
                    cls._wrapper_circuit_open_until = l_cooldown
                    cls._wrapper_circuit_open_until_mono = now_mono + max(0.0, l_cooldown - now)
                    cls._wrapper_failures = l_failures
                    cls._wrapper_circuit_reason = l_reason
                    is_open = True
                    reason = l_reason

            cooldown_rem = 0.0
            if is_open:
                if cls._wrapper_circuit_open_until_mono > 0.0:
                    cooldown_rem = max(
                        cls._wrapper_circuit_open_until_mono - now_mono,
                        cls._wrapper_circuit_open_until - now,
                        0.0,
                    )
                else:
                    cooldown_rem = max(0.0, cls._wrapper_circuit_open_until - now)

            return {
                "failures": cls._wrapper_failures,
                "circuit_open_until": cls._wrapper_circuit_open_until,
                "is_open": is_open,
                "cooldown_remaining": cooldown_rem,
                "reason": reason,
                "epoch": cls._ledger_epoch,
            }

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
        Includes self-verification against companion manifest before execution (A6).
        """
        repo_dir_q = shlex.quote(str(self.repo_dir))
        python_bin_q = shlex.quote(str(self.python_bin))
        try:
            _h = Path.home()
            local_bin_path = str(_h / ".local" / "bin")
        except Exception:
            local_bin_path = "/usr/local/bin"
        local_bin_q = shlex.quote(local_bin_path)

        wrapper_name = "hermes_hourly_digest.sh"
        manifest_name = f".{wrapper_name}.manifest"

        wrapper_content = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n\n"
            'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
            f'MANIFEST="$SCRIPT_DIR/{manifest_name}"\n'
            'if [ -f "$MANIFEST" ]; then\n'
            '    (cd "$SCRIPT_DIR" && sha256sum -c "$MANIFEST" --status) || {\n'
            '        echo "FATAL: Wrapper script SHA-256 integrity verification failed against manifest!" >&2\n'
            '        exit 1\n'
            '    }\n'
            'fi\n\n'
            f"REPO_DIR={repo_dir_q}\n"
            'cd "$REPO_DIR"\n'
            f'export PATH={local_bin_q}:"$PATH"\n\n'
            f'exec {python_bin_q} "$REPO_DIR/tools/hourly_digest_monitor.py" --notify --self-heal\n'
        )
        digest = hashlib.sha256(wrapper_content.encode("utf-8")).hexdigest()
        return wrapper_content, digest

    def _resolve_scripts_dir_fd(self) -> int:
        """
        Creates or opens scripts_dir component-by-component, anchored to each parent's
        fd with O_NOFOLLOW | O_DIRECTORY (CWE-367 / CWE-427 / CWE-59).
        Refusal originates directly from ELOOP/ENOTDIR on O_NOFOLLOW without prior lstat.
        Fails closed with RuntimeError if O_NOFOLLOW is unsupported on platform.
        Caller owns the returned fd and must os.close() it.
        """
        o_nofollow = getattr(os, "O_NOFOLLOW", None)
        if not o_nofollow:
            raise RuntimeError(
                "O_NOFOLLOW unavailable on this platform; refusing to resolve scripts_dir without symlink protection (CWE-59 fail-closed)"
            )

        d = Path(os.path.abspath(str(self.scripts_dir)))
        root = d.anchor or "/"
        cloexec = getattr(os, "O_CLOEXEC", 0)
        open_flags = os.O_RDONLY | os.O_DIRECTORY | o_nofollow | cloexec

        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | cloexec)
        cur_fd = root_fd
        parts = d.parts[1:]

        try:
            for comp in parts:
                try:
                    nxt = os.open(comp, open_flags, dir_fd=cur_fd)
                except FileNotFoundError:
                    os.mkdir(comp, mode=0o700, dir_fd=cur_fd)
                    nxt = os.open(comp, open_flags, dir_fd=cur_fd)
                except OSError as exc:
                    if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                        logger.error(
                            json.dumps({
                                "event": "scripts_dir_symlink_refused",
                                "component": str(comp),
                                "scripts_dir": str(self.scripts_dir),
                                "euid": os.geteuid(),
                                "ts": time.time(),
                            })
                        )
                        if comp == parts[-1]:
                            raise RuntimeError(f"scripts_dir open refused (symlink or non-dir): {self.scripts_dir}") from exc
                        else:
                            raise RuntimeError(f"scripts_dir ancestor is a symlink, refusing: {comp}") from exc
                    raise
                if cur_fd != root_fd:
                    os.close(cur_fd)
                cur_fd = nxt
            return cur_fd
        except Exception:
            if cur_fd != root_fd:
                os.close(cur_fd)
            os.close(root_fd)
            raise

    def _create_exclusive_temp(
        self, dir_fd: int, base_name: str, data: bytes, is_executable: bool = False
    ) -> str:
        """
        Creates an unpredictable, exclusive temporary file (CWE-340 / CWE-377 / CWE-494 / CWE-59)
        with 128-bit cryptographic randomness (secrets.token_hex(16)).
        Fails closed if O_NOFOLLOW is unavailable.
        Retries up to TEMP_MAX_RETRIES ONLY on FileExistsError (EEXIST). Fatal errnos (ENOSPC, EACCES, EMFILE)
        fail immediately with structured SIEM event 'temp_create_fatal_errno' to prevent amplification DoS.
        Writes data, fchmods to 0o700 if is_executable else 0o600, fsyncs, and closes fd.
        Returns the relative temporary file name.
        """
        o_nofollow = getattr(os, "O_NOFOLLOW", None)
        if not o_nofollow:
            raise RuntimeError(
                "O_NOFOLLOW unavailable on this platform; refusing to create wrapper temp without symlink protection (CWE-59 fail-closed)"
            )

        write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | o_nofollow | getattr(os, "O_CLOEXEC", 0)
        mode = 0o600
        target_mode = 0o700 if is_executable else 0o600

        last_exc: Optional[Exception] = None
        for attempt in range(self.TEMP_MAX_RETRIES):
            token = self._token_source(16)
            tmp_name = f".{base_name}.tmp.{token}"
            try:
                tmp_fd = os.open(tmp_name, write_flags, mode, dir_fd=dir_fd)
            except OSError as exc:
                if exc.errno == errno.EEXIST or isinstance(exc, FileExistsError):
                    last_exc = exc
                    logger.warning(
                        json.dumps({
                            "event": "temp_collision_retry",
                            "base_name": base_name,
                            "tmp_name": tmp_name,
                            "attempt": attempt + 1,
                            "max_retries": self.TEMP_MAX_RETRIES,
                            "ts": time.time(),
                        })
                    )
                    continue
                # Fatal errno (ENOSPC, EACCES, EMFILE, ELOOP, EROFS, etc. in _FATAL_TEMP_ERRNOS) are NOT collisions — fail closed immediately without retrying!
                logger.error(
                    json.dumps({
                        "event": "temp_create_fatal_errno",
                        "base_name": base_name,
                        "tmp_name": tmp_name,
                        "errno": exc.errno,
                        "strerror": str(exc),
                        "attempt": attempt + 1,
                        "ts": time.time(),
                    })
                )
                raise

            # Successfully created and opened exclusive temp fd
            try:
                os.write(tmp_fd, data)
                if target_mode != mode:
                    try:
                        os.fchmod(tmp_fd, target_mode)
                    except OSError:
                        pass
                os.fsync(tmp_fd)
            finally:
                os.close(tmp_fd)
            return tmp_name

        # All retries exhausted -> fail closed with structured SIEM audit log
        logger.error(
            json.dumps({
                "event": "temp_create_exhausted",
                "base_name": base_name,
                "max_retries": self.TEMP_MAX_RETRIES,
                "ts": time.time(),
            })
        )
        if last_exc:
            raise last_exc
        raise RuntimeError(f"Failed creating exclusive temp file for {base_name} after {self.TEMP_MAX_RETRIES} attempts")

    def ensure_wrapper_script(self) -> Tuple[Path, str]:
        """
        Authoritative wrapper creation & reconciliation (CWE-427 / CWE-367 / CWE-78 / CWE-494 / CWE-362 / CWE-59):
        - Component-by-component O_NOFOLLOW directory resolution eliminates TOCTOU races (fail-closed if O_NOFOLLOW missing).
        - Verifies ownership (st_uid == os.geteuid()) and directory permissions (mode & 0o022 == 0).
        - Hardens temp creation with unpredictable secrets.token_hex(16) and bounded retries against DoS.
        - Content-addressed SHA-256 verification and companion .manifest generation for runtime invocation lock.
        - Thread-safe circuit breaker preventing cascading failure storms under outages.
        - Returns (wrapper_script_path, content_sha256).
        """
        o_nofollow = getattr(os, "O_NOFOLLOW", None)
        if not o_nofollow:
            raise RuntimeError(
                "O_NOFOLLOW unavailable on this platform; refusing to inspect scripts without symlink protection (CWE-59 fail-closed)"
            )

        now = time.time()
        now_mono = time.monotonic()
        with SelfHealingManager._with_ledger_lock():
            if SelfHealingManager._circuit_state_file:
                l_open, l_cooldown, l_failures, l_reason = SelfHealingManager._load_circuit_ledger(
                    SelfHealingManager._circuit_state_file,
                    now=now,
                )
                if l_open:
                    SelfHealingManager._wrapper_circuit_open_until = l_cooldown
                    SelfHealingManager._wrapper_circuit_open_until_mono = now_mono + max(0.0, l_cooldown - now)
                    SelfHealingManager._wrapper_failures = l_failures
                    SelfHealingManager._wrapper_circuit_reason = l_reason
                    remaining = int(max(0.0, l_cooldown - now))
                    raise RuntimeError(
                        f"Wrapper reconciliation circuit breaker OPEN (cooling down for {remaining}s after persistent failure: {l_reason or 'unknown'})"
                    )

            is_open_mono = (
                SelfHealingManager._wrapper_circuit_open_until_mono > 0.0
                and now_mono < SelfHealingManager._wrapper_circuit_open_until_mono
            )
            is_open_wall = (now < SelfHealingManager._wrapper_circuit_open_until)
            if is_open_mono or is_open_wall:
                remaining = int(
                    max(
                        SelfHealingManager._wrapper_circuit_open_until_mono - now_mono,
                        SelfHealingManager._wrapper_circuit_open_until - now,
                        0.0,
                    )
                )
                reason_detail = SelfHealingManager._wrapper_circuit_reason
                if reason_detail and ("hold" in reason_detail or "corrupt" in reason_detail or "type_confusion" in reason_detail):
                    raise RuntimeError(
                        f"Wrapper reconciliation circuit breaker OPEN (cooling down for {remaining}s after persistent failure: {reason_detail})"
                    )
                raise RuntimeError(
                    f"Wrapper reconciliation circuit breaker OPEN (cooling down for {remaining}s after repeated failures)"
                )

        try:
            dir_fd = self._resolve_scripts_dir_fd()
            try:
                st_dir = os.fstat(dir_fd)
                if st_dir.st_uid != os.geteuid():
                    raise PermissionError(f"scripts_dir not owned by current user (euid {os.geteuid()}, owner {st_dir.st_uid}): {self.scripts_dir}")
                if st_dir.st_mode & 0o022:
                    logger.info(
                        json.dumps({
                            "event": "scripts_dir_mode_hardened",
                            "scripts_dir": str(self.scripts_dir),
                            "orig_mode": oct(st_dir.st_mode),
                            "target_mode": oct(0o700),
                            "ts": time.time(),
                        })
                    )
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
                manifest_name = f".{wrapper_name}.manifest"
                wrapper_content, digest = self.render_wrapper_content()
                data = wrapper_content.encode("utf-8")
                manifest_content = f"{digest}  {wrapper_name}\n"
                manifest_data = manifest_content.encode("utf-8")

                needs_write = True
                try:
                    check_flags = os.O_RDONLY | o_nofollow | getattr(os, "O_CLOEXEC", 0)
                    file_fd = os.open(wrapper_name, check_flags, dir_fd=dir_fd)
                    try:
                        st = os.fstat(file_fd)
                        if st.st_mode & 0o022:
                            try:
                                os.fchmod(file_fd, 0o700)
                            except OSError:
                                pass
                        owned_by_us = (st.st_uid == os.geteuid())
                        with open(file_fd, "r", encoding="utf-8", closefd=False) as fh:
                            existing_content = fh.read()
                        content_matches = (existing_content == wrapper_content)
                        if not content_matches:
                            logger.warning(
                                json.dumps({
                                    "event": "wrapper_tamper_detected",
                                    "wrapper_name": wrapper_name,
                                    "action": "republish_authoritative",
                                    "ts": time.time(),
                                })
                            )
                        needs_write = not (owned_by_us and content_matches)
                        if not needs_write and (os.fstat(file_fd).st_mode & 0o022):
                            needs_write = True
                    finally:
                        os.close(file_fd)
                except OSError:
                    needs_write = True

                needs_manifest_write = True
                try:
                    check_flags = os.O_RDONLY | o_nofollow | getattr(os, "O_CLOEXEC", 0)
                    m_fd = os.open(manifest_name, check_flags, dir_fd=dir_fd)
                    try:
                        st_m = os.fstat(m_fd)
                        if st_m.st_mode & 0o022:
                            try:
                                os.fchmod(m_fd, 0o600)
                            except OSError:
                                pass
                        with open(m_fd, "r", encoding="utf-8", closefd=False) as fh:
                            existing_m = fh.read()
                        needs_manifest_write = (existing_m != manifest_content)
                        if not needs_manifest_write and (os.fstat(m_fd).st_mode & 0o022):
                            needs_manifest_write = True
                    finally:
                        os.close(m_fd)
                except OSError:
                    needs_manifest_write = True

                if not needs_write and needs_manifest_write:
                    # Crash recovery / self-healing: wrapper matches canonical template, reconcile companion manifest
                    tmp_m = self._create_exclusive_temp(
                        dir_fd=dir_fd,
                        base_name=manifest_name,
                        data=manifest_data,
                        is_executable=False,
                    )
                    try:
                        os.replace(tmp_m, manifest_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                        try:
                            os.fsync(dir_fd)
                        except OSError:
                            pass
                    except Exception as exc:
                        try:
                            os.unlink(tmp_m, dir_fd=dir_fd)
                        except OSError:
                            pass
                        logger.error("manifest self-heal failed for %s: %s", manifest_name, exc)
                        raise
                elif needs_write:
                    # Full publication: prepare and fsync BOTH temp files before replacing either (CWE-494 / crash transactionality)
                    tmp_w = self._create_exclusive_temp(
                        dir_fd=dir_fd,
                        base_name=wrapper_name,
                        data=data,
                        is_executable=True,
                    )
                    try:
                        tmp_m = self._create_exclusive_temp(
                            dir_fd=dir_fd,
                            base_name=manifest_name,
                            data=manifest_data,
                            is_executable=False,
                        )
                    except Exception:
                        try:
                            os.unlink(tmp_w, dir_fd=dir_fd)
                        except OSError:
                            pass
                        raise

                    tmp_w_replaced = False
                    tmp_m_replaced = False
                    try:
                        os.replace(tmp_w, wrapper_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                        tmp_w_replaced = True
                        try:
                            os.fsync(dir_fd)
                        except OSError:
                            pass

                        os.replace(tmp_m, manifest_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                        tmp_m_replaced = True
                        try:
                            os.fsync(dir_fd)
                        except OSError:
                            pass
                    except Exception as exc:
                        if not tmp_w_replaced:
                            try:
                                os.unlink(tmp_w, dir_fd=dir_fd)
                            except OSError:
                                pass
                        if not tmp_m_replaced:
                            try:
                                os.unlink(tmp_m, dir_fd=dir_fd)
                            except OSError:
                                pass
                        logger.error("wrapper atomic publication failed: %s", exc)
                        raise

                with SelfHealingManager._with_ledger_lock():
                    SelfHealingManager._wrapper_failures = 0
                    SelfHealingManager._wrapper_circuit_open_until = 0.0
                    SelfHealingManager._wrapper_circuit_open_until_mono = 0.0
                    SelfHealingManager._wrapper_circuit_reason = None
                    if SelfHealingManager._circuit_state_file and SelfHealingManager._circuit_state_file.exists():
                        try:
                            SelfHealingManager._circuit_state_file.unlink()
                        except OSError:
                            pass
                wrapper_script = self.scripts_dir / wrapper_name
                return wrapper_script, digest
            finally:
                os.close(dir_fd)
        except Exception as exc:
            with SelfHealingManager._with_ledger_lock():
                SelfHealingManager._wrapper_failures += 1
                if SelfHealingManager._wrapper_failures >= SelfHealingManager.CIRCUIT_MAX_FAILURES:
                    now = time.time()
                    if SelfHealingManager._wrapper_circuit_open_until <= now:
                        reason = f"{type(exc).__name__}: {exc}"
                        exc_errno = getattr(exc, "errno", None)
                        SelfHealingManager._trip_circuit_breaker(reason=reason, errno_val=exc_errno)
                        logger.warning(
                            "Wrapper reconciliation circuit breaker TRIPPED (cooldown %ds, persistent ledger saved) after %d failures: %s",
                            int(SelfHealingManager.CIRCUIT_COOLDOWN_SECONDS),
                            SelfHealingManager._wrapper_failures,
                            exc,
                        )
            raise

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
