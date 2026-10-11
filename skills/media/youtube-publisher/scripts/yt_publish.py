#!/usr/bin/env python3
"""YouTube Publisher — upload, captions, thumbnails, playlists, metadata, and automated SEO."""
import argparse
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

# Add script directory and repo root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(REPO_ROOT))

try:
    from seo_metadata import build_seo_metadata, detect_channel, resolve_channel_token
except ImportError:
    # Fallback if invoked from arbitrary working directory
    from skills.media.youtube_publisher.scripts.seo_metadata import (
        build_seo_metadata,
        detect_channel,
        resolve_channel_token,
    )


def normalize_title(title: str) -> str:
    return unicodedata.normalize("NFC", title)


def shorts_title(title: str) -> str:
    title = normalize_title(title).strip()
    return title if "#shorts" in title.casefold() else f"{title} #Shorts"


def find_candidate_thumbnail(video_path=None, md_path=None, explicit_thumb=None):
    """Auto-discover matching thumbnail for video if not passed explicitly."""
    if explicit_thumb:
        p = Path(explicit_thumb)
        return p if p.exists() else None

    search_dirs = []
    if video_path and Path(video_path).parent.exists():
        search_dirs.append(Path(video_path).parent)
    if md_path and Path(md_path).parent.exists():
        search_dirs.append(Path(md_path).parent)
        search_dirs.append(Path(md_path).parent / "output")
    search_dirs.append(REPO_ROOT / "assets/scripts_video/output")
    search_dirs.append(REPO_ROOT / "storage/media_bank/thumbnails")

    stems = []
    if video_path:
        vstem = Path(video_path).stem
        stems.extend([vstem, vstem.replace("_final", ""), vstem.replace("_telegram", "")])
    if md_path:
        stems.append(Path(md_path).stem)

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for stem in stems:
            for pat in [
                f"thumb_{stem}.jpg",
                f"thumb_{stem}.png",
                f"{stem}_thumb.jpg",
                f"{stem}.jpg",
                f"{stem}.png",
            ]:
                candidate = s_dir / pat
                if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 10_000:
                    return candidate

    return None


