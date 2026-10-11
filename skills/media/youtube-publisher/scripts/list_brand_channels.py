#!/usr/bin/env python3
"""
List ALL YouTube channels accessible by the current token (including Brand Accounts).
Uses both channels.list(mine=True) and channels.list(managedByMe=True).
Also queries the People API to list Brand Accounts linked to the Google Account.
"""
import json
import os
import sys
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))


def load_credentials(token_path: Path):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

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

    return creds


def list_channels(creds):
    from googleapiclient.discovery import build

    yt = build("youtube", "v3", credentials=creds)
    results = {}

    # 1. mine=True (the channel bound to the authenticated identity)
    print("=" * 60)
    print("📺 channels.list(mine=True) — Kênh chính của token hiện tại:")
    print("=" * 60)
    resp = yt.channels().list(part="snippet,statistics,brandingSettings", mine=True).execute()
    for item in resp.get("items", []):
        ch_id = item["id"]
        title = item["snippet"]["title"]
        custom = item["snippet"].get("customUrl", "N/A")
        subs = item.get("statistics", {}).get("subscriberCount", "?")
        vids = item.get("statistics", {}).get("videoCount", "?")
        print(f"  ✅ {title} ({custom}) — ID: {ch_id} — {subs} subs, {vids} videos")
        results[ch_id] = {"title": title, "customUrl": custom, "source": "mine"}

    # 2. managedByMe=True (content owner channels)
    print("\n" + "=" * 60)
    print("📺 channels.list(managedByMe=True) — Kênh được quản lý:")
    print("=" * 60)
    try:
        resp2 = yt.channels().list(part="snippet,statistics", managedByMe=True).execute()
        for item in resp2.get("items", []):
            ch_id = item["id"]
            title = item["snippet"]["title"]
            custom = item["snippet"].get("customUrl", "N/A")
            subs = item.get("statistics", {}).get("subscriberCount", "?")
            vids = item.get("statistics", {}).get("videoCount", "?")
            print(f"  📋 {title} ({custom}) — ID: {ch_id} — {subs} subs, {vids} videos")
            if ch_id not in results:
                results[ch_id] = {"title": title, "customUrl": custom, "source": "managedByMe"}
        if not resp2.get("items"):
            print("  (Không tìm thấy kênh nào qua managedByMe)")
    except Exception as e:
        print(f"  ⚠ managedByMe không khả dụng: {e}")

    # 3. Try searching by known handle
    print("\n" + "=" * 60)
    print("🔍 Tìm kênh @phamtrai-dialy bằng forHandle:")
    print("=" * 60)
    try:
        resp3 = yt.channels().list(part="snippet,statistics", forHandle="phamtrai-dialy").execute()
        for item in resp3.get("items", []):
            ch_id = item["id"]
            title = item["snippet"]["title"]
            custom = item["snippet"].get("customUrl", "N/A")
            subs = item.get("statistics", {}).get("subscriberCount", "?")
            vids = item.get("statistics", {}).get("videoCount", "?")
            print(f"  🎯 {title} ({custom}) — ID: {ch_id} — {subs} subs, {vids} videos")
            if ch_id not in results:
                results[ch_id] = {"title": title, "customUrl": custom, "source": "forHandle"}
        if not resp3.get("items"):
            print("  (Không tìm thấy)")
    except Exception as e:
        print(f"  ⚠ forHandle lookup failed: {e}")

    # 4. Also try searching by known custom URL patterns
    for handle in ["zenpham-g3l", "realitydecode"]:
        try:
            resp4 = yt.channels().list(part="snippet", forHandle=handle).execute()
            for item in resp4.get("items", []):
                ch_id = item["id"]
                title = item["snippet"]["title"]
                custom = item["snippet"].get("customUrl", "N/A")
                if ch_id not in results:
                    print(f"  📍 {title} ({custom}) — ID: {ch_id}")
                    results[ch_id] = {"title": title, "customUrl": custom, "source": f"forHandle({handle})"}
        except Exception:
            pass

    # 5. Try direct API call to list all channels accessible via this token
    print("\n" + "=" * 60)
    print("🔗 Sử dụng raw HTTP để kiểm tra channel delegation:")
    print("=" * 60)
    try:
        import requests
        token = creds.token
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {"part": "snippet,statistics", "mine": "true"}
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, params=params, headers=headers)
        data = r.json()
        for item in data.get("items", []):
            ch_id = item["id"]
            title = item["snippet"]["title"]
            print(f"  🔑 Raw API: {title} — ID: {ch_id}")
    except Exception as e:
        print(f"  ⚠ Raw API call failed: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Tổng cộng: {len(results)} kênh được tìm thấy")
    print("=" * 60)
    return results


if __name__ == "__main__":
    token_file = sys.argv[1] if len(sys.argv) > 1 else str(HERMES_HOME / "google_token_phamtrai_dialy.json")
    token_path = Path(token_file)
    if not token_path.exists():
        print(f"Token file not found: {token_path}")
        sys.exit(1)

    print(f"Loading token from: {token_path}\n")
    creds = load_credentials(token_path)
    channels = list_channels(creds)
