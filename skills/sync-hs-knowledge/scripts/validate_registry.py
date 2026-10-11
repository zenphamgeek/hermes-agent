#!/usr/bin/env python3
"""Source registry validation script."""

import sys
import json
import argparse
from pathlib import Path

skill_dir = Path(__file__).resolve().parent.parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from service.core.registry import SourceRegistry

def main():
    parser = argparse.ArgumentParser(description="Validate HS Knowledge source registry YAML")
    parser.add_argument("--file", default=str(skill_dir / "references" / "source-catalog.yaml"), help="Path to catalog YAML")
    parser.add_argument("--json", action="store_true", default=True, help="Output JSON format")
    args = parser.parse_args()

    try:
        registry = SourceRegistry(args.file)
        issues = registry.validate_all()
        if issues:
            print(json.dumps({"valid": False, "issues": issues}, indent=2))
            sys.exit(2)
        print(json.dumps({"valid": True, "sources_count": len(registry.list_sources())}, indent=2))
    except Exception as e:
        print(json.dumps({"valid": False, "error": str(e)}, indent=2))
        sys.exit(2)

if __name__ == "__main__":
    main()
