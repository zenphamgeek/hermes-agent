#!/usr/bin/env python3
"""Health check script for Docker container and process liveness."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.db.session import get_db_session
from service.db.models import Source

def main():
    try:
        with get_db_session() as db:
            src_count = db.query(Source).count()
            print(f"HEALTHY: Database connected, {src_count} sources configured.")
            sys.exit(0)
    except Exception as e:
        print(f"UNHEALTHY: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
