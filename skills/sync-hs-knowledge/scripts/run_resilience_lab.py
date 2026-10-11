#!/usr/bin/env python3
"""Resilience Lab runner script."""

import sys
import json
import argparse
from pathlib import Path

skill_dir = Path(__file__).resolve().parent.parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from service.acquisition.resilience_lab.simulator import ResilienceLabSimulator

def main():
    parser = argparse.ArgumentParser(description="Run offline WAF/Challenge Resilience Lab")
    parser.add_argument("--scenario", default="challenge-matrix", help="Scenario or challenge-matrix")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    sim = ResilienceLabSimulator()
    if args.scenario == "challenge-matrix":
        results = [r.model_dump() for r in sim.run_matrix()]
        all_passed = all(r["passed"] for r in results)
        print(json.dumps({"scenario": args.scenario, "all_passed": all_passed, "matrix": results}, indent=2))
        if not all_passed:
            sys.exit(9)
    else:
        res = sim.run_scenario(args.scenario)
        print(json.dumps(res.model_dump(), indent=2))
        if not res.passed:
            sys.exit(9)

if __name__ == "__main__":
    main()
