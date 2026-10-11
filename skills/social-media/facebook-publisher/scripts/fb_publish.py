#!/usr/bin/env python3
"""Facebook Publisher — Post text, photos, videos, reels to Facebook Pages.

Uses Meta Graph API v21.0 with Page Access Token.

Usage:
    python fb_publish.py post --message TEXT [--link URL] [--schedule ISO]
    python fb_publish.py photo --image FILE [--image FILE2] --caption TEXT
    python fb_publish.py video --video FILE --title TITLE --description DESC
    python fb_publish.py reel --video FILE --description DESC
    python fb_publish.py insights --metric METRIC --period PERIOD
    python fb_publish.py --check
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    # Fallback to urllib
    requests = None
    import urllib.request
    import urllib.error
    import urllib.parse


GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _load_credentials():
    """Load FB credentials from ~/.hermes/.env."""
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    env_path = Path(hermes_home) / ".env"

    creds = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if key in (
                        "FB_PAGE_ACCESS_TOKEN_PERSONAL",
                        "FB_PAGE_ID_PERSONAL",
                        "FB_PAGE_ACCESS_TOKEN_BIZ",
                        "FB_PAGE_ID_BIZ",
                        "META_APP_ID",
                        "META_APP_SECRET",
                    ):
                        creds[key] = value

    return creds


def _get_page_creds(brand="personal"):
    """Get page token and ID for the specified brand."""
    creds = _load_credentials()
    suffix = "PERSONAL" if brand == "personal" else "BIZ"

    token = creds.get(f"FB_PAGE_ACCESS_TOKEN_{suffix}")
    page_id = creds.get(f"FB_PAGE_ID_{suffix}")

    if not token:
        print(json.dumps({
            "status": "error",
            "error": f"FB_PAGE_ACCESS_TOKEN_{suffix} not found in ~/.hermes/.env"
        }))
        sys.exit(1)

    if not page_id:
        print(json.dumps({
            "status": "error",
            "error": f"FB_PAGE_ID_{suffix} not found in ~/.hermes/.env"
        }))
        sys.exit(1)

    return token, page_id


def _graph_request(method, endpoint, params=None, data=None, files=None, token=None):
    """Make a Graph API request."""
    url = f"{GRAPH_API_BASE}/{endpoint}"

    if params is None:
        params = {}
    if token:
        params["access_token"] = token

    if requests:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=60)
        elif method == "POST":
            if files:
                resp = requests.post(url, params=params, data=data, files=files, timeout=300)
            else:
                resp = requests.post(url, params=params, json=data, timeout=60)
        else:
            raise ValueError(f"Unsupported method: {method}")

        try:
            result = resp.json()
        except Exception:
            result = {"raw": resp.text}

        if resp.status_code == 429:
            # Rate limited — wait and retry
            wait = 60
            print(f"Rate limited, waiting {wait}s...", file=sys.stderr)
            time.sleep(wait)
            return _graph_request(method, endpoint, params, data, files, token)

        return result, resp.status_code
    else:
        # Fallback to urllib
        if method == "GET":
            query = urllib.parse.urlencode(params)
            req = urllib.request.Request(f"{url}?{query}")
        elif method == "POST" and not files:
            query = urllib.parse.urlencode(params)
            body = json.dumps(data or {}).encode()
            req = urllib.request.Request(
                f"{url}?{query}",
                data=body,
                headers={"Content-Type": "application/json"},
            )
        else:
            raise ValueError("File upload requires 'requests' package. Install with: pip install requests")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                return result, resp.status
        except urllib.error.HTTPError as e:
            result = json.loads(e.read()) if e.fp else {"error": str(e)}
            return result, e.code


def cmd_check(args):
    """Check Facebook API connectivity."""
    token, page_id = _get_page_creds(args.brand)

    result, status = _graph_request("GET", f"{page_id}", {"fields": "name,id,fan_count"}, token=token)

    if status == 200 and "name" in result:
        print(json.dumps({
            "status": "ok",
            "page": result["name"],
            "page_id": result["id"],
            "fans": result.get("fan_count", 0),
        }))
    else:
        error = result.get("error", {})
        print(json.dumps({
            "status": "error",
            "error": error.get("message", str(result)),
            "code": error.get("code", status),
        }))
        sys.exit(1)


def cmd_post(args):
    """Create a text post on the Page."""
    token, page_id = _get_page_creds(args.brand)

    data = {"message": args.message}

    if args.link:
        data["link"] = args.link

    if args.schedule:
        # Convert to Unix timestamp
        dt = datetime.fromisoformat(args.schedule)
        data["scheduled_publish_time"] = int(dt.timestamp())
        data["published"] = False

    result, status = _graph_request("POST", f"{page_id}/feed", data=data, token=token)

    if "id" in result:
        post_id = result["id"]
        output = {
            "status": "ok",
            "post_id": post_id,
            "url": f"https://facebook.com/{post_id.replace('_', '/posts/')}",
        }

        # Auto-comment if requested
        if args.first_comment:
            comment_data = {"message": args.first_comment}
            _graph_request("POST", f"{post_id}/comments", data=comment_data, token=token)
            output["first_comment"] = "posted"

        print(json.dumps(output))
    else:
        error = result.get("error", {})
        print(json.dumps({
            "status": "error",
            "error": error.get("message", str(result)),
            "code": error.get("code", status),
        }))
        sys.exit(1)


def cmd_photo(args):
    """Post photo(s) to the Page."""
    token, page_id = _get_page_creds(args.brand)

    if not requests:
        print(json.dumps({"status": "error", "error": "Photo upload requires 'requests' package"}))
        sys.exit(1)

    if len(args.image) == 1:
        # Single photo
        with open(args.image[0], "rb") as f:
            files = {"source": (Path(args.image[0]).name, f, "image/jpeg")}
            data = {"message": args.caption or ""}
            result, status = _graph_request("POST", f"{page_id}/photos", data=data, files=files, token=token)
    else:
        # Multi-photo album: upload each as unpublished, then create post with photo IDs
        photo_ids = []
        for img_path in args.image:
            with open(img_path, "rb") as f:
                files = {"source": (Path(img_path).name, f, "image/jpeg")}
                data = {"published": "false"}
                result, status = _graph_request("POST", f"{page_id}/photos", data=data, files=files, token=token)
                if "id" in result:
                    photo_ids.append(result["id"])

        # Create the album post
        data = {"message": args.caption or ""}
        for i, pid in enumerate(photo_ids):
            data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})

        result, status = _graph_request("POST", f"{page_id}/feed", data=data, token=token)

    if "id" in result:
        print(json.dumps({
            "status": "ok",
            "post_id": result["id"],
            "photo_count": len(args.image),
        }))
    else:
        error = result.get("error", {})
        print(json.dumps({"status": "error", "error": error.get("message", str(result))}))
        sys.exit(1)


def cmd_video(args):
    """Upload video to the Page using resumable upload."""
    token, page_id = _get_page_creds(args.brand)

    if not requests:
        print(json.dumps({"status": "error", "error": "Video upload requires 'requests' package"}))
        sys.exit(1)

    video_path = Path(args.video)
    if not video_path.exists():
        print(json.dumps({"status": "error", "error": f"Video not found: {video_path}"}))
        sys.exit(1)

    file_size = video_path.stat().st_size

    # Step 1: Start upload session
    data = {
        "upload_phase": "start",
        "file_size": file_size,
    }
    result, status = _graph_request("POST", f"{page_id}/videos", data=data, token=token)

    if "upload_session_id" not in result:
        print(json.dumps({"status": "error", "error": f"Failed to start upload: {result}"}))
        sys.exit(1)

    session_id = result["upload_session_id"]
    video_id = result.get("video_id")

    # Step 2: Transfer file
    with open(video_path, "rb") as f:
        files = {"video_file_chunk": (video_path.name, f, "video/mp4")}
        data = {
            "upload_phase": "transfer",
            "upload_session_id": session_id,
            "start_offset": "0",
        }
        result, status = _graph_request("POST", f"{page_id}/videos", data=data, files=files, token=token)

    # Step 3: Finish upload
    data = {
        "upload_phase": "finish",
        "upload_session_id": session_id,
        "title": args.title or "",
        "description": args.description or "",
    }
    result, status = _graph_request("POST", f"{page_id}/videos", data=data, token=token)

    if result.get("success"):
        print(json.dumps({
            "status": "ok",
            "video_id": video_id,
            "title": args.title,
        }))
    else:
        print(json.dumps({"status": "error", "error": str(result)}))
        sys.exit(1)


def cmd_reel(args):
    """Upload a Reel to the Page."""
    token, page_id = _get_page_creds(args.brand)

    if not requests:
        print(json.dumps({"status": "error", "error": "Reel upload requires 'requests' package"}))
        sys.exit(1)

    video_path = Path(args.video)
    if not video_path.exists():
        print(json.dumps({"status": "error", "error": f"Video not found: {video_path}"}))
        sys.exit(1)

    # Reels use the /video_reels endpoint
    with open(video_path, "rb") as f:
        files = {"source": (video_path.name, f, "video/mp4")}
        data = {"description": args.description or ""}
        result, status = _graph_request("POST", f"{page_id}/video_reels", data=data, files=files, token=token)

    if "id" in result:
        print(json.dumps({
            "status": "ok",
            "reel_id": result["id"],
        }))
    else:
        error = result.get("error", {})
        print(json.dumps({"status": "error", "error": error.get("message", str(result))}))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Facebook Page Publisher")
    parser.add_argument("--check", action="store_true", help="Check API connectivity")
    parser.add_argument("--brand", default="personal", choices=["personal", "biz"],
                        help="Which brand profile to use")

    subparsers = parser.add_subparsers(dest="command")

    # Post
    p_post = subparsers.add_parser("post", help="Create a text post")
    p_post.add_argument("--message", required=True, help="Post text")
    p_post.add_argument("--link", default=None, help="Link to attach")
    p_post.add_argument("--schedule", default=None, help="Schedule time (ISO 8601)")
    p_post.add_argument("--first-comment", default=None, help="Auto-comment after posting")

    # Photo
    p_photo = subparsers.add_parser("photo", help="Post photo(s)")
    p_photo.add_argument("--image", action="append", required=True, help="Path to image (repeat for multi)")
    p_photo.add_argument("--caption", default="", help="Photo caption")

    # Video
    p_video = subparsers.add_parser("video", help="Upload video")
    p_video.add_argument("--video", required=True, help="Path to video file")
    p_video.add_argument("--title", default="", help="Video title")
    p_video.add_argument("--description", default="", help="Video description")

    # Reel
    p_reel = subparsers.add_parser("reel", help="Upload Reel")
    p_reel.add_argument("--video", required=True, help="Path to video file")
    p_reel.add_argument("--description", default="", help="Reel description")

    args = parser.parse_args()

    if args.check:
        cmd_check(args)
    elif args.command == "post":
        cmd_post(args)
    elif args.command == "photo":
        cmd_photo(args)
    elif args.command == "video":
        cmd_video(args)
    elif args.command == "reel":
        cmd_reel(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
