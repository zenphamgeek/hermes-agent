---
name: youtube-publisher
description: Upload videos and manage playlists via YouTube Data API.
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
required_credential_files:
- path: google_token.json
  description: Google OAuth2 token with YouTube scope (created by google-workspace
    setup)
- path: google_client_secret.json
  description: Google OAuth2 client credentials
metadata:
  hermes:
    tags:
    - YouTube
    - Video
    - Upload
    - Publishing
    - Media
    related_skills:
    - youtube-content
    - google-workspace
    - media-studio
---
# YouTube Publisher

Upload videos, set custom thumbnails, manage playlists, and post to the Community
tab on YouTube — through Hermes-managed OAuth and the YouTube Data API v3.


## When to Use

Use this skill when:
- The user asks to upload videos and manage playlists via youtube data api.
- Executing automated youtube publisher workflows and tasks.

## Prerequisites

- Google OAuth2 token with YouTube scopes (via `google-workspace` skill setup with `--services youtube`)
- `google-api-python-client` and `google-auth-oauthlib` Python packages
- `YOUTUBE_API_KEY` in `~/.hermes/.env` (for read-only operations)
- `GCP_PROJECT_ID` in `~/.hermes/.env`

## Setup

If the `google-workspace` skill is already set up, just ensure the YouTube
Data API v3 is enabled in the GCP project and the token has YouTube scopes.

If not, run the google-workspace setup with YouTube services:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --auth-url --services youtube --format json
# User approves in browser, pastes redirect URL
$GSETUP --auth-code "REDIRECT_URL" --format json
$GSETUP --check
```

Install Python dependencies:
```bash
uv pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

## Secret Safety (MANDATORY)

- **Never** read, print, or expose `google_token.json` or `google_client_secret.json` to LLM context
- **Never** expose API keys in chat
- Use `--check` to verify credentials without displaying them

## Usage

All commands go through the publish script:

```bash
YTP="uv run python SKILL_DIR/scripts/yt_publish.py"
```

### Upload Video (Automated SEO via Script Markdown)

The recommended workflow is passing the script markdown file with `--md`. The publisher automatically detects the channel, generates mobile-first titles (< 70 chars), builds a 3-tier keyword taxonomy (~450 chars), creates rich 4-part descriptions with chapter timestamps, and selects the appropriate channel token.

**Pre-Flight Quality Gate (MANDATORY INVARIANT):**
All uploads undergo automated pre-flight QA validation before any YouTube API call is made:
1. **Thumbnail Check**: Must exist, <= 2MB, >= 1280x720 (16:9) or 720x1280 (9:16), following channel cover template. Auto-discovered if not passed explicitly (`output/thumb_<stem>.jpg`).
2. **Title Check**: Non-empty, NFC normalized, <= 100 chars (recommended < 70 chars for mobile-first).
3. **Description Check**: Non-empty, must contain timestamps starting at `00:00`.
4. **Tags Check**: 3-tier taxonomy, total chars <= 500.
*If any pre-flight check fails, upload is immediately rejected with a hard stop (exit code 1).*

```bash
# Preview SEO metadata & Pre-Flight QA checklist without uploading (dry-run)
$YTP upload --video /path/to/video.mp4 --md /path/to/script.md --dry-run

# Upload with automated SEO & auto-discovered thumbnail (defaults to public)
$YTP upload --video /path/to/video.mp4 --md /path/to/script.md

# Upload to specific channel or with specific token override
$YTP upload --video /path/to/video.mp4 --md /path/to/script.md --channel TOI_DOC_SACH --privacy public
```

### Manual Upload (Custom Title & Tags)

```bash
# Basic upload
$YTP upload --video /path/to/video.mp4 \
  --title "Vì Sao Ta Cứ Muốn Thắng? - Trang Tử | Tôi Đọc Sách" \
  --description "Mô tả video chi tiết kèm mục lục..." \
  --tags "Tôi Đọc Sách,Trang Tử,Nam Hoa Kinh,Triết Học" \
  --category 27 \
  --privacy public

# With thumbnail
$YTP upload --video /path/to/video.mp4 \
  --title "Video Title" \
  --thumbnail /path/to/thumb.jpg \
  --privacy public

# Scheduled publish
$YTP upload --video /path/to/video.mp4 \
  --title "Scheduled Video" \
  --privacy private \
  --publish-at "2026-08-23T19:00:00+07:00"

# Shorts (appends #Shorts to title)
$YTP upload --video /path/to/shorts_9x16.mp4 \
  --title "Khi AI Làm Hết — Mình Còn Là Ai?" \
  --shorts
```

### Set Thumbnail (for existing video)

```bash
$YTP thumbnail --video-id VIDEO_ID --image /path/to/thumb.jpg
```

### Manage Playlists

```bash
# List playlists
$YTP playlists

# Create playlist
$YTP playlist-create --title "AI Tips" --description "Daily AI tips and tricks"

# Add video to playlist
$YTP playlist-add --playlist-id PL_ID --video-id VIDEO_ID
```

### Check Connectivity

```bash
# Check default channel (ZENPHAM)
$YTP --check

# Check specific channels
$YTP --check --channel PHAMTRAI_DIALY
$YTP --check --channel REALITY_DECODE
# Outputs: {"status": "ok", "channel": "REALITY DECODE", "channel_id": "UCIAospm4AXGBYsJVGTtEB8A"}
```

## Output Format

All commands return JSON to stdout:

```json
{
  "status": "ok",
  "video_id": "dQw4w9WgXcQ",
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "privacy": "private"
}
```

Errors:
```json
{
  "status": "error",
  "error": "Upload failed: quota exceeded",
  "details": "..."
}
```

## Error Handling

- **Token expired**: auto-refreshes. If refresh fails, re-run google-workspace OAuth setup
- **Quota exceeded**: YouTube Data API has daily quota limits (10,000 units/day).
  Upload = 1600 units. Check quota at https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- **Upload failed mid-way**: script uses resumable upload, auto-retries 3 times
- **Missing dependencies**: `uv pip install google-api-python-client google-auth-oauthlib`

## Agent Workflow

1. Verify: `$YTP --check`
2. Prepare: ensure video file + thumbnail + metadata are ready
3. Upload with `--privacy private` first for user review
4. After user approval, update to `public` or set `--publish-at`
5. Report video URL back to user
