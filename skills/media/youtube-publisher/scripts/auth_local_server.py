#!/usr/bin/env python3
"""
OAuth Local Server Authenticator for YouTube Multi-Channel.
Runs a local server on port 8085 to capture Google OAuth redirect automatically.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import wsgiref.simple_server
wsgiref.simple_server.WSGIServer.allow_reuse_address = True

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
CLIENT_SECRET_PATH = HERMES_HOME / "google_client_secret.json"

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def get_token_path(channel_key: str) -> Path:
    normalized = channel_key.lower().replace("-", "_").strip()
    if normalized in ("zenpham", "default"):
        return HERMES_HOME / "google_token.json"
    return HERMES_HOME / f"google_token_{normalized}.json"


def authenticate_channel(channel_key: str = "phamtrai_dialy", port: int = 8085, login_hint: str = None):
    if not CLIENT_SECRET_PATH.exists():
        print(f"Error: Client secret not found at {CLIENT_SECRET_PATH}")
        sys.exit(1)

    print(f"Starting OAuth Flow for channel '{channel_key}' on port {port}...")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH),
        scopes=SCOPES,
    )

    kwargs = {
        "port": port,
        "prompt": "consent select_account",
        "access_type": "offline",
        "open_browser": False,
    }
    if login_hint:
        kwargs["login_hint"] = login_hint

    creds = flow.run_local_server(**kwargs)

    # Inspect the channel
    yt = build("youtube", "v3", credentials=creds)
    ch_resp = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not ch_resp.get("items"):
        raise RuntimeError("No YouTube channel found for this authorized account/brand.")

    ch_info = ch_resp["items"][0]
    channel_title = ch_info["snippet"]["title"]
    channel_id = ch_info["id"]
    custom_url = ch_info["snippet"].get("customUrl", "")

    token_payload = json.loads(creds.to_json())
    token_payload["channel_title"] = channel_title
    token_payload["channel_id"] = channel_id
    token_payload["channel_custom_url"] = custom_url
    token_payload["channel_key"] = channel_key

    target_token_path = get_token_path(channel_key)
    target_token_path.write_text(json.dumps(token_payload, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"🎉 KẾT NỐI THÀNH CÔNG: Kênh '{channel_title}' ({custom_url})")
    print(f"Token saved to: {target_token_path}")
    print("=" * 60 + "\n")
    return token_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="phamtrai_dialy")
    parser.add_argument("--port", type=int, default=8085)
    parser.add_argument("--login-hint", default=None, help="Email hint for Google account picker")
    args = parser.parse_args()
    authenticate_channel(args.channel, args.port, login_hint=args.login_hint)