def validate_preflight_qa(
    video_path,
    thumbnail_path=None,
    title="",
    description="",
    tags=None,
    category_id="27",
    allow_no_thumbnail=False,
    skip_qa_gate=False,
):
    """
    Validate all pre-flight standards before YouTube upload.
    Returns dictionary with QA status and details.
    Raises ValueError with actionable instructions if any mandatory check fails.
    """
    qa_results = {
        "passed": True,
        "checks": {},
        "errors": [],
        "warnings": [],
    }
    if skip_qa_gate:
        qa_results["checks"]["qa_gate"] = "SKIPPED"
        return qa_results

    tags_list = tags or []

    # 1. THUMBNAIL CHECK
    if not thumbnail_path or not Path(thumbnail_path).exists():
        if allow_no_thumbnail:
            qa_results["checks"]["thumbnail"] = "WARNING: Missing thumbnail (allowed via flag)"
            qa_results["warnings"].append("No thumbnail provided (--allow-no-thumbnail)")
        else:
            qa_results["passed"] = False
            qa_results["checks"]["thumbnail"] = "FAIL: Missing thumbnail"
            qa_results["errors"].append(
                "MANDATORY THUMBNAIL MISSING: YouTube Publishing Rules require an approved cover thumbnail. "
                "Generate one via cover_design_engine.py or specify --thumbnail /path/to/thumb.jpg."
            )
    else:
        tpath = Path(thumbnail_path)
        thumb_size = tpath.stat().st_size
        if thumb_size > 2 * 1024 * 1024:
            qa_results["passed"] = False
            qa_results["checks"]["thumbnail"] = f"FAIL: Thumbnail file size {thumb_size // 1024}KB exceeds 2MB limit"
            qa_results["errors"].append(f"Thumbnail {tpath.name} exceeds YouTube limit of 2MB ({thumb_size} bytes).")
        else:
            try:
                from PIL import Image
                with Image.open(tpath) as im:
                    w, h = im.size
                    if w < 1280 and h < 1280:
                        qa_results["passed"] = False
                        qa_results["checks"]["thumbnail"] = f"FAIL: Resolution {w}x{h} below minimum 1280x720/720x1280"
                        qa_results["errors"].append(f"Thumbnail resolution {w}x{h} too low. Minimum is 1280x720.")
                    else:
                        qa_results["checks"]["thumbnail"] = f"PASS ({w}x{h}, {thumb_size // 1024}KB)"
            except Exception:
                qa_results["checks"]["thumbnail"] = f"PASS ({thumb_size // 1024}KB)"

    # 2. TITLE CHECK
    norm_title = unicodedata.normalize("NFC", (title or "").strip())
    if not norm_title:
        qa_results["passed"] = False
        qa_results["checks"]["title"] = "FAIL: Empty title"
        qa_results["errors"].append("Video title is required and cannot be empty.")
    elif len(norm_title) > 100:
        qa_results["passed"] = False
        qa_results["checks"]["title"] = f"FAIL: Title length {len(norm_title)} > 100 characters"
        qa_results["errors"].append(f"Video title is {len(norm_title)} characters (YouTube max is 100).")
    elif len(norm_title) > 70:
        qa_results["checks"]["title"] = f"PASS with WARNING: Title length {len(norm_title)} > 70 chars (Mobile truncation risk)"
        qa_results["warnings"].append("Title exceeds 70 characters; may be truncated on mobile YouTube feeds.")
    else:
        qa_results["checks"]["title"] = f"PASS ({len(norm_title)} chars, Mobile-First)"

    # 3. DESCRIPTION & CHAPTERS CHECK
    desc = (description or "").strip()
    is_short_video = (
        "#shorts" in (title or "").lower()
        or (tags_list and any("short" in str(t).lower() for t in tags_list))
    )
    if not desc or len(desc) < 50:
        qa_results["passed"] = False
        qa_results["checks"]["description"] = "FAIL: Empty or too short description"
        qa_results["errors"].append("Description must be detailed and at least 50 characters.")
    elif not is_short_video and "00:00" not in desc:
        qa_results["passed"] = False
        qa_results["checks"]["description"] = "FAIL: Missing starting chapter '00:00'"
        qa_results["errors"].append("Description must include video chapters starting at '00:00'.")
    else:
        desc_label = "Shorts format verified" if is_short_video else "Chapters starting at 00:00 found"
        qa_results["checks"]["description"] = f"PASS ({len(desc)} chars, {desc_label})"

    # 4. TAGS CHECK
    total_tag_chars = sum(len(t) for t in tags_list) + max(0, (len(tags_list) - 1) * 2) if tags_list else 0
    if not tags_list:
        qa_results["passed"] = False
        qa_results["checks"]["tags"] = "FAIL: Empty tags list"
        qa_results["errors"].append("Video must have keyword tags (minimum 1 tag).")
    elif total_tag_chars > 500:
        qa_results["passed"] = False
        qa_results["checks"]["tags"] = f"FAIL: Tags total length {total_tag_chars} > 500 characters limit"
        qa_results["errors"].append(f"Tags exceed 500 characters ({total_tag_chars} chars).")
    else:
        qa_results["checks"]["tags"] = f"PASS ({len(tags_list)} tags, {total_tag_chars}/500 chars)"

    # 5. CATEGORY CHECK
    if not category_id or not str(category_id).isdigit():
        qa_results["passed"] = False
        qa_results["checks"]["category"] = f"FAIL: Invalid category ID '{category_id}'"
        qa_results["errors"].append(f"Invalid category ID: {category_id}.")
    else:
        qa_results["checks"]["category"] = f"PASS (Category ID: {category_id})"

    if not qa_results["passed"]:
        error_msg = "[PRE-FLIGHT QA HARD STOP]\n" + "\n".join(f" - {err}" for err in qa_results["errors"])
        raise ValueError(error_msg)

    return qa_results


