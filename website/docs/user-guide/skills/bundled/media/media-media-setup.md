---
title: "Media Setup — Setup YouTube, X, and Facebook publishing platforms"
sidebar_label: "Media Setup"
description: "Setup YouTube, X, and Facebook publishing platforms"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Media Setup

Setup YouTube, X, and Facebook publishing platforms.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/media-setup` |
| Version | `1.0.0` |
| Author | ZENPHAM, Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `media`, `setup`, `youtube`, `facebook`, `twitter`, `x`, `automation` |
| Related skills | [`xurl`](/docs/user-guide/skills/bundled/social-media/social-media-xurl), [`youtube-publisher`](/docs/user-guide/skills/bundled/media/media-youtube-publisher), [`facebook-publisher`](/docs/user-guide/skills/bundled/social-media/social-media-facebook-publisher), [`google-workspace`](/docs/user-guide/skills/bundled/productivity/productivity-google-workspace) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Media Platform Setup

Automated setup for media publishing accounts across YouTube, X (Twitter), and Facebook.
Uses browser automation to register accounts and configure API credentials, pausing only
when human interaction is required (OTP, CAPTCHA, 2FA).


## When to Use

Use this skill when:
- The user asks to setup youtube, x, and facebook publishing platforms.
- Executing automated media setup workflows and tasks.

## Prerequisites

- Hermes browser tool (`agent-browser` or local Chromium)
- Personal info configured in `REPO_ROOT/.conf`
- API credentials will be stored in `~/.hermes/.env`

## Configuration File

The `.conf` file at the repo root contains personal info used during registration:

```ini
FULL_NAME=PHAM VU THANG
NICKNAME=ZENPHAM
PHONE=+84913252992
GMAIL_USER=inteligentsilos@gmail.com
```

Read it with:
```bash
source REPO_ROOT/.conf
echo "$FULL_NAME"
```

## Secret Safety (MANDATORY)

- **Never** read, print, or expose `~/.hermes/.env` contents to LLM context
- **Never** expose OAuth tokens, API keys, or passwords in chat
- After setup, verify credentials via status commands only (e.g., `xurl auth status`)
- Passwords and OTPs provided by the user during setup must NOT be logged or repeated back

## Verify Script

Check status of all platforms:

```bash
python SKILL_DIR/scripts/verify_platforms.py --check-all
```

Output:
```json
{
  "x": {"status": "ok|missing|error", "username": "@zenpham"},
  "youtube": {"status": "ok|missing|error", "channel": "ZENPHAM"},
  "facebook": {"status": "ok|missing|error", "page": "ZENPHAM - AI & Tech"}
}
```

---

## Runbook 1: X (Twitter) Setup

### Step 1: Create X Account (Browser Automation)

1. Navigate to `https://x.com/i/flow/signup`
2. Fill in: Name from `$FULL_NAME`, Email from `$GMAIL_USER`
3. **PAUSE** — Ask user for email verification code or SMS OTP
4. Complete signup, set handle to `$NICKNAME` (lowercase)
5. Set profile photo and bio (AI & Tech content creator)

### Step 2: X Developer Portal

1. Navigate to `https://developer.x.com/en/portal/dashboard`
2. Sign up for Free tier
3. Create App → Get Client ID + Client Secret
4. Save to `~/.hermes/.env`:
   ```
   X_CLIENT_ID=<value>
   X_CLIENT_SECRET=<value>
   ```

### Step 3: Configure xurl CLI

```bash
# Install xurl if missing
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash

# Register app (agent reads credentials from .env, user runs this)
xurl auth apps add zenpham --client-id $X_CLIENT_ID --client-secret $X_CLIENT_SECRET

# OAuth flow (opens browser)
xurl auth oauth2 --app zenpham $X_USERNAME_PERSONAL

# Set default
xurl auth default zenpham

# Verify
xurl auth status
xurl whoami
```

### Step 4: Update .conf

Set `X_USERNAME_PERSONAL=<handle>` in `.conf`.

---

## Runbook 2: YouTube Setup

### Step 1: Create YouTube Channel

1. Navigate to `https://youtube.com` → Sign in with `$GMAIL_USER`
2. **PAUSE** — Ask user for password or 2FA code if needed
3. Create channel with name `$BRAND_PERSONAL_NAME` (ZENPHAM)
4. Set channel description, avatar

### Step 2: Google Cloud API Setup

Uses the existing Google Workspace skill's OAuth infrastructure:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"

# Check if already authenticated
$GSETUP --check

# If not, set up with YouTube scope
$GSETUP --client-secret /path/to/client_secret.json
$GSETUP --auth-url --services youtube --format json
# PAUSE — Send auth URL to user, wait for redirect URL
$GSETUP --auth-code "REDIRECT_URL_FROM_USER" --format json
$GSETUP --check
```

If Google Workspace is already set up, just ensure the YouTube Data API v3 is
enabled in the GCP project (`$GCP_PROJECT_ID` from `~/.hermes/.env`).

### Step 3: Update .conf

Set `YT_CHANNEL_PERSONAL=<channel_id>` in `.conf`.

---

## Runbook 3: Facebook Setup

### Step 1: Create Facebook Account

1. Navigate to `https://facebook.com/r.php`
2. Fill in: First/Last name, Email, Password, Birthday
3. **PAUSE** — Ask user for SMS OTP or email verification
4. Complete registration

### Step 2: Create Facebook Page

1. Navigate to `https://facebook.com/pages/creation`
2. Create Page: Name = `$BRAND_PERSONAL_NAME - AI & Tech`
3. Set category: "Science, Technology & Engineering"
4. Add profile photo, cover photo

### Step 3: Meta Developer App

1. Navigate to `https://developers.facebook.com/apps/creation/`
2. Create App → Type: Business
3. Add Product: Facebook Login for Business
4. Configure permissions: `pages_manage_posts`, `pages_read_engagement`, `publish_video`
5. Generate Page Access Token (long-lived)
6. Save to `~/.hermes/.env`:
   ```
   META_APP_ID=<value>
   META_APP_SECRET=<value>
   FB_PAGE_ACCESS_TOKEN_PERSONAL=<token>
   FB_PAGE_ID_PERSONAL=<page_id>
   ```

### Step 4: Update .conf

Set `FB_PAGE_PERSONAL=<page_name>` in `.conf`.

---

## Agent Workflow

1. Source `.conf` for personal info
2. Check `verify_platforms.py --check-all` for current status
3. Run the appropriate runbook for any platform showing `missing`
4. After each runbook, verify again
5. Report final status to user via Telegram
