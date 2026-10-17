#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_fleet_council_adversarial_stress.py
==============================================
Adversarial Stress Test Harness for tools/fleet_council_dispatcher.py.

Evaluates:
1. Concurrency & ThreadPool Stress:
   - High-load parallel dispatches (32-64 tasks) across mock nodes.
   - Thread safety of FleetClient and CacheManager under concurrent multi-threaded execution.
2. Network Chaos & Flakiness:
   - Burst HTTP 429 (Rate Limit) and HTTP 503 (Service Unavailable) recovering via jittered backoff.
   - Socket Timeout and ConnectionReset recovering on retry.
   - Unrecoverable network errors triggering FleetUnreachableError (Exit Code 3).
   - Quota exhaustion triggering QuotaStarvationError (Exit Code 4).
   - EMPIRICAL DEFECT PROOFS:
     * Status API failure raising uncaught CouncilExecutionError (crash instead of Exit Code 3).
     * Quota-exhausted nodes falsely treated as available due to missing status check.
     * Zero quota float evaluation bug (0.0 or 1.0 -> 1.0).
     * Job polling network drop escaping polling loop.
3. Cache Corruption Resistance:
   - Truncated (0-byte) cache file recovery as cache miss.
   - Corrupted JSON syntax recovery as cache miss.
   - Read-only cache file (0o444) handling without crash.
   - EMPIRICAL DEFECT PROOF: Valid JSON with corrupted schema ({}, []) causing unhandled TypeError crash.
