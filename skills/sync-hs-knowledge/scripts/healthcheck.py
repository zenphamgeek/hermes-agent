#!/usr/bin/env python3
"""Infrastructure healthcheck script."""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

skill_dir = Path(__file__).resolve().parent.parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from service.db.session import init_db, get_db_session
from service.core.registry import load_source_registry

def main():
    parser = argparse.ArgumentParser(description="HS Knowledge Healthcheck")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    try:
        init_db()
        with get_db_session() as db:
            registry = load_source_registry()
            status = {
                "status": "healthy",
                "database": "connected",
                "sources_configured": len(registry.list_sources()),
                "timestamp": str(datetime.now())
            }
            print(json.dumps(status, indent=2))
    except Exception as e:
        print(json.dumps({"status": "unhealthy", "error": str(e)}, indent=2))
        sys.exit(7)

if __name__ == "__main__":
    main()
