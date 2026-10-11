"""Tests for Resilience Lab Simulator & Classifier."""

from service.acquisition.resilience_lab.simulator import ResilienceSimulator
from service.acquisition.classifier import ResponseClassifier, ResponseClass


def test_resilience_simulator_all_scenarios():
    sim = ResilienceSimulator()
    results = sim.run_all_scenarios()
    assert len(results) == 6
    for r in results:
        assert r.handled_properly is True


def test_response_classifier_turnstile():
    body = "<html><body><div class=\"cf-turnstile\"></div></body></html>"
    res_class = ResponseClassifier.classify(403, headers={"server": "cloudflare"}, body_text=body)
    assert res_class == ResponseClass.INTERACTIVE_CHALLENGE


def test_response_classifier_rate_limit():
    res_class = ResponseClassifier.classify(429, headers={"retry-after": "5"}, body_text="Too many requests")
    assert res_class == ResponseClass.RATE_LIMIT
