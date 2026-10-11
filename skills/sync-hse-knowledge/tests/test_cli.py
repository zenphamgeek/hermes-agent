"""Tests for Typer CLI hse-knowledge."""

from typer.testing import CliRunner
from service.cli import app

runner = CliRunner()


def test_cli_sources_list():
    result = runner.invoke(app, ["sources", "list", "--json"])
    assert result.exit_code == 0
    assert "VN_GOV_LEGAL" in result.stdout


def test_cli_sources_validate():
    result = runner.invoke(app, ["sources", "validate", "--json"])
    assert result.exit_code == 0
    assert '"valid": true' in result.stdout


def test_cli_plan():
    result = runner.invoke(app, ["plan", "--scope", "vietnam-core", "--json"])
    assert result.exit_code == 0
    assert "target_sources" in result.stdout


def test_cli_on_demand():
    result = runner.invoke(app, ["on-demand", "Acetone", "--json"])
    assert result.exit_code == 0
    assert '"status": "success"' in result.stdout


def test_cli_resilience_lab():
    result = runner.invoke(app, ["resilience-lab", "run", "--json"])
    assert result.exit_code == 0
    assert '"handled_properly": true' in result.stdout
