"""
Comprehensive Unit & Integration Test Suite for Sovereign Victory Critic & Anti-Fake-Pass Engine
(`tools/sovereign_victory_critic.py`) and Hourly Digest Telemetry Integration.
"""

import ast
import json
import sqlite3
from pathlib import Path

import pytest

from tools.hourly_digest_monitor import (
    HermesTelegramNotifier,
    format_markdown_report,
)
from tools.sovereign_victory_critic import (
    CANONICAL_ARGON_MODELS,
    SovereignVictoryCritic,
    main as critic_main,
    normalize_argon_model_slug,
)


def test_normalize_argon_model_slug_three_levels():
    assert normalize_argon_model_slug("gemini-3.8-flash-high") == "gemini-4-argon-high"
    assert normalize_argon_model_slug("gemini-3.8-flash-medium") == "gemini-4-argon-medium"
    assert normalize_argon_model_slug("gemini-3.8-flash-low") == "gemini-4-argon-low"
    assert normalize_argon_model_slug("gemini-3.8-flash") == "gemini-4-argon-high"
    assert normalize_argon_model_slug("gemini-3-8-flash-high") == "gemini-4-argon-high"
    assert normalize_argon_model_slug("gemini-3-8-flash-medium") == "gemini-4-argon-medium"
    assert normalize_argon_model_slug("gemini-3-8-flash-low") == "gemini-4-argon-low"
    assert normalize_argon_model_slug("") == "gemini-4-argon-high"
    assert normalize_argon_model_slug(None) == "gemini-4-argon-high"
    for m in CANONICAL_ARGON_MODELS:
        assert normalize_argon_model_slug(m) == m
    assert normalize_argon_model_slug("claude-opus-5-5-high") == "claude-opus-5-5-high"


