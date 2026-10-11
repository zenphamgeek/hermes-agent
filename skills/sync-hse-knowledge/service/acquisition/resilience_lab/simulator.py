"""Resilience Lab Simulator for Fault Injection & Quarantine Testing."""

from typing import Dict, Any, List
from pydantic import BaseModel

from service.acquisition.classifier import ResponseClassifier, ResponseClass
from service.acquisition.resilience_lab.fixtures import SCENARIO_FIXTURES


class ScenarioResult(BaseModel):
    scenario_name: str
    injected_status: int
    detected_class: ResponseClass
    handled_properly: bool
    quarantined: bool


class ResilienceSimulator:
    def run_all_scenarios(self) -> List[ScenarioResult]:
        results = []
        for name, fixture in SCENARIO_FIXTURES.items():
            res_class = ResponseClassifier.classify(
                status_code=fixture["status_code"],
                headers=fixture.get("headers"),
                body_text=fixture.get("body")
            )

            quarantined = (res_class == ResponseClass.INTERACTIVE_CHALLENGE)
            handled = res_class in (
                ResponseClass.SUCCESS,
                ResponseClass.NOT_MODIFIED,
                ResponseClass.RATE_LIMIT,
                ResponseClass.TRANSIENT,
                ResponseClass.INTERACTIVE_CHALLENGE,
                ResponseClass.JS_REQUIRED
            )

            results.append(ScenarioResult(
                scenario_name=name,
                injected_status=fixture["status_code"],
                detected_class=res_class,
                handled_properly=handled,
                quarantined=quarantined
            ))
        return results