def _get_credentials(token_override=None, channel=None):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        print(json.dumps({"status": "error", "error": "Missing dependencies. Run: uv pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"}))
        sys.exit(1)

    token_path, is_specific = resolve_channel_token(channel=channel or "ZENPHAM", override_path=token_override)
    if not token_path.exists():
        print(json.dumps({
            "status": "error",
            "error": f"YouTube token not found. Expected at {token_path}. Run YouTube setup first."
        }))
        sys.exit(1)

    with open(token_path, encoding="utf-8") as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)
    return creds, token_path


def _get_youtube_service(token_override=None, channel=None):
    from googleapiclient.discovery import build
    creds, token_path = _get_credentials(token_override=token_override, channel=channel)
    return build("youtube", "v3", credentials=creds, static_discovery=True), token_path


def _error(error):
    print(json.dumps({"status": "error", "error": str(error)}))
    sys.exit(1)


def cmd_check(args):
    try:
        channel_name = getattr(args, "channel", None)
        token_file = getattr(args, "token_file", None)
        service, token_path = _get_youtube_service(token_override=token_file, channel=channel_name)
        response = service.channels().list(part="snippet,statistics", mine=True).execute()
        if not response.get("items"):
            raise RuntimeError("No YouTube channel found for this account")
        channel = response["items"][0]
        print(json.dumps({
            "status": "ok",
            "channel": channel["snippet"]["title"],
            "channel_id": channel["id"],
            "subscriber_count": channel.get("statistics", {}).get("subscriberCount", "N/A"),
            "token_path": str(token_path),
        }))
    except Exception as e:
        _error(e)


