---
name: x-publisher
description: Publish X and Twitter threads and posts via xurl CLI.
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
prerequisites:
  commands:
  - xurl
metadata:
  hermes:
    tags:
    - media
    - social-media
    - x
    - twitter
    - publishing
    related_skills:
    - xurl
    - media-studio
    - media-setup
---
# X Publisher — Twitter/X Thread & Post Publishing

Wrapper skill that uses the `xurl` CLI to publish content to X/Twitter.
Uses the existing `xurl` skill for authentication and API access.


## When to Use

Use this skill when:
- The user asks to publish x and twitter threads and posts via xurl cli.
- Executing automated x publisher workflows and tasks.

## Prerequisites

- `xurl` installed (`~/.local/bin/xurl`)
- OAuth configured: `xurl auth status` shows authenticated
- See `media-setup` skill for setup instructions

## Capabilities

### Post a Single Tweet

```bash
# Text only
xurl post "Your tweet text here"

# With image
xurl post "Tweet with image" --media /path/to/image.jpg

# With video
xurl post "Tweet with video" --media /path/to/video.mp4
```

### Post a Thread

```bash
# Thread from a file (one tweet per paragraph, separated by blank lines)
xurl thread --file /path/to/thread.txt

# Thread from command line
xurl thread \
  "Tweet 1: The hook" \
  "Tweet 2: The content" \
  "Tweet 3: More content" \
  "Tweet 4: The CTA"
```

### Post Thread with Media on First Tweet

```bash
xurl thread \
  --media /path/to/thumbnail.jpg \
  "🧵 Hook tweet with image" \
  "Tweet 2 content" \
  "Final tweet with CTA"
```

## Media Pipeline Integration

When called from `media-studio`, use the following pattern:

```bash
# 1. Read the X thread script
SCRIPT="/tmp/media-studio/YYYY-MM-DD/script_x.md"

# 2. Parse tweets (each [TWEET N] block = one tweet)
# The agent should parse the script and extract individual tweets

# 3. Post as thread with thumbnail on first tweet
xurl thread \
  --media /tmp/media-studio/YYYY-MM-DD/thumb_x.jpg \
  "Tweet 1 text" \
  "Tweet 2 text" \
  "Tweet 3 text" \
  "Tweet 4 text" \
  "Tweet 5 text" \
  "Final CTA tweet"
```

## Rate Limits (Free Tier)

- **1,500 tweets/month** (includes replies and threads)
- **50 requests/15 min** for posting
- Best practice: Post max 1 thread/day = ~6 tweets × 30 days = 180 tweets/month

## Verification

```bash
# Check auth status
xurl auth status

# Check identity
xurl whoami

# Test post (use --dry-run if available)
xurl post "Test post from Hermes" --dry-run 2>/dev/null || echo "No dry-run support"
```
