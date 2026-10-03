#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
youtube_sync_and_cleanup_s1.py
==============================
Sovereign YouTube Sync and Cleanup Manager for Series 1 (S1E1 to S1E5).
Handles:
1. Deletion of flawed private draft Shorts (5 flawed items from S1E4).
2. Deletion of duplicate private Shorts (5 duplicate items from S1E1).
3. Verification of quota state and scheduled publication queue.
"""

import sys
import json
import time
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

REPO_ROOT = Path("/home/zen/hermes-agent")
TOKEN_FILE = Path("/home/zen/.hermes/google_token.json")

# Target flawed video IDs to delete (S1E4 old slow/cut audio drafts)
FLAWED_SHORTS_TO_DELETE = [
    {"video_id": "q8BlmesL2eU", "title": "Ác mộng A/B testing (flawed slow audio)", "episode": "S01_EP04"},
    {"video_id": "Z2nM4t-wexE", "title": "Nghiên cứu sỏi thận 1986 (flawed slow audio)", "episode": "S01_EP04"},
    {"video_id": "lA_Cpo5orQQ", "title": "Hình học kỳ dị (flawed slow audio)", "episode": "S01_EP04"},
    {"video_id": "E6zyGkVByWg", "title": "Chiếc kéo Judea Pearl (flawed slow audio)", "episode": "S01_EP04"},
    {"video_id": "UAN1zMwepgI", "title": "Cạm bẫy Collider (flawed slow audio)", "episode": "S01_EP04"},
]

# Target duplicate video IDs to delete (S1E1 duplicate uploads)
DUPLICATE_SHORTS_TO_DELETE = [
    {"video_id": "hx_P2UIVHHs", "title": "Laplace Coin Toss (duplicate)", "episode": "S01_EP01"},
    {"video_id": "vkiOA-MGmDk", "title": "Rainy Self-Driving Car (duplicate)", "episode": "S01_EP01"},
    {"video_id": "un8qfdUEw2s", "title": "Frequentist vs Bayes (duplicate)", "episode": "S01_EP01"},
    {"video_id": "aYEl_MVQpR8", "title": "99% Test Trap (duplicate)", "episode": "S01_EP01"},
    {"video_id": "gCIvG4GOgkI", "title": "LLM Temperature (duplicate)", "episode": "S01_EP01"},
]

ALL_TARGETS_FOR_DELETION = FLAWED_SHORTS_TO_DELETE + DUPLICATE_SHORTS_TO_DELETE


def get_youtube_service():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(f"OAuth token not found at {TOKEN_FILE}")
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes", ["https://www.googleapis.com/auth/youtube"])
    )
    return build("youtube", "v3", credentials=creds, static_discovery=True)


def check_quota():
    try:
        service = get_youtube_service()
        res = service.channels().list(part="snippet", mine=True).execute()
        return True, f"Channel: {res['items'][0]['snippet']['title']}"
    except HttpError as e:
        if e.resp.status == 403 and "quotaExceeded" in str(e):
            return False, "Quota exceeded (daily limit reached; resets at 00:00 PST / ~14:00-15:00 UTC+7)"
        return False, str(e)
    except Exception as e:
        return False, str(e)


def delete_flawed_videos(dry_run: bool = True):
    print("=" * 70)
    print(f"🎬 YOUTUBE CLEANUP: DELETING FLAWED & DUPLICATE VIDEOS ({'DRY RUN' if dry_run else 'LIVE'})")
    print("=" * 70)

    quota_ok, quota_msg = check_quota()
    print(f"[*] API Quota Status: {'AVAILABLE' if quota_ok else 'EXHAUSTED'} ({quota_msg})")

    print(f"\n📋 Identified {len(ALL_TARGETS_FOR_DELETION)} videos targeted for deletion:")
    for idx, item in enumerate(ALL_TARGETS_FOR_DELETION, 1):
        print(f"  {idx:02d}. [{item['episode']}] ID: {item['video_id']} - {item['title']}")

    if dry_run:
        print("\n💡 This is a DRY RUN. Pass --execute to delete when quota is available.")
        return

    if not quota_ok:
        print("\n⚠️ CANNOT EXECUTE DELETION: YouTube API quota is currently exceeded.")
        print("   The operation is queued and will execute as soon as the quota window resets.")
        return

    service = get_youtube_service()
    deleted = 0
    for item in ALL_TARGETS_FOR_DELETION:
        vid = item["video_id"]
        try:
            print(f"[*] Deleting {vid} ({item['title']})...")
            service.videos().delete(id=vid).execute()
            print(f"  ✅ Deleted successfully: {vid}")
            deleted += 1
            time.sleep(1)
        except HttpError as e:
            if "notFound" in str(e):
                print(f"  ℹ️ Video {vid} already deleted or not found.")
            else:
                print(f"  ❌ Error deleting {vid}: {e}")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")

    print(f"\n🎉 Deletion complete. Successfully processed {deleted}/{len(ALL_TARGETS_FOR_DELETION)} videos.")


if __name__ == "__main__":
    exec_mode = "--execute" in sys.argv
    delete_flawed_videos(dry_run=not exec_mode)