def cmd_upload(args):
    from googleapiclient.http import MediaFileUpload

    video_path = Path(args.video)
    if not video_path.exists() and not getattr(args, "dry_run", False):
        _error(f"Video not found: {video_path}")

    # Hard Publishing Safety Gate (Single Source of Truth enforcement)
    resolved_video_str = str(video_path.resolve())
    forbidden_markers = ["/_archive/", "/manim_production_stack/", "/legacy_", "/poc_"]
    for marker in forbidden_markers:
        if marker in resolved_video_str:
            _error(f"HARD SAFETY GATE TRIGGERED: Video is inside an archived/legacy path ('{marker}'): {video_path}. Publishing forbidden!")

    # Process script markdown if provided
    md_metadata = {}
    related_long_id = getattr(args, "related_long_id", None)
    related_short_id = getattr(args, "related_short_id", None)
    if getattr(args, "md", None):
        md_file = Path(args.md)
        if not md_file.exists():
            _error(f"Script markdown not found: {md_file}")
        md_metadata = build_seo_metadata(
            md_file,
            related_longform_id=related_long_id,
            related_short_id=related_short_id
        )

    channel = getattr(args, "channel", None) or md_metadata.get("channel", "ZENPHAM")
    token_file = getattr(args, "token_file", None)
    if not token_file and md_metadata:
        token_file = md_metadata.get("token_path")

    # Resolve Title
    title = args.title or md_metadata.get("title", "")
    if not title:
        _error("Video title is required (either provide --title or --md <script.md>)")

    if args.shorts or (md_metadata and not md_metadata.get("is_landscape", True)):
        title = shorts_title(title)
    else:
        title = normalize_title(title)

    # Resolve Description & Tags
    description = args.description if args.description else md_metadata.get("description", "")
    if args.tags:
        tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
    else:
        tags_list = md_metadata.get("tags", [])

    category_id = str(args.category) if args.category != 27 or "category_id" not in md_metadata else md_metadata.get("category_id", "27")
    privacy = args.privacy or "public"

    # Resolve thumbnail (explicit or auto-discovery)
    md_path = Path(args.md) if getattr(args, "md", None) else None
    thumb_path = find_candidate_thumbnail(video_path, md_path, getattr(args, "thumbnail", None))

    # Pre-Flight QA Gate Validation
    qa_report = {}
    try:
        qa_report = validate_preflight_qa(
            video_path=video_path,
            thumbnail_path=thumb_path,
            title=title,
            description=description,
            tags=tags_list,
            category_id=category_id,
            allow_no_thumbnail=getattr(args, "allow_no_thumbnail", False),
            skip_qa_gate=getattr(args, "skip_qa_gate", False),
        )
    except ValueError as ve:
        _error(str(ve))

    # DRY-RUN: Output payload for inspection without uploading
    if getattr(args, "dry_run", False):
        print(json.dumps({
            "status": "dry_run",
            "channel": channel,
            "token_path": str(token_file),
            "title": title,
            "title_length": len(title),
            "description_preview": description[:300] + "...",
            "description_total_chars": len(description),
            "tags_count": len(tags_list),
            "tags_total_chars": sum(len(t) for t in tags_list) + max(0, (len(tags_list) - 1) * 2),
            "tags": tags_list,
            "category_id": category_id,
            "privacy": privacy,
            "video": str(video_path),
            "thumbnail": str(thumb_path) if thumb_path else None,
            "qa_checklist": qa_report.get("checks", {}),
            "qa_warnings": qa_report.get("warnings", []),
        }, ensure_ascii=False, indent=2))
        return

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags_list,
            "categoryId": category_id,
            "defaultLanguage": args.language or "vi",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        }
    }
    if args.publish_at:
        body["status"]["publishAt"] = args.publish_at

    mime_type = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
    }.get(video_path.suffix.lower(), "video/mp4")

    youtube, token_used = _get_youtube_service(token_override=token_file, channel=channel)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(video_path), mimetype=mime_type, resumable=True, chunksize=10 * 1024 * 1024)
    )
    response = None
    for retries in range(4):
        try:
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%", file=sys.stderr)
            break
        except Exception as e:
            if retries == 3:
                _error(f"Upload failed after 3 retries: {e}")
            print(f"Upload error, retrying in {2 ** (retries + 1)}s... ({e})", file=sys.stderr)
            time.sleep(2 ** (retries + 1))

    video_id = response["id"]
    result = {
        "status": "ok",
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "privacy": privacy,
        "title": title,
        "channel": channel,
        "token_used": str(token_used),
    }
    if thumb_path and thumb_path.exists():
        try:
            mime = "image/jpeg" if thumb_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumb_path), mimetype=mime)
            ).execute()
            result["thumbnail"] = "set"
            result["thumbnail_file"] = str(thumb_path)
        except Exception as e:
            result["thumbnail_error"] = str(e)

    # Post Author CTA Comment if related longform/short ID is linked
    if related_long_id:
        try:
            long_url = f"https://youtube.com/watch?v={related_long_id}"
            cta_text = (
                f"🎬 Xem trọn vẹn bản phân tích toán học & code Manim 3D của tập này tại video dài: {long_url}\n"
                f"🔔 Đăng ký kênh @zenpham để không bỏ lỡ chuỗi bài 'Tôi Làm Việc'!"
            )
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {"snippet": {"textOriginal": cta_text}}
                    }
                }
            ).execute()
            result["pinned_cta_comment"] = "posted"
        except Exception as ce:
            result["comment_notice"] = str(ce)
    elif related_short_id:
        try:
            short_url = f"https://youtube.com/shorts/{related_short_id}"
            short_notice = (
                f"📱 Bạn bận rộn? Xem tóm tắt nhanh 30s của tập này tại: {short_url}\n"
                f"💬 Hãy để lại góc nhìn của bạn về bài toán này dưới phần bình luận nhé!"
            )
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {"snippet": {"textOriginal": short_notice}}
                    }
                }
            ).execute()
            result["short_comment"] = "posted"
        except Exception as ce:
            result["comment_notice"] = str(ce)

    print(json.dumps(result, ensure_ascii=False))


