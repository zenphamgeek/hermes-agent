#!/usr/bin/env python3
"""Script to run Resilience Lab test matrix."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.acquisition.resilience_lab.simulator import ResilienceSimulator

def main():
    sim = ResilienceSimulator()
    results = sim.run_all_scenarios()
    failed = [r for r in results if not r.handled_properly]
    for r in results:
        print(f"[{'PASS' if r.handled_properly else 'FAIL'}] {r.scenario_name}: Status {r.injected_status} -> {r.detected_class.value} (Quarantine: {r.quarantined})")
    
    if failed:
        print(f"FAILED: {len(failed)} scenarios failed.")
        sys.exit(1)
    print("SUCCESS: All resilience scenarios handled properly.")
    sys.exit(0)

if __name__ == "__main__":
    main()
