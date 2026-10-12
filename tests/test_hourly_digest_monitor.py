"""
Test Suite for Hermes Agent 24/7 Hourly Digest Monitor, Cronjob Clog & Anomaly Detector,
Entropy Stream Degradation Scanner, Composite Health Calculator, and Self-Healing Engine.
"""

import json
import shlex
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