def cmd_captions_upload(args):
    from googleapiclient.http import MediaFileUpload
    captions = Path(args.captions)
    if not captions.is_file():
        _error(f"Caption file not found: {captions}")
    if captions.suffix.lower() != ".srt":
        _error(f"Captions must be a valid .srt file: {captions}")
    try:
        service, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        response = service.captions().insert(
            part="snippet",
            body={"snippet": {"videoId": args.video_id, "language": args.language, "name": args.name or captions.stem, "isDraft": args.draft}},
            media_body=MediaFileUpload(str(captions), mimetype="application/x-subrip", resumable=True)
        ).execute()
        print(json.dumps({"status": "ok", "video_id": args.video_id, "caption_id": response["id"], "language": args.language}))
    except Exception as e:
        _error(e)


def cmd_video_update_title(args):
    try:
        youtube, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        items = youtube.videos().list(part="snippet", id=args.video_id).execute().get("items", [])
        if not items:
            raise RuntimeError(f"Video not found: {args.video_id}")
        snippet = items[0]["snippet"]
        snippet["title"] = normalize_title(args.title)
        youtube.videos().update(part="snippet", body={"id": args.video_id, "snippet": snippet}).execute()
        print(json.dumps({"status": "ok", "video_id": args.video_id, "title": snippet["title"]}))
    except Exception as e:
        _error(e)


def cmd_video_update_metadata(args):
    try:
        md_metadata = {}
        if getattr(args, "md", None):
            md_file = Path(args.md)
            if not md_file.exists():
                _error(f"Script markdown not found: {md_file}")
            md_metadata = build_seo_metadata(md_file)

        channel = getattr(args, "channel", None) or md_metadata.get("channel", "ZENPHAM")
        token_file = getattr(args, "token_file", None) or md_metadata.get("token_path")

        youtube, token_used = _get_youtube_service(token_override=token_file, channel=channel)
        items = youtube.videos().list(part="snippet", id=args.video_id).execute().get("items", [])
        if not items:
            raise RuntimeError(f"Video not found: {args.video_id}")

        snippet = items[0]["snippet"]
        title = args.title or md_metadata.get("title", "")
        if title:
            snippet["title"] = normalize_title(title)

        desc = args.description if args.description else md_metadata.get("description", "")
        if desc:
            snippet["description"] = desc

        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else md_metadata.get("tags", [])
        if tags:
            snippet["tags"] = tags

        if getattr(args, "category", None) or "category_id" in md_metadata:
            cat_id = str(args.category) if getattr(args, "category", None) else md_metadata.get("category_id")
            if cat_id:
                snippet["categoryId"] = cat_id

        if getattr(args, "dry_run", False):
            print(json.dumps({
                "status": "dry_run_update",
                "video_id": args.video_id,
                "title": snippet.get("title"),
                "description_preview": snippet.get("description", "")[:250] + "...",
                "tags_count": len(snippet.get("tags", [])),
                "tags": snippet.get("tags", []),
                "token_used": str(token_used)
            }, ensure_ascii=False, indent=2))
            return

        youtube.videos().update(part="snippet", body={"id": args.video_id, "snippet": snippet}).execute()
        print(json.dumps({
            "status": "ok",
            "video_id": args.video_id,
            "title": snippet["title"],
            "tags_count": len(snippet.get("tags", [])),
            "updated_with_seo": True
        }, ensure_ascii=False))
    except Exception as e:
        _error(e)


def cmd_delete(args):
    try:
        service, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        service.videos().delete(id=args.video_id).execute()
        print(json.dumps({"status": "ok", "deleted": args.video_id}))
    except Exception as e:
        _error(e)


def cmd_thumbnail(args):
    from googleapiclient.http import MediaFileUpload
    image = Path(args.image)
    if not image.is_file():
        _error(f"Image not found: {image}")
    try:
        youtube, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        youtube.thumbnails().set(videoId=args.video_id, media_body=MediaFileUpload(str(image), mimetype="image/jpeg")).execute()
        print(json.dumps({"status": "ok", "video_id": args.video_id, "thumbnail": "set"}))
    except Exception as e:
        _error(e)