"""

from __future__ import annotations

import concurrent.futures
import io
import json
import os
from pathlib import Path
import random
import sys
import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from tools.fleet_council_dispatcher import (
    COUNCIL_ROLES,
    DEFAULT_CACHE_DIR,
    DEFAULT_FLEET_URL,
    DEFAULT_TIMEOUT,
    CacheManager,
    CouncilExecutionError,
    CouncilRoleConfig,
    DeliberationReport,
    DeliberationSynthesizer,
    DispatcherCLI,
    FleetClient,
    FleetUnreachableError,
    MemberDeliberation,
    NodeInfo,
    QuotaStarvationError,
    RubricScorecard,
    VetoFailureError,
)

# Standard mock 8-node cluster
MOCK_8_NODES = [
    NodeInfo(name="ultra-2", tier="ultra", status="idle", account_email="u2@test.com", preferred_model="claude-opus-4-6-thinking"),
    NodeInfo(name="pro-1", tier="ultra", status="idle", account_email="p1@test.com", preferred_model="gemini-4-argon-high"),
    NodeInfo(name="node-4", tier="pro", status="idle", account_email="n4@test.com", preferred_model="gemini-4-argon-high"),
    NodeInfo(name="node-5", tier="pro", status="idle", account_email="n5@test.com", preferred_model="gemini-4-argon-high"),
    NodeInfo(name="node-6", tier="pro", status="idle", account_email="n6@test.com", preferred_model="gemini-4-argon-high"),
    NodeInfo(name="node-7", tier="pro", status="idle", account_email="n7@test.com", preferred_model="gemini-4-argon-high"),
    NodeInfo(name="node-8", tier="pro", status="idle", account_email="n8@test.com", preferred_model="gemini-4-argon-high"),
    NodeInfo(name="team-3", tier="pro", status="idle", account_email="t3@test.com", preferred_model="gemini-4-argon-high"),
]


# ===========================================================================
# 1. Concurrency & ThreadPool Stress Tests
# ===========================================================================

def test_concurrency_high_load_parallel_dispatches():
    """Stress test FleetClient.run_parallel under high volume (48 concurrent tasks)."""
    client = FleetClient(max_retries=2, timeout=10.0)

    task_count = 48
    tasks = [
        {
            "role_id": f"role_{i % 8}",
            "node_name": f"node_{i % 8}",
            "prompt": f"Stress prompt payload {i} with extensive synthetic context data " * 10,
            "model": "gemini-4-argon-high",
            "cache_key": f"stress_key_{i}",
        }
        for i in range(task_count)
    ]

    completed_counter = 0
    lock = threading.Lock()

    def mock_run_task(node_name: str, prompt: str, model: str | None = None, timeout: float = 10.0):
        nonlocal completed_counter
        # Introduce micro-jitter to provoke race conditions
        time.sleep(random.uniform(0.005, 0.02))
        with lock:
            completed_counter += 1
        return {
            "status": "completed",
            "clean_response": f"### 1. Assessment: APPROVED\nHigh-load response for {node_name}\n### 6. Score: 3.8",
            "total_tokens": 150,
            "cost_saved_usd": 0.002,
        }

    with patch.object(client, "run_task", side_effect=mock_run_task):
        start = time.time()
        results = client.run_parallel(tasks, timeout=10.0)
        duration = time.time() - start

        assert len(results) == task_count
        assert completed_counter == task_count
        assert duration < 5.0  # Must complete rapidly via ThreadPool parallelism

        # Verify no data corruption across returned task payloads
        for idx, res in enumerate(results):
            assert "job_result" in res
            assert res["job_result"]["status"] == "completed"
            assert res["cache_key"].startswith("stress_key_")


def test_concurrency_multi_threaded_fleet_client_invocations():
    """Verify thread-safety when multiple threads invoke FleetClient methods simultaneously."""
    client = FleetClient(max_retries=2, timeout=5.0)
    num_threads = 12
    barrier = threading.Barrier(num_threads)
    results_list: list[dict[str, Any]] = []
    errors: list[Exception] = []

    def worker_thread(thread_idx: int):
        barrier.wait()  # Synchronize start to maximize concurrency
        subtasks = [
            {"role_id": f"t_{thread_idx}_r_{j}", "node_name": f"node_{j}", "prompt": f"p_{j}"}
            for j in range(4)
        ]
        try:
            with patch.object(client, "run_task", return_value={"status": "completed", "response": f"done_{thread_idx}"}):
                res = client.run_parallel(subtasks, timeout=5.0)
                results_list.extend(res)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results_list) == num_threads * 4


def test_concurrency_cache_manager_multithreaded_read_write(tmp_path: Path):
    """Stress test CacheManager under heavy simultaneous multi-threaded read and write traffic."""
    cache_mgr = CacheManager(cache_dir=tmp_path, enabled=True)
    num_threads = 16
    operations_per_thread = 50
    barrier = threading.Barrier(num_threads)
    thread_errors: list[Exception] = []

    def hammer_cache(worker_id: int):
        barrier.wait()
        # Half keys are shared, half are thread-private
        for i in range(operations_per_thread):
            key = f"shared_key_{i % 5}" if worker_id % 2 == 0 else f"worker_{worker_id}_key_{i}"
            payload = {
                "role_id": f"worker_{worker_id}",
                "role_title": "Tester",
                "node_name": "node-4",
                "tier": "pro",
                "model": "flash",
                "score": 3.5,
                "verdict": "APPROVED",
                "critique": f"Stress test data payload cycle {i}",
                "directives": ["Keep running"],
            }
            try:
                if i % 3 == 0:
                    cache_mgr.put(key, payload)
                else:
                    _ = cache_mgr.get(key)
            except Exception as exc:
                thread_errors.append(exc)

    threads = [threading.Thread(target=hammer_cache, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # CacheManager must NOT raise unhandled exceptions during concurrent access
    assert len(thread_errors) == 0


# ===========================================================================
# 2. Network Chaos & Flakiness Tests
# ===========================================================================

def test_network_chaos_burst_429_503_recovers_with_backoff():
    """Verify jittered exponential backoff recovers when server bursts 429 then 503 then 200 OK."""
    client = FleetClient(base_url="http://localhost:7777", max_retries=4)

    err_429 = urllib.error.HTTPError(
        url="http://localhost:7777/api/fleet/health",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=io.BytesIO(b"Rate limit exceeded"),
    )
    err_503 = urllib.error.HTTPError(
        url="http://localhost:7777/api/fleet/health",
        code=503,
        msg="Service Unavailable",
        hdrs={},
        fp=io.BytesIO(b"Node Busy"),
    )

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"status": "ok", "nodes": 8}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    call_seq = [err_429, err_503, mock_resp]
    sleep_calls: list[float] = []

    def mock_urlopen(req, timeout):
        res = call_seq.pop(0)
        if isinstance(res, Exception):
            raise res
        return res

    with patch("urllib.request.urlopen", side_effect=mock_urlopen), \
         patch("time.sleep", side_effect=lambda d: sleep_calls.append(d)):
        data = client._request("/api/fleet/health", method="GET", retries=4)

        assert data == {"status": "ok", "nodes": 8}
        assert len(sleep_calls) == 2
        # Backoff attempt 0: ~1.0 + jitter, attempt 1: ~2.0 + jitter
        assert sleep_calls[0] >= 1.0
        assert sleep_calls[1] >= 2.0


def test_network_chaos_socket_timeout_recovers_with_backoff():
    """Verify socket TimeoutError on early attempts recovers on subsequent retry."""
    client = FleetClient(base_url="http://localhost:7777", max_retries=3)

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"status": "ok"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    call_count = 0
    sleep_calls: list[float] = []

    def mock_urlopen(req, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("Socket timed out waiting for headers")
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen), \
         patch("time.sleep", side_effect=lambda d: sleep_calls.append(d)):
        data = client._request("/api/fleet/health", method="GET", retries=3)

        assert data == {"status": "ok"}
        assert call_count == 2
        assert len(sleep_calls) == 1


def test_network_chaos_connection_reset_recovers_with_backoff():
    """Verify ConnectionResetError recovers on subsequent retry."""
    client = FleetClient(base_url="http://localhost:7777", max_retries=3)

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"status": "ok"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    call_count = 0

    def mock_urlopen(req, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionResetError("Connection reset by peer")
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen), \
         patch("time.sleep"):
        data = client._request("/api/fleet/health", method="GET", retries=3)

        assert data == {"status": "ok"}
        assert call_count == 2


def test_network_chaos_unreachable_fleet_health_exits_code_3():
    """Verify that unrecoverable network outage on health check returns POSIX exit code 3."""
    with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError("Connection refused")), \
         patch("time.sleep"):
        exit_code = DispatcherCLI.run(["--topic", "Test Chaos", "--dry-run"])
        assert exit_code == 3


def test_quota_starvation_all_nodes_error_exits_code_4():
    """Verify that when all nodes have status 'error', QuotaStarvationError triggers exit code 4."""
    error_nodes = [
        NodeInfo(name=f"node-{i}", tier="ultra" if i < 2 else "pro", status="error", account_email="", preferred_model="")
        for i in range(8)
    ]
    with patch.object(FleetClient, "get_health", return_value={"status": "ok", "nodes": 8}), \
         patch.object(FleetClient, "get_status", return_value=error_nodes):
        exit_code = DispatcherCLI.run(["--topic", "Test Starvation", "--dry-run"])
        assert exit_code == 4


# ===========================================================================
# 3. Cache Corruption Resistance Tests
# ===========================================================================

def test_cache_corruption_truncated_zero_bytes_recovers_as_miss(tmp_path: Path):
    """Verify truncated (0-byte) cache file is handled gracefully and treated as cache miss."""
    cache_mgr = CacheManager(cache_dir=tmp_path, enabled=True)
    key = cache_mgr.compute_hash("math_core", "Test Topic", "Script", "model")
    cache_file = tmp_path / f"{key}.json"

    # Create empty 0-byte cache file
    cache_file.write_text("", encoding="utf-8")
    assert cache_file.stat().st_size == 0

    # Must return None without raising exception
    result = cache_mgr.get(key)
    assert result is None


def test_cache_corruption_malformed_json_syntax_recovers_as_miss(tmp_path: Path):
    """Verify corrupted JSON syntax is caught and treated as cache miss."""
    cache_mgr = CacheManager(cache_dir=tmp_path, enabled=True)
    key = cache_mgr.compute_hash("math_core", "Test Topic", "Script", "model")
    cache_file = tmp_path / f"{key}.json"

    # Write broken syntax
    cache_file.write_text('{"role_id": "math_core", "critique": "incomplete... ', encoding="utf-8")

    result = cache_mgr.get(key)
    assert result is None


def test_cache_corruption_read_only_cache_file_graceful_warning(tmp_path: Path):
    """Verify put() to a read-only cache file (0o444) does not crash."""
    cache_mgr = CacheManager(cache_dir=tmp_path, enabled=True)
    key = "readonly_key"
    cache_file = tmp_path / f"{key}.json"
    cache_file.write_text('{"initial": "content"}', encoding="utf-8")

    # Make file read-only
    os.chmod(cache_file, 0o444)
    try:
        # Should log warning, not raise PermissionError
        cache_mgr.put(key, {"new": "data"})
    finally:
        os.chmod(cache_file, 0o644)  # restore for cleanup


def test_cache_corruption_unreadable_cache_file_returns_none(tmp_path: Path):
    """Verify get() on an unreadable cache file (0o000) does not crash and returns None."""
    cache_mgr = CacheManager(cache_dir=tmp_path, enabled=True)
    key = "unreadable_key"
    cache_file = tmp_path / f"{key}.json"
    cache_file.write_text('{"secret": "data"}', encoding="utf-8")

    os.chmod(cache_file, 0o000)
    try:
        val = cache_mgr.get(key)
        assert val is None
    finally:
        os.chmod(cache_file, 0o644)


# ===========================================================================
# 4. EMPIRICAL DEFECT PROOFS (Adversarial Findings)
# ===========================================================================

def test_DEFECT_status_api_http_error_causes_unhandled_crash():
    """
    REMEDIATION VERIFICATION #1:
    When /api/fleet/status fails with HTTP 503 or 429 after retries,
    FleetClient.get_status() wraps CouncilExecutionError into FleetUnreachableError,
    which DispatcherCLI.run() catches and returns exit code 3 cleanly.
    """
    with patch.object(FleetClient, "get_health", return_value={"status": "ok", "nodes": 8}):
        with patch.object(
            FleetClient,
            "_request",
            side_effect=CouncilExecutionError("Fleet HTTP error 503 on /api/fleet/status: Service Unavailable"),
        ):
            exit_code = DispatcherCLI.run(["--topic", "Test Status Failure", "--dry-run"])
            assert exit_code == 3


def test_DEFECT_corrupted_cache_schema_causes_unhandled_typeerror_crash(tmp_path: Path):
    """
    REMEDIATION VERIFICATION #2:
    When a cache file contains valid JSON with a malformed schema (e.g. empty dict {} or array []),
    DispatcherCLI.run() catches (TypeError, KeyError, ValueError, AttributeError),
    logs a warning, and treats it as a cache miss, falling back to executing the task!
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cm = CacheManager(cache_dir=cache_dir)

    # Compute key for math_core
    key = cm.compute_hash("math_core", "Test Topic", "", "claude-opus-4-6-thinking")
    # Corrupt schema: valid JSON dict, but missing required attributes
    (cache_dir / f"{key}.json").write_text("{}", encoding="utf-8")

    with patch.object(FleetClient, "get_health", return_value={"status": "ok", "nodes": 8}), \
         patch.object(FleetClient, "allocate_nodes", return_value={"math_core": MOCK_8_NODES[0]}), \
         patch.object(FleetClient, "run_parallel", return_value=[{
             "role_id": "math_core",
             "cache_key": key,
             "job_result": {
                 "status": "completed",
                 "clean_response": "### 1. Assessment: APPROVED\n### 6. Score: 3.8",
                 "total_tokens": 100,
                 "cost_saved_usd": 0.001,
             }
         }]):

        exit_code = DispatcherCLI.run([
            "--topic", "Test Topic",
            "-r", "math_core",
            "--cache-dir", str(cache_dir),
            "-o", str(tmp_path / "out.md"),
        ])

        assert exit_code == 0
        assert (tmp_path / "out.md").exists()


