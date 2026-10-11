---
title: "Youtube Publisher — Upload videos and manage playlists via YouTube Data API"
sidebar_label: "Youtube Publisher"
description: "Upload videos and manage playlists via YouTube Data API"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Youtube Publisher

Upload videos and manage playlists via YouTube Data API.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/youtube-publisher` |
| Version | `1.0.0` |
| Author | ZENPHAM, Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `YouTube`, `Video`, `Upload`, `Publishing`, `Media` |
| Related skills | [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content), [`google-workspace`](/docs/user-guide/skills/bundled/productivity/productivity-google-workspace), [`media-studio`](/docs/user-guide/skills/bundled/media/media-media-studio) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

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

### Upload Video

```bash
# Basic upload (defaults to private)
$YTP upload --video /path/to/shorts.mp4 \
  --title "Vibe Coding là gì? #shorts" \
  --description "Tìm hiểu Vibe Coding trong 60 giây..." \
  --tags "AI,vibecoding,shorts,tech" \
  --category 28

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

# Shorts (auto-detected by aspect ratio, but explicit tag helps)
$YTP upload --video /path/to/shorts_9x16.mp4 \
  --title "Quick AI Tip #shorts" \
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
$YTP --check
# Outputs: {"status": "ok", "channel": "ZENPHAM", "channel_id": "UC..."}
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
