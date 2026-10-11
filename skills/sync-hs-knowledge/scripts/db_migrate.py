#!/usr/bin/env python3
"""Database migration runner script."""

import sys
import json
import argparse
from pathlib import Path

skill_dir = Path(__file__).resolve().parent.parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from service.db.session import init_db

def main():
    parser = argparse.ArgumentParser(description="Database migration runner")
    parser.add_argument("--direction", default="upgrade", choices=["upgrade", "downgrade"], help="Migration direction")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    try:
        init_db()
        print(json.dumps({"status": "migration_complete", "direction": args.direction}, indent=2))
    except Exception as e:
        print(json.dumps({"status": "migration_failed", "error": str(e)}, indent=2))
        sys.exit(7)

if __name__ == "__main__":
    main()