def test_DEFECT_quota_exhausted_nodes_falsely_allocated():
    """
    REMEDIATION VERIFICATION #3:
    In FleetClient.allocate_nodes(), nodes with status == 'quota_exhausted'
    are properly filtered out. When insufficient active nodes remain,
    it raises QuotaStarvationError.
    """
    client = FleetClient()

    # Cluster where ultra-2 is quota_exhausted and pro-1 is idle
    # If 2 ultra roles are requested, it raises QuotaStarvationError!
    exhausted_cluster = [
        NodeInfo(name="ultra-2", tier="ultra", status="quota_exhausted", account_email="u2@test.com", preferred_model="opus"),
        NodeInfo(name="pro-1", tier="ultra", status="idle", account_email="p1@test.com", preferred_model="flash"),
    ] + MOCK_8_NODES[2:]  # 6 pro nodes

    with patch.object(client, "get_status", return_value=exhausted_cluster):
        with pytest.raises(QuotaStarvationError):
            client.allocate_nodes(["math_core", "synthesis"])


def test_DEFECT_zero_quota_fraction_falsely_evaluated_as_100_percent():
    """
    REMEDIATION VERIFICATION #4:
    In NodeInfo.from_dict():
        gemini_quota_fraction=float(g_q) if g_q is not None else 1.0
    0.0 is preserved as 0.0 instead of being overwritten to 1.0!
    """
    node_data = {
        "name": "node-exhausted",
        "tier": "pro",
        "status": "idle",
        "gemini_quota_fraction": 0.0,
        "claude_quota_fraction": 0.0,
    }
    node = NodeInfo.from_dict(node_data)
    assert node.gemini_quota_fraction == 0.0
    assert node.claude_quota_fraction == 0.0


