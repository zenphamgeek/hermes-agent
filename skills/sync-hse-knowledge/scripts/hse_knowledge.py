#!/usr/bin/env python3
"""CLI Entrypoint wrapper for hse-knowledge."""

import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.cli import app

if __name__ == "__main__":
    app()
