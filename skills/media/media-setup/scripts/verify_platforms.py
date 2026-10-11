#!/usr/bin/env python3
"""Verify connectivity to all media publishing platforms.

Usage:
    python verify_platforms.py --check-all
    python verify_platforms.py --check x
    python verify_platforms.py --check youtube
    python verify_platforms.py --check facebook
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_x() -> dict:
    """Check X/Twitter connectivity via xurl."""
    result = {"status": "missing", "username": None, "details": None}

    # Check if xurl is installed
    xurl_path = subprocess.run(
        ["which", "xurl"], capture_output=True, text=True
    )
    if xurl_path.returncode != 0:
        result["details"] = "xurl CLI not installed"
        return result

    # Check auth status
    try:
        auth = subprocess.run(
            ["xurl", "auth", "status"],
            capture_output=True, text=True, timeout=10
        )
        if auth.returncode != 0 or "oauth2: (none)" in auth.stdout:
            result["details"] = "xurl not authenticated"
            return result

        # Try whoami
        whoami = subprocess.run(
            ["xurl", "whoami"],
            capture_output=True, text=True, timeout=10
        )
        if whoami.returncode == 0:
            try:
                data = json.loads(whoami.stdout)
                username = data.get("data", {}).get("username", "unknown")
                result["status"] = "ok"
                result["username"] = f"@{username}"
            except json.JSONDecodeError:
                result["status"] = "ok"
                result["details"] = "Authenticated but couldn't parse whoami"
        else:
            result["details"] = f"whoami failed: {whoami.stderr.strip()}"

    except subprocess.TimeoutExpired:
        result["details"] = "xurl command timed out"
    except Exception as e:
        result["details"] = str(e)

    return result


def check_youtube() -> dict:
    """Check YouTube API connectivity via Google Workspace setup."""
    result = {"status": "missing", "channel": None, "details": None}

    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    token_path = Path(hermes_home) / "google_token.json"

    if not token_path.exists():
        result["details"] = "google_token.json not found"
        return result

    # Check if token has YouTube scopes
    try:
        with open(token_path) as f:
            token_data = json.load(f)
        scopes = token_data.get("scopes", [])
        has_youtube = any("youtube" in s.lower() for s in scopes)

        if has_youtube:
            result["status"] = "ok"
            result["details"] = "YouTube scope present in token"
        else:
            result["status"] = "partial"
            result["details"] = (
                "Google token exists but missing YouTube scope. "
                "Re-run setup with --services youtube"
            )
    except (json.JSONDecodeError, KeyError) as e:
        result["details"] = f"Token file parse error: {e}"

    # Check API key
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if api_key:
        result["api_key"] = "present"
    else:
        if result["status"] != "ok":
            result["details"] = (result.get("details", "") or "") + "; YOUTUBE_API_KEY not set"

    return result


def check_facebook() -> dict:
    """Check Facebook Graph API connectivity."""
    result = {"status": "missing", "page": None, "details": None}

    # Check for page access token
    token = os.environ.get("FB_PAGE_ACCESS_TOKEN_PERSONAL")
    if not token:
        # Try loading from .env
        env_path = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("FB_PAGE_ACCESS_TOKEN_PERSONAL="):
                        token = line.split("=", 1)[1].strip()
                        break

    if not token:
        result["details"] = "FB_PAGE_ACCESS_TOKEN_PERSONAL not set in ~/.hermes/.env"
        return result

    # Test the token with a simple API call
    try:
        import urllib.request
        import urllib.error

        url = f"https://graph.facebook.com/v21.0/me?access_token={token}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            result["status"] = "ok"
            result["page"] = data.get("name", "Unknown")
    except urllib.error.HTTPError as e:
        result["details"] = f"Graph API error: {e.code} {e.reason}"
    except Exception as e:
        result["details"] = f"Connection error: {e}"

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify media platform connectivity")
    parser.add_argument(
        "--check",
        choices=["x", "youtube", "facebook", "all"],
        default="all",
        help="Which platform(s) to check",
    )
    parser.add_argument("--check-all", action="store_true", help="Check all platforms")
    args = parser.parse_args()

    if args.check_all:
        args.check = "all"

    # Load .env for environment variables
    env_path = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

    results = {}

    if args.check in ("all", "x"):
        results["x"] = check_x()
    if args.check in ("all", "youtube"):
        results["youtube"] = check_youtube()
    if args.check in ("all", "facebook"):
        results["facebook"] = check_facebook()

    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Exit code: 0 if all checked platforms are ok, 1 otherwise
    all_ok = all(r["status"] == "ok" for r in results.values())
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