def test_DEFECT_job_polling_network_drop_escapes_polling_loop():
    """
    REMEDIATION VERIFICATION #5:
    In FleetClient.run_task(), the job polling loop catches both
    CouncilExecutionError and FleetUnreachableError, allowing transient socket
    disconnects to retry on subsequent intervals without aborting prematurely.
    """
    client = FleetClient(timeout=30.0)

    # First call: submit job -> returns job_id 'job_123'
    # Second call (poll attempt 1): transient network drop -> raises FleetUnreachableError
    # Third call (poll attempt 2): completes successfully!
    call_count = 0

    def mock_request(endpoint, method="GET", data=None, retries=3):
        nonlocal call_count
        call_count += 1
        if endpoint == "/api/fleet/run":
            return {"job_id": "job_123"}
        elif endpoint == "/api/fleet/jobs/job_123":
            if call_count == 2:
                # Transient network drop during polling
                raise FleetUnreachableError("Connection dropped during poll")
            return {"status": "completed", "clean_response": "done"}
        return {}

    with patch.object(client, "_request", side_effect=mock_request), \
         patch("time.sleep"):
        res = client.run_task(node_name="node-4", prompt="test prompt", timeout=30.0)

        assert res["status"] == "completed"
        assert res["clean_response"] == "done"
        assert call_count >= 3

