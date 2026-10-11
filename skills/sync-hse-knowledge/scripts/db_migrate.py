#!/usr/bin/env python3
"""Database schema initialization and migration script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.db.session import init_db, get_db_session
from service.core.registry import load_source_registry

def main():
    print("Initializing HSE database schema...")
    init_db()
    with get_db_session() as db:
        registry = load_source_registry()
        count = registry.sync_to_db(db)
        print(f"Synced {count} sources to database.")
    print("Database migration completed successfully.")

if __name__ == "__main__":
    main()
