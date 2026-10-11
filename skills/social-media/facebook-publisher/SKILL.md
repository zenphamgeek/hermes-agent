---
name: facebook-publisher
description: Post text, photos, and videos via Meta Graph API.
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Facebook
    - Meta
    - Social Media
    - Publishing
    - Fanpage
    related_skills:
    - xurl
    - media-studio
---
# Facebook Publisher

Post text, photos, videos, and Reels to Facebook Pages via Meta Graph API v21.0.


## When to Use

Use this skill when:
- The user asks to post text, photos, and videos via meta graph api.
- Executing automated facebook publisher workflows and tasks.

## Prerequisites

- Facebook Page created
- Meta Developer App with permissions: `pages_manage_posts`, `pages_read_engagement`, `publish_video`
- Page Access Token (long-lived) stored in `~/.hermes/.env` as `FB_PAGE_ACCESS_TOKEN_PERSONAL`
- Page ID stored in `~/.hermes/.env` as `FB_PAGE_ID_PERSONAL`

## Secret Safety (MANDATORY)

- **Never** read, print, or expose Page Access Tokens to LLM context
- **Never** expose `META_APP_SECRET` in chat
- Use `--check` to verify credentials without displaying tokens
- The script reads tokens from `~/.hermes/.env` directly — never pass them as CLI arguments

## Usage

All commands go through the publish script:

```bash
FBP="uv run python SKILL_DIR/scripts/fb_publish.py"
```

### Text Post

```bash
# Simple text post
$FBP post --message "Hello from Hermes! 🤖"

# With link (note: FB may reduce reach for posts with external links)
$FBP post --message "Check out this article" --link "https://example.com"

# Scheduled post (minimum 10 minutes in the future, max 75 days)
$FBP post --message "Scheduled content" --schedule "2026-08-23T11:45:00+07:00"
```

### Photo Post

```bash
# Single photo
$FBP photo --image /path/to/image.jpg --caption "Infographic: AI Trends 2026"

# Multiple photos (album/carousel)
$FBP photo --image /path/to/img1.jpg --image /path/to/img2.jpg --image /path/to/img3.jpg \
  --caption "Carousel: 5 Steps to Vibe Coding"
```

### Video Post

```bash
# Standard video
$FBP video --video /path/to/video.mp4 \
  --title "Vibe Coding Tutorial" \
  --description "Learn Vibe Coding in 5 minutes"

# Reel (vertical video, 9:16 aspect ratio)
$FBP reel --video /path/to/shorts.mp4 \
  --description "Quick AI tip #shorts"
```

### Auto-Comment (avoid link suppression)

```bash
# Post text first, then add comment with link
$FBP post --message "Great article about AI Agents!" \
  --first-comment "Source: https://example.com/article"
```

### Check Connectivity

```bash
$FBP --check
# Output: {"status": "ok", "page": "ZENPHAM - AI & Tech", "page_id": "123456"}
```

### Read Insights

```bash
$FBP insights --metric post_impressions,post_engaged_users --period day
```

## Output Format

All commands return JSON:

```json
{
  "status": "ok",
  "post_id": "PAGE_ID_POST_ID",
  "url": "https://facebook.com/PAGE_ID/posts/POST_ID"
}
```

Errors:
```json
{
  "status": "error",
  "error": "OAuthException: (#200) Insufficient permissions",
  "code": 200
}
```

## Error Handling

- **Token expired**: Long-lived Page tokens last ~60 days. Regenerate via Meta Developer Console
- **Permission denied**: Check app permissions in Meta Developer Console
- **Rate limiting**: Graph API has complex rate limits. Script auto-waits on 429
- **Video processing**: Large videos use resumable upload. Script polls until processing completes

## Agent Workflow

1. Verify: `$FBP --check`
2. Before posting, always confirm content with user (draft → approve → publish)
3. For posts with links: use `--first-comment` to avoid reach suppression
4. After posting, report the post URL back to user
5. Never post without explicit user approval
