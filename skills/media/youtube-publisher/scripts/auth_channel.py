#!/usr/bin/env python3
"""
YouTube Multi-Channel Authenticator & Manager for Hermes Agent.
===============================================================
Enables independent OAuth2 authentication for separate YouTube channels
or Brand Accounts under the same (or different) Google accounts (e.g. inteligentsilos@gmail.com).

Usage:
  # 1. Generate Auth URL for 'phamtrai_dialy':
  python3 auth_channel.py --channel phamtrai_dialy --auth-url

  # 2. Complete exchange after user selects the channel in browser:
  python3 auth_channel.py --channel phamtrai_dialy --auth-code "http://localhost:1/?state=...&code=..."

  # 3. Check / verify channel connection:
  python3 auth_channel.py --channel phamtrai_dialy --check

  # 4. List all authenticated YouTube channels:
  python3 auth_channel.py --list-all
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
CLIENT_SECRET_PATH = HERMES_HOME / "google_client_secret.json"
PENDING_AUTH_DIR = HERMES_HOME / "cache" / "oauth_pending"
PENDING_AUTH_DIR.mkdir(parents=True, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]

REDIRECT_URI = "http://localhost:1"


def get_token_path(channel_key: str) -> Path:
    normalized = channel_key.lower().replace("-", "_").strip()
    if normalized == "zenpham" or normalized == "default":
        return HERMES_HOME / "google_token.json"
    return HERMES_HOME / f"google_token_{normalized}.json"


def get_pending_auth_path(channel_key: str) -> Path:
    normalized = channel_key.lower().replace("-", "_").strip()
    return PENDING_AUTH_DIR / f"pending_auth_{normalized}.json"


def generate_auth_url(channel_key: str) -> str:
    if not CLIENT_SECRET_PATH.exists():
        print(json.dumps({
            "status": "error",
            "error": f"Client secret not found at {CLIENT_SECRET_PATH}. Please provide Google client secret."
        }))
        sys.exit(1)

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        autogenerate_code_verifier=True,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent select_account",
    )

    pending_data = {
        "channel_key": channel_key,
        "state": state,
        "code_verifier": flow.code_verifier,
        "redirect_uri": REDIRECT_URI,
    }
    get_pending_auth_path(channel_key).write_text(json.dumps(pending_data), encoding="utf-8")
    return auth_url


def exchange_code(channel_key: str, code_or_url: str) -> Dict:
    pending_path = get_pending_auth_path(channel_key)
    if not pending_path.exists():
        raise RuntimeError(f"No pending auth state found for '{channel_key}'. Run --auth-url first.")

    pending_data = json.loads(pending_path.read_text(encoding="utf-8"))

    # Extract code and state from URL if full redirect URL was pasted
    code = code_or_url.strip()
    if code.startswith("http"):
        parsed = urlparse(code)
        params = parse_qs(parsed.query)
        code = params.get("code", [""])[0]
        ret_state = params.get("state", [""])[0]
        if ret_state and ret_state != pending_data.get("state"):
            print(f"[!] Warning: state mismatch (expected {pending_data.get('state')}, got {ret_state})")

    if not code:
        raise ValueError("Could not extract authorization code from input.")

    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH),
        scopes=SCOPES,
        redirect_uri=pending_data.get("redirect_uri", REDIRECT_URI),
        state=pending_data.get("state"),
        code_verifier=pending_data.get("code_verifier"),
    )

    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Inspect the channel bound to this credential
    yt = build("youtube", "v3", credentials=creds)
    ch_resp = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not ch_resp.get("items"):
        raise RuntimeError("No YouTube channel found for this authorized account/brand.")

    ch_info = ch_resp["items"][0]
    channel_title = ch_info["snippet"]["title"]
    channel_id = ch_info["id"]
    custom_url = ch_info["snippet"].get("customUrl", "")

    # Save token payload
    token_payload = json.loads(creds.to_json())
    token_payload["channel_title"] = channel_title
    token_payload["channel_id"] = channel_id
    token_payload["channel_custom_url"] = custom_url
    token_payload["channel_key"] = channel_key

    target_token_path = get_token_path(channel_key)
    target_token_path.write_text(json.dumps(token_payload, indent=2), encoding="utf-8")

    # Clean up pending
    if pending_path.exists():
        pending_path.unlink()

    return {
        "status": "ok",
        "channel_key": channel_key,
        "channel_title": channel_title,
        "channel_id": channel_id,
        "custom_url": custom_url,
        "token_path": str(target_token_path),
    }


def verify_channel(channel_key: str) -> Dict:
    token_path = get_token_path(channel_key)
    if not token_path.exists():
        return {
            "status": "error",
            "channel_key": channel_key,
            "error": f"Token file not found at {token_path}",
        }

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    with open(token_path, encoding="utf-8") as f:
        data = json.load(f)

    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        data["token"] = creds.token
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    yt = build("youtube", "v3", credentials=creds)
    ch_resp = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not ch_resp.get("items"):
        return {"status": "error", "channel_key": channel_key, "error": "No channel found"}

    ch = ch_resp["items"][0]
    return {
        "status": "ok",
        "channel_key": channel_key,
        "channel_title": ch["snippet"]["title"],
        "channel_id": ch["id"],
        "custom_url": ch["snippet"].get("customUrl", ""),
        "subscribers": ch.get("statistics", {}).get("subscriberCount", "N/A"),
        "video_count": ch.get("statistics", {}).get("videoCount", "N/A"),
        "token_path": str(token_path),
    }


def list_all_channels() -> List[Dict]:
    results = []
    tokens = list(HERMES_HOME.glob("google_token*.json"))
    for t in tokens:
        key = "zenpham" if t.name == "google_token.json" else t.stem.replace("google_token_", "")
        res = verify_channel(key)
        results.append(res)
    return results


KNOWN_CHANNELS = {
    "reality_decode": {
        "title": "REALITY DECODE",
        "email": "inteligentsilos@gmail.com",
        "url": "https://www.youtube.com",
        "hint": "Chọn tài khoản Google 'inteligentsilos@gmail.com' -> chọn kênh 'REALITY DECODE'",
    },
    "phamtrai_dialy": {
        "title": "Biết Địa lý từ Ba tôi",
        "email": "inteligentsilos@gmail.com",
        "url": "https://www.youtube.com/@phamtrai-dialy",
        "hint": "Chọn kênh: 'Biết Địa lý từ Ba tôi' (@phamtrai-dialy)",
    },
    "zenpham": {
        "title": "ZENPHAM",
        "email": "inteligentsilos@gmail.com",
        "url": "https://www.youtube.com/@zenpham-g3l",
        "hint": "Chọn kênh: 'ZENPHAM'",
    },
}


def main():
    parser = argparse.ArgumentParser(description="YouTube Multi-Channel Auth Manager")
    parser.add_argument("--channel", default="reality_decode", help="Channel key (e.g. reality_decode, phamtrai_dialy, zenpham)")
    parser.add_argument("--auth-url", action="store_true", help="Generate authorization URL")
    parser.add_argument("--auth-code", help="Authorization code or callback redirect URL")
    parser.add_argument("--check", action="store_true", help="Verify channel credentials")
    parser.add_argument("--list-all", action="store_true", help="List all authenticated channels")

    args = parser.parse_args()

    ch_clean = args.channel.lower().replace("-", "_").strip()
    ch_meta = KNOWN_CHANNELS.get(ch_clean, {
        "title": args.channel.upper(),
        "email": "tài khoản Google quản lý kênh",
        "url": "",
        "hint": f"Chọn kênh: {args.channel}",
    })

    if args.list_all:
        res = list_all_channels()
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    if args.auth_url:
        url = generate_auth_url(args.channel)
        print("\n" + "=" * 70)
        print(f"🔑 XÁC THỰC OAUTH2 CHO KÊNH: {ch_meta['title']} ({ch_clean.upper()})")
        print("=" * 70)
        print(f"1. Mở liên kết dưới đây bằng trình duyệt có đăng nhập '{ch_meta['email']}':\n")
        print(url)
        print("\n2. Khi màn hình Google hiện ra danh sách các tài khoản / kênh / Brand Accounts:")
        print(f"   👉 {ch_meta['hint']}")
        print("   👉 Nhấn 'Allow' / 'Cho phép' để cấp quyền quản lý và upload video.")
        print("3. Trình duyệt sẽ chuyển hướng sang trang (http://localhost:1/?state=...&code=...).")
        print("   (Trang này có thể hiện 'Không thể kết nối' - ĐÂY LÀ ĐIỀU HOÀN TOÀN BÌNH THƯỜNG).")
        print("4. Sao chép toàn bộ đường dẫn trên thanh địa chỉ và dán vào chat hoặc chạy lệnh:")
        print(f"   .venv/bin/python auth_channel.py --channel {ch_clean} --auth-code '<DÁN_ĐƯỜNG_DẪN_VÀO_ĐÂY>'")
        print("=" * 70 + "\n")
        return

    if args.auth_code:
        try:
            res = exchange_code(args.channel, args.auth_code)
            print(json.dumps(res, indent=2, ensure_ascii=False))
            print(f"\n🎉 KẾT NỐI THÀNH CÔNG: Kênh '{res['channel_title']}' ({res['custom_url']}) -> {res['token_path']}")
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False))
            sys.exit(1)
        return

    if args.check:
        res = verify_channel(args.channel)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
