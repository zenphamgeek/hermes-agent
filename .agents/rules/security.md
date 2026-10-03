# Security & Access Control Rules

## Secrets Management

- **`.env` is for secrets ONLY**: API keys, tokens, passwords, bot tokens
- **`config.yaml` is for behavioral settings**: timeouts, thresholds, feature flags
- **NEVER** expose secrets in:
  - Git commits or diffs
  - Log files or terminal output
  - Telegram messages or screenshots
  - Skill files or AGENTS.md
  - Agent responses to users

## Telegram Security

- **User whitelist**: Only execute commands from users in `TELEGRAM_ALLOWED_USERS`
- **Admin commands**: `/stop`, `/pause`, `/yolo`, `/restart` require admin-level users
- **Coding commands**: `agy:`, `trae:` patterns require authenticated users
- **Never run shell commands** from unverified Telegram users
- **File paths in screenshots**: Crop or redact paths containing credentials

## Credential Handling Protocol

When needing to update API keys:
1. Navigate browser to provider's API key page
2. User authenticates (only manual step)
3. Agent extracts key via DOM/API
4. Write to `~/.hermes/.env` via `PUT /api/env` with session token
5. Verify connection works
6. Never store keys in config.yaml, skills, or rules files

## Infrastructure Credentials

- **PostgreSQL**: Per-database users (see infrastructure.md)
- **Redis**: Password `redis_p15_2026` — for internal use only
- **MinIO S3**: `minioadmin / minio_p15_2026` — admin access
- **Hermes Dashboard**: Session token via `X-Hermes-Session-Token` header
- **Telegram Bot**: `TELEGRAM_BOT_TOKEN` in `.env`

## Code Security

- **Dangerous command approvals**: Gateway uses `/approve` and `/deny` for risky commands
- **YOLO mode** (`/yolo`): Skips all dangerous command approvals — use with caution
- **Autopilot state**: Persisted in `~/.hermes/autopilot.json`, not in `.env`
- **Plugin isolation**: Plugins in `~/.hermes/plugins/` work within ABCs/hooks, never touch core files