def test_evaluate_fake_pass_trivial_assertions(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    # Tests with assert True, assert 1 == 1, assert bool(1), assert 'a' == 'a'
    trivial_code = """
def test_case_true():
    assert True

def test_case_numeric_eq():
    assert 1 == 1

def test_case_bool_call():
    assert bool(1)

def test_case_string_eq():
    assert "hello" == "hello"
"""
    res = critic.evaluate_fake_pass_risk(
        claim_text="Implemented tests",
        test_code=trivial_code,
        execution_log="pytest passed in 0.1s exit code 0",
    )
    codes = {item["code"] for item in res["detected_anti_patterns"]}
    assert "trivial_assertion" in codes
    assert res["fake_pass_risk_score"] >= 0.45
    assert any("trivial" in rem.lower() or "assert true" in rem.lower() for rem in res["remediation_steps"])


def test_evaluate_fake_pass_empty_test_functions(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    empty_code = """
def test_no_assertions():
    x = 10
    y = 20
    z = x + y

def test_another_empty():
    pass
"""
    res = critic.evaluate_fake_pass_risk(
        claim_text="Implemented tests",
        test_code=empty_code,
        execution_log="passed in 0.1s exit code 0",
    )
    codes = {item["code"] for item in res["detected_anti_patterns"]}
    assert "trivial_assertion" in codes
    triv_item = next(item for item in res["detected_anti_patterns"] if item["code"] == "trivial_assertion")
    assert "0 real assertions in test_no_assertions, test_another_empty" in triv_item["detail"]


def test_evaluate_fake_pass_silent_exception_swallow(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    swallow_code = """
def test_something():
    try:
        val = int("not_a_number")
    except Exception:
        pass
    assert val is not None
"""
    res = critic.evaluate_fake_pass_risk(
        claim_text="Implemented error handling test",
        test_code=swallow_code,
        execution_log="passed in 0.2s exit code 0",
    )
    codes = {item["code"] for item in res["detected_anti_patterns"]}
    assert "silent_exception_swallow" in codes
    swallow_item = next(item for item in res["detected_anti_patterns"] if item["code"] == "silent_exception_swallow")
    assert "except Exception: pass" in swallow_item["detail"]


def test_evaluate_fake_pass_unexecuted_claims(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    clean_test_code = """
def test_real():
    assert 2 + 2 == 4
"""
    # Victory claim without execution log evidence
    res_no_log = critic.evaluate_fake_pass_risk(
        claim_text="Task Victory: Everything is 100% completed and passed",
        test_code=clean_test_code,
        execution_log="",
    )
    codes_no_log = {item["code"] for item in res_no_log["detected_anti_patterns"]}
    assert "unexecuted_test_claim" in codes_no_log
    assert res_no_log["verdict"] in ("CONDITIONAL_RETRY", "REJECT_FAKE_PASS")

    # Victory claim with execution log evidence -> unexecuted_test_claim should NOT be triggered
    res_with_log = critic.evaluate_fake_pass_risk(
        claim_text="Task Victory: Everything is 100% completed and passed",
        test_code=clean_test_code,
        execution_log="1 passed in 0.05s (exit code 0)",
    )
    codes_with_log = {item["code"] for item in res_with_log["detected_anti_patterns"]}
    assert "unexecuted_test_claim" not in codes_with_log
    assert res_with_log["verdict"] == "PASS"


def test_evaluate_fake_pass_over_mocked_sut(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    over_mocked_code = """
def test_mocked_computation():
    calculator.compute.return_value = 999
    res = calculator.compute()
    assert res == 999
"""
    res = critic.evaluate_fake_pass_risk(
        claim_text="Added computation tests",
        test_code=over_mocked_code,
        execution_log="passed in 0.1s exit code 0",
    )
    codes = {item["code"] for item in res["detected_anti_patterns"]}
    assert "over_mocked_sut" in codes


def test_evaluate_fake_pass_legacy_flash_leak(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    dummy_file = tmp_path / "config.yaml"
    dummy_file.write_text("model: gemini-3.8-flash-high\n", encoding="utf-8")

    res = critic.evaluate_fake_pass_risk(
        claim_text="Config updated to gemini-3.8-flash-medium",
        test_code="def test_ok(): assert 1 == 2 - 1",
        execution_log="passed in 0.1s exit code 0",
        changed_files=[str(dummy_file)],
    )
    codes = {item["code"] for item in res["detected_anti_patterns"]}
    assert "legacy_gemini_3_8_flash_leak" in codes
    assert res["fake_pass_risk_score"] >= 0.30


def test_evaluate_fake_pass_syntax_error(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    broken_code = "def test_syntax_err(:\n    assert True"
    res = critic.evaluate_fake_pass_risk(
        claim_text="Tests written",
        test_code=broken_code,
        execution_log="passed exit code 0",
    )
    codes = {item["code"] for item in res["detected_anti_patterns"]}
    assert "syntax_error_in_test_code" in codes
    assert res["verdict"] in ("CONDITIONAL_RETRY", "REJECT_FAKE_PASS")


def test_evaluate_fake_pass_clean_tests_pass(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    clean_code = """
def test_matrix_multiplication():
    a = [[1, 2], [3, 4]]
    b = [[2, 0], [1, 2]]
    # Real computation and behavioral assertion
    c00 = a[0][0] * b[0][0] + a[0][1] * b[1][0]
    c01 = a[0][0] * b[0][1] + a[0][1] * b[1][1]
    assert c00 == 4
    assert c01 == 4

def test_exception_raised():
    import pytest
    with pytest.raises(ValueError):
        int("not_a_number")
"""
    res = critic.evaluate_fake_pass_risk(
        claim_text="Matrix multiplication and error handling verified",
        test_code=clean_code,
        execution_log="2 passed in 0.12s (exit code 0)",
    )
    assert res["fake_pass_risk_score"] == 0.0
    assert res["risk_level"] == "LOW"
    assert res["verdict"] == "PASS"
    assert res["detected_anti_patterns"] == []
    assert res["remediation_steps"] == []


def test_critique_victory_claim_four_axes_and_attestation(tmp_path):
    db_file = tmp_path / "knowledge_compiler.db"
    critic = SovereignVictoryCritic(db_path=db_file)

    good_test_code = """
def test_argon_tiers():
    tiers = ("gemini-4-argon-high", "gemini-4-argon-medium", "gemini-4-argon-low")
    assert len(tiers) == 3
    assert tiers[0] == "gemini-4-argon-high"
"""
    cert = critic.critique_victory_claim(
        claim_type="task_victory",
        title="Migrate Fleet Routing to Gemini 4 Argon",
        claim_summary="Migrated all models to gemini-4-argon-high, gemini-4-argon-medium, gemini-4-argon-low with pytest exit code 0.",
        requirements=["gemini-4-argon-high", "gemini-4-argon-medium", "gemini-4-argon-low", "pytest"],
        evidence_log="pytest: 15 passed in 1.45s (exit code 0)",
        test_code=good_test_code,
        project="hermes-agent",
    )
    assert cert["gate_passed"] is True
    assert cert["verdict"] == "VICTORY_CERTIFIED"
    assert cert["critique_id"].startswith("vc:")
    assert len(cert["critique_id"]) == 19  # 'vc:' + 16 hex chars
    assert cert["fake_pass_risk_score"] == 0.0

    # Validate 4 axes
    axes = cert["axes"]
    assert axes["requirement_alignment_score"] == 100.0
    assert axes["empirical_execution_score"] == 100.0
    assert axes["counterfactual_falsification_score"] == 100.0
    assert axes["regression_and_argon_safety_score"] == 100.0
    assert cert["composite_critic_score"] == 100.0

    # Verify SQLite persistence directly
    with sqlite3.connect(str(db_file)) as conn:
        row = conn.execute(
            "SELECT critique_id, claim_type, project, verdict, composite_critic_score FROM victory_critique_ledger WHERE critique_id = ?",
            (cert["critique_id"],),
        ).fetchone()
        assert row is not None
        assert row[0] == cert["critique_id"]
        assert row[1] == "task_victory"
        assert row[2] == "hermes-agent"
        assert row[3] == "VICTORY_CERTIFIED"
        assert row[4] == 100.0


def test_critique_victory_claim_rejection_on_fake_pass_and_failures(tmp_path):
    critic = SovereignVictoryCritic(db_path=tmp_path / "critic.db")

    bad_test_code = """
def test_fake():
    assert True
"""
    # Claim with trivial assertion and test failures in log
    fail_cert = critic.critique_victory_claim(
        claim_type="task_victory",
        title="Task Victory: Flaky Feature Done",
        claim_summary="Completed feature implementation without genuine test logic",
        requirements=["database_clustering", "pci_dss_compliance", "zero_lag_sync"],
        evidence_log="FAILED tests/test_foo.py - AssertionError: 4 != 5 (1 failed, 10 passed in 0.8s)",
        test_code=bad_test_code,
        project="hermes-agent",
    )
    assert fail_cert["gate_passed"] is False
    assert fail_cert["verdict"] == "REJECT_FAKE_PASS"
    assert fail_cert["fake_pass_risk_score"] >= 0.45
    assert fail_cert["axes"]["regression_and_argon_safety_score"] <= 45.0
    assert fail_cert["composite_critic_score"] < 65.0



def test_seed_canonical_project_critiques_and_summary(tmp_path):
    db_file = tmp_path / "knowledge_compiler.db"
    critic = SovereignVictoryCritic(db_path=db_file)

    seeded = critic.seed_canonical_project_critiques()
    assert len(seeded) == 5

    summary = critic.get_ledger_summary()
    assert summary["total_critiques"] == 5
    assert summary["passed_count"] == 5
    assert summary["blocked_count"] == 0
    assert summary["avg_fake_pass_risk"] == 0.0
    assert summary["avg_critic_score"] >= 95.0
    assert set(summary["projects_covered"]) == {
        "O20",
        "VerticalRisk",
        "agy-pinned-monitor",
        "hermes-agent",
        "zencode-ent",
    }


def test_hourly_digest_format_markdown_report_victory_critic(tmp_path):
    db_file = tmp_path / "knowledge_compiler.db"
    critic = SovereignVictoryCritic(db_path=db_file)
    critic.seed_canonical_project_critiques()

    summary = critic.get_ledger_summary()
    scan_result = {
        "overall_health_score": 98,
        "severity": "HEALTHY",
        "timestamp": "2026-10-17T12:00:00Z",
        "cron": {"cron_health_score": 100, "ticker_heartbeat": {"is_stale": False}},
        "entropy": {"entropy_health_score": 95, "streams": []},
        "victory_critic": {
            "total_critiques": summary["total_critiques"],
            "passed_count": summary["passed_count"],
            "blocked_count": summary["blocked_count"],
            "avg_fake_pass_risk": summary["avg_fake_pass_risk"],
            "avg_composite_score": summary["avg_critic_score"],
        },
    }

    notifier = HermesTelegramNotifier()
    md_report = notifier.format_markdown_report(scan_result)

    assert "## 🛡️ Sovereign Victory Critic & Anti-Fake-Pass Telemetry" in md_report
    assert f"- Total Critiques: {summary['total_critiques']}" in md_report
    assert f"- Certified Victories: {summary['passed_count']}" in md_report
    assert f"- Blocked Fake Passes: {summary['blocked_count']}" in md_report
    assert f"- Avg Fake Pass Risk: {summary['avg_fake_pass_risk']:.3f}" in md_report
    assert f"- Avg Composite Score: {summary['avg_critic_score']:.1f}/100" in md_report

    # Also test top-level module function format_markdown_report()
    fn_report = format_markdown_report(scan_result)
    assert fn_report == md_report


def test_cli_main_interface(capsys):
    # Test --summary CLI
    ret = critic_main(["--summary"])
    assert ret == 0
    captured = capsys.readouterr()
    summary_data = json.loads(captured.out)
    assert "total_critiques" in summary_data
    assert "passed_count" in summary_data

    # Test --evaluate-fake-pass without execution log -> should exit with code 1
    ret_fail = critic_main(["--evaluate-fake-pass", "Task Victory: all done"])
    assert ret_fail == 1
    captured_fail = capsys.readouterr()
    res_fail = json.loads(captured_fail.out)
    assert res_fail["verdict"] in ("CONDITIONAL_RETRY", "REJECT_FAKE_PASS")

    # Test --evaluate-fake-pass with empirical execution log -> should exit with code 0
    ret_pass = critic_main([
        "--evaluate-fake-pass", "Task Victory: all done",
        "--execution-log", "pytest 5 passed in 0.1s exit code 0",
    ])
    assert ret_pass == 0
    captured_pass = capsys.readouterr()
    res_pass = json.loads(captured_pass.out)
    assert res_pass["verdict"] == "PASS"

    # Test --critique-victory CLI with empirical execution log -> exit 0
    ret_critique = critic_main([
        "--critique-victory", "Test CLI Victory",
        "--execution-log", "pytest 10 passed in 0.5s exit code 0",
    ])
    assert ret_critique == 0
    captured_critique = capsys.readouterr()
    res_critique = json.loads(captured_critique.out)
    assert res_critique["gate_passed"] is True


def test_gemini_strict_dod_reminder_and_cli_injection(capsys):
    from tools.sovereign_victory_critic import (
        GEMINI_STRICT_DOD_MARKER,
        build_gemini_strict_dod_reminder,
        ensure_gemini_dod_reminder,
    )
    from tools.fleet_council_dispatcher import COUNCIL_ROLES

    block = build_gemini_strict_dod_reminder(
        task_level="L3_COMPLEX",
        task_type="code_gen",
        target_model="gemini-3.8-flash-medium",
    )
    assert GEMINI_STRICT_DOD_MARKER in block
    assert "gemini-4-argon-medium" in block
    for i in range(1, 6):
        assert f"[DoD-{i}]" in block

    # Idempotence on Gemini 4 Argon models
    p1 = ensure_gemini_dod_reminder("Write unit tests for router", target_model="gemini-4-argon-high")
    p2 = ensure_gemini_dod_reminder(p1, target_model="gemini-4-argon-high")
    assert p1 == p2
    assert p1.count(GEMINI_STRICT_DOD_MARKER) == 1

    # CLI --inject-gemini-dod flag
    ret = critic_main([
        "--inject-gemini-dod", "Refactor module X",
        "--target-model", "gemini-4-argon-low",
        "--task-level", "L2_STANDARD",
    ])
    assert ret == 0
    out = capsys.readouterr().out
    assert "Refactor module X" in out
    assert GEMINI_STRICT_DOD_MARKER in out
    assert "gemini-4-argon-low" in out

    # CouncilRoleConfig.build_prompt embeds DoD reminder for Gemini 4 Argon
    role_prompt = COUNCIL_ROLES["youtube_expert"].build_prompt(
        topic="Shannon Entropy",
        script_content="Scene 1 draft",
        target_model="gemini-4-argon-high",
    )
    assert GEMINI_STRICT_DOD_MARKER in role_prompt

