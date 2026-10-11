"""Test CLI commands and Typer integration (Section 18)."""

import pytest
from typer.testing import CliRunner
from service.cli import app

runner = CliRunner()


def test_cli_plan():
    result = runner.invoke(app, ["plan", "--source", "VN_CUSTOMS_RULINGS", "--json"])
    assert result.exit_code == 0
    assert "VN_CUSTOMS_RULINGS" in result.stdout


def test_cli_sources_list():
    result = runner.invoke(app, ["sources", "list", "--json"])
    assert result.exit_code == 0
    assert "VN_GOV_LEGAL" in result.stdout


def test_cli_sources_validate():
    result = runner.invoke(app, ["sources", "validate", "--json"])
    assert result.exit_code == 0
    assert '"valid": true' in result.stdout


def test_cli_license_readiness():
    result = runner.invoke(app, ["license", "readiness", "--json"])
    assert result.exit_code == 0
    assert "WCO_HS_CONTENT" in result.stdout


def test_cli_resilience_lab():
    result = runner.invoke(app, ["resilience-lab", "run", "--scenario", "challenge-matrix", "--json"])
    assert result.exit_code == 0
    assert '"all_passed": true' in result.stdout


def test_cli_health():
    result = runner.invoke(app, ["health", "--json"])
    assert result.exit_code == 0
    assert '"status": "healthy"' in result.stdout
