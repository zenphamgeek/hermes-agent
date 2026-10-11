"""Resilience Lab offline simulation executor."""

from typing import Dict, List, Any
from pydantic import BaseModel

from service.acquisition.classifier import ResponseClass, ResponseClassifier
from service.acquisition.retry_engine import AdaptiveRetryEngine
from .fixtures import get_fixture_response


class ScenarioResult(BaseModel):
    scenario: str
    status_code: int
    classified_as: ResponseClass
    expected_class: ResponseClass
    passed: bool
    retry_recommended: bool


class ResilienceLabSimulator:
    def __init__(self):
        self.retry_engine = AdaptiveRetryEngine(base_delay=0.1, max_delay=1.0)

    def run_scenario(self, scenario: str) -> ScenarioResult:
        status_code, headers, body = get_fixture_response(scenario)
        resp_class = ResponseClassifier.classify(status_code, headers, body)

        expected_mapping = {
            "challenge": ResponseClass.INTERACTIVE_CHALLENGE,
            "rate_limit": ResponseClass.RATE_LIMIT,
            "server_error": ResponseClass.TRANSIENT,
            "not_modified": ResponseClass.NOT_MODIFIED,
            "success": ResponseClass.SUCCESS
        }

        expected = expected_mapping.get(scenario, ResponseClass.UNKNOWN_ERROR)
        passed = (resp_class == expected)

        retry_decision = self.retry_engine.compute_retry(1, resp_class, headers)

        return ScenarioResult(
            scenario=scenario,
            status_code=status_code,
            classified_as=resp_class,
            expected_class=expected,
            passed=passed,
            retry_recommended=retry_decision.should_retry
        )

    def run_matrix(self) -> List[ScenarioResult]:
        scenarios = ["challenge", "rate_limit", "server_error", "not_modified", "success"]
        return [self.run_scenario(s) for s in scenarios]
