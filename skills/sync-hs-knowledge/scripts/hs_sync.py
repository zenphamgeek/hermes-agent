#!/usr/bin/env python3
"""CLI wrapper executable for HS Knowledge Sync."""

import sys
from pathlib import Path

# Add parent directory to sys.path so service is importable
skill_dir = Path(__file__).resolve().parent.parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from service.cli import app

if __name__ == "__main__":
    app()