def cmd_playlists(args):
    try:
        service, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        items = service.playlists().list(part="snippet,contentDetails", mine=True, maxResults=50).execute().get("items", [])
        print(json.dumps({
            "status": "ok",
            "playlists": [{"id": i["id"], "title": i["snippet"]["title"], "description": i["snippet"].get("description", ""), "count": i.get("contentDetails", {}).get("itemCount", 0)} for i in items]
        }))
    except Exception as e:
        _error(e)


def cmd_playlist_create(args):
    try:
        service, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        response = service.playlists().insert(
            part="snippet,status",
            body={"snippet": {"title": normalize_title(args.title), "description": args.description or ""}, "status": {"privacyStatus": args.privacy}}
        ).execute()
        print(json.dumps({"status": "ok", "playlist_id": response["id"], "title": response["snippet"]["title"]}))
    except Exception as e:
        _error(e)


def cmd_playlist_add(args):
    try:
        service, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        service.playlistItems().insert(
            part="snippet",
            body={"snippet": {"playlistId": args.playlist_id, "resourceId": {"kind": "youtube#video", "videoId": args.video_id}}}
        ).execute()
        print(json.dumps({"status": "ok", "playlist_id": args.playlist_id, "video_id": args.video_id}))
    except Exception as e:
        _error(e)


def cmd_comment(args):
    """Post an author comment on a video."""
    try:
        service, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        body = {
            "snippet": {
                "videoId": args.video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": args.text
                    }
                }
            }
        }
        res = service.commentThreads().insert(part="snippet", body=body).execute()
        print(json.dumps({
            "status": "ok",
            "video_id": args.video_id,
            "comment_id": res["id"],
            "text": args.text
        }, ensure_ascii=False))
    except Exception as e:
        _error(e)


