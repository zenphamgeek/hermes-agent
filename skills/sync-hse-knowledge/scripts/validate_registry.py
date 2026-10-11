#!/usr/bin/env python3
"""Script to validate source catalog YAML definitions."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.core.registry import load_source_registry

def main():
    registry = load_source_registry()
    errors = registry.validate()
    if errors:
        print(f"FAILED: Found {len(errors)} errors:")
        for e in errors:
            print(f" - {e}")
        sys.exit(2)
    print(f"SUCCESS: {len(registry.list_sources())} sources are valid.")
    sys.exit(0)

if __name__ == "__main__":
    main()
