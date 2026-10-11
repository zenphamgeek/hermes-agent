"""Test offline Resilience Lab simulation (Section 10.5, AC-018, AC-019, AC-022)."""

import pytest
from service.acquisition.resilience_lab.simulator import ResilienceLabSimulator


def test_resilience_lab_matrix():
    simulator = ResilienceLabSimulator()
    results = simulator.run_matrix()
    assert len(results) == 5
    for r in results:
        assert r.passed is True, f"Scenario {r.scenario} failed: classified as {r.classified_as}"


def test_resilience_lab_challenge_quarantine():
    simulator = ResilienceLabSimulator()
    res = simulator.run_scenario("challenge")
    assert res.passed is True
    assert res.retry_recommended is False