def cmd_link_short(args):
    """
    Bidirectionally links a 16:9 Long-form episode and a 9:16 Micro-Short:
    1. Updates Short description to include direct link to Long-form.
    2. Updates Long-form description to include direct link to Short.
    3. Posts author CTA comment on Short pointing to Long-form.
    4. Posts author comment on Long-form pointing to Short.
    5. Outputs confirmation and YouTube Studio guidance.
    """
    try:
        service, _ = _get_youtube_service(token_override=getattr(args, "token_file", None), channel=getattr(args, "channel", None))
        long_id = args.long_id
        short_id = args.short_id

        # 1. Fetch Long-form video snippet
        long_res = service.videos().list(part="snippet", id=long_id).execute()
        if not long_res.get("items"):
            _error(f"Long-form video not found: {long_id}")
        long_item = long_res["items"][0]
        long_snippet = long_item["snippet"]

        # 2. Fetch Short video snippet
        short_res = service.videos().list(part="snippet", id=short_id).execute()
        if not short_res.get("items"):
            _error(f"Short video not found: {short_id}")
        short_item = short_res["items"][0]
        short_snippet = short_item["snippet"]

        short_url = f"https://youtube.com/shorts/{short_id}"
        long_url = f"https://youtube.com/watch?v={long_id}"

        # 3. Update Short Description
        short_desc = short_snippet["description"]
        if long_id not in short_desc:
            short_link_block = (
                f"─────────────────────────────────────────\n"
                f"👉 XEM BẢN PHÂN TÍCH TOÁN HỌC CHI TIẾT & MÃ NGUỒN MANIM 3D TẠI:\n"
                f"🔗 {long_url}\n"
                f"─────────────────────────────────────────\n\n"
            )
            short_snippet["description"] = short_link_block + short_desc
            service.videos().update(part="snippet", body={"id": short_id, "snippet": short_snippet}).execute()
            print(f"[OK] Updated Short ({short_id}) description with Long-form link: {long_url}", file=sys.stderr)

        # 4. Update Long-form Description
        long_desc = long_snippet["description"]
        if short_id not in long_desc:
            short_notice = f"\n📱 Xem tóm tắt nhanh 30s của tập này: {short_url}\n"
            if "─────────────────────────────────────────" in long_desc:
                parts = long_desc.split("─────────────────────────────────────────", 1)
                long_snippet["description"] = parts[0] + short_notice + "─────────────────────────────────────────" + parts[1]
            else:
                long_snippet["description"] = short_notice + long_desc
            service.videos().update(part="snippet", body={"id": long_id, "snippet": long_snippet}).execute()
            print(f"[OK] Updated Long-form ({long_id}) description with Short link: {short_url}", file=sys.stderr)

        # 5. Post Author CTA Comment on Short
        short_comment_text = (
            f"🎬 Xem trọn vẹn bản phân tích toán học & code Manim của tập này tại video dài: {long_url}\n"
            f"🔔 Đăng ký kênh @zenpham để không bỏ lỡ chuỗi bài 'Tôi Làm Việc'!"
        )
        try:
            service.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": short_id,
                        "topLevelComment": {"snippet": {"textOriginal": short_comment_text}}
                    }
                }
            ).execute()
            print(f"[OK] Posted author CTA comment on Short ({short_id})", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Could not post comment on Short: {e}", file=sys.stderr)

        # 6. Post Author Comment on Long-form
        long_comment_text = (
            f"📱 Bạn bận rộn? Xem tóm tắt nhanh 30s của tập này tại: {short_url}\n"
            f"💬 Hãy để lại câu hỏi hoặc chia sẻ góc nhìn của bạn về bài toán này nhé!"
        )
        try:
            service.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": long_id,
                        "topLevelComment": {"snippet": {"textOriginal": long_comment_text}}
                    }
                }
            ).execute()
            print(f"[OK] Posted author comment on Long-form ({long_id})", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Could not post comment on Long-form: {e}", file=sys.stderr)

        print(json.dumps({
            "status": "ok",
            "linked": True,
            "long_id": long_id,
            "short_id": short_id,
            "long_url": long_url,
            "short_url": short_url,
            "youtube_studio_instruction": f"Vào YouTube Studio -> Chi tiết Short ({short_id}) -> Mục 'Video có liên quan' (Related video) -> Chọn video dài: {long_id} để kích hoạt pill bấm trực tiếp trên giao diện Shorts điện thoại!"
        }, ensure_ascii=False, indent=2))
    except Exception as e:
        _error(e)


def main():
    parser = argparse.ArgumentParser(description="YouTube Publisher with Automatic SEO")
    parser.add_argument("--check", action="store_true", help="Check YouTube API connectivity")
    parser.add_argument("--channel", help="Target channel ('TOI_DOC_SACH' or 'ZENPHAM')")
    parser.add_argument("--token-file", help="Path to specific OAuth token file")

    commands = parser.add_subparsers(dest="command")

    # UPLOAD command
    p = commands.add_parser("upload", help="Upload a video with automated or custom SEO")
    p.add_argument("--video", required=True, help="Path to video file")
    p.add_argument("--md", help="Path to script markdown to auto-generate Title, Tags, Description and detect Channel")
    p.add_argument("--title", help="Custom video title (overrides --md)")
    p.add_argument("--description", default="", help="Custom description (overrides --md)")
    p.add_argument("--tags", default="", help="Custom comma-separated tags (overrides --md)")
    p.add_argument("--category", type=int, default=27, help="YouTube category ID (default 27 for Education)")
    p.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"], help="Video privacy")
    p.add_argument("--publish-at", help="Scheduled publish time (ISO 8601)")
    p.add_argument("--thumbnail", help="Path to custom thumbnail image")
    p.add_argument("--language", default="vi", help="Default language (default 'vi')")
    p.add_argument("--shorts", action="store_true", help="Force Shorts format (#Shorts in title)")
    p.add_argument("--related-long-id", help="Video ID of paired long-form episode (for Shorts)")
    p.add_argument("--related-short-id", help="Video ID of paired 30s Short (for Long-form)")
    p.add_argument("--channel", help="Target channel ('TOI_DOC_SACH', 'ZENPHAM', 'PHAMTRAI_DIALY', or 'REALITY_DECODE')")
    p.add_argument("--token-file", help="Path to specific OAuth token file")
    p.add_argument("--allow-no-thumbnail", action="store_true", help="Allow upload without thumbnail (emergency/debug only)")
    p.add_argument("--skip-qa-gate", action="store_true", help="Skip Pre-flight QA validation (debug only)")
    p.add_argument("--dry-run", action="store_true", help="Preview SEO metadata payload and QA checklist without uploading")

    # CAPTIONS command
    p = commands.add_parser("captions-upload", help="Upload SRT captions")
    p.add_argument("--video-id", required=True)
    p.add_argument("--captions", required=True)
    p.add_argument("--language", default="vi")
    p.add_argument("--name", default=None)
    p.add_argument("--draft", action="store_true")
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")

    # VIDEO UPDATE TITLE command
    p = commands.add_parser("video-update-title", help="Update an existing video title")
    p.add_argument("--video-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")

    # VIDEO UPDATE METADATA (Full SEO update) command
    p = commands.add_parser("video-update-metadata", help="Update existing video with complete SEO metadata via markdown")
    p.add_argument("--video-id", required=True)
    p.add_argument("--md", help="Path to script markdown to auto-generate Title, Tags, Description")
    p.add_argument("--title", help="Override title")
    p.add_argument("--description", default="", help="Override description")
    p.add_argument("--tags", default="", help="Override tags")
    p.add_argument("--category", type=int, default=None)
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")
    p.add_argument("--dry-run", action="store_true", help="Preview metadata changes without updating API")

    # DELETE command
    p = commands.add_parser("delete", help="Delete a video permanently")
    p.add_argument("--video-id", required=True)
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")

    # THUMBNAIL command
    p = commands.add_parser("thumbnail", help="Set thumbnail for existing video")
    p.add_argument("--video-id", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")

    # PLAYLISTS commands
    p = commands.add_parser("playlists", help="List playlists")
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")

    p = commands.add_parser("playlist-create", help="Create a playlist")
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--privacy", default="public")
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")

    p = commands.add_parser("playlist-add", help="Add a video to a playlist")
    p.add_argument("--playlist-id", required=True)
    p.add_argument("--video-id", required=True)
    p.add_argument("--channel", help="Target channel")
    p.add_argument("--token-file", help="OAuth token file")

    # COMMENT command
    p = commands.add_parser("comment", help="Post an author comment on a video")
    p.add_argument("--video-id", required=True, help="Target video ID")
    p.add_argument("--text", required=True, help="Comment text")
    p.add_argument("--channel", help="Target channel ('TOI_DOC_SACH', 'ZENPHAM', 'PHAMTRAI_DIALY', or 'REALITY_DECODE')")
    p.add_argument("--token-file", help="OAuth token file")

    # LINK-SHORT command
    p = commands.add_parser("link-short", help="Bidirectionally link a 16:9 episode and a 9:16 short")
    p.add_argument("--long-id", required=True, help="YouTube Video ID of 16:9 Longform episode")
    p.add_argument("--short-id", required=True, help="YouTube Video ID of 9:16 Short")
    p.add_argument("--channel", help="Target channel ('TOI_DOC_SACH', 'ZENPHAM', 'PHAMTRAI_DIALY', or 'REALITY_DECODE')")
    p.add_argument("--token-file", help="OAuth token file")

    args = parser.parse_args()
    if args.check:
        cmd_check(args)
    elif args.command == "upload":
        cmd_upload(args)
    elif args.command == "captions-upload":
        cmd_captions_upload(args)
    elif args.command == "video-update-title":
        cmd_video_update_title(args)
    elif args.command == "video-update-metadata":
        cmd_video_update_metadata(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "thumbnail":
        cmd_thumbnail(args)
    elif args.command == "comment":
        cmd_comment(args)
    elif args.command == "link-short":
        cmd_link_short(args)
    elif args.command == "playlists":
        cmd_playlists(args)
    elif args.command == "playlist-create":
        cmd_playlist_create(args)
    elif args.command == "playlist-add":
        cmd_playlist_add(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
