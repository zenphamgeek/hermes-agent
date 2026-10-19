---
name: account-vault
description: Secure multi-account credential vault manager.
version: 2.0.0
author: Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Credentials
    - Vault
    - Encryption
    - Auth
    - 2FA
    - TOTP
    - Sessions
    - Automation
    related_skills:
    - google-workspace
    - himalaya
    - browser-use
    - github
---

# Account Vault (Autonomous Secrets & Identity Engine)

Autonomous encrypted credential and identity manager for services the user owns. Stores credentials, 2FA/TOTP secrets, extra metadata, and browser sessions in an AES-256-GCM encrypted store.

Provides zero-touch execution:
- **RFC-6238 TOTP Engine**: Generates real-time 6-digit 2FA codes directly for login automation.
- **Zero-Leak Process Injection (`exec`)**: Spawns sub-commands with injected environment variables without writing secrets to disk or shell history.
- **Session & Cookie Stash**: Caches encrypted browser cookies to bypass login screens and CAPTCHAs.
- **Autonomous Password Rotation (`rotate`, `generate`)**: Generates high-entropy passwords and tracks history.
- **Auto-Snapshots & Point-In-Time Rollback (`snapshots`, `restore`)**: Creates automatic encrypted backups before any mutation.
- **Security Audit & k-Anonymity Breach Check (`audit`)**: Scans for weak, reused, stale, or breached passwords.
- **Universal Migration (`import`, `export`)**: Seamlessly imports/exports Bitwarden, 1Password, KeePass, and `.env` files.
- **In-Memory Python SDK (`AccountVault`)**: Programmatic zero-overhead access for Hermes skills.

---

## Prerequisites

- Python 3.10+ with `cryptography` package.
- Master passphrase resolved from `ACCOUNT_VAULT_PASS` env, `~/.hermes/.account_vault_pass`, or interactive prompt.

---

## Quick Reference

```bash
VAULT="python ${HERMES_HOME:-$HOME/.hermes}/skills/account-vault/scripts/vault.py"

# 1. Setup & Passphrase
$VAULT init --passphrase "master-secret"

# 2. Add / Store Credential with 2FA TOTP secret
$VAULT add github -u "octocat" -p "token-or-pass" --totp-secret "JBSWY3DPEHPK3PXP" --field email=octo@github.com

# 3. Read Credentials & Active 2FA TOTP Code
$VAULT get github --json
$VAULT get github --with-totp --json
$VAULT totp github                    # outputs current 6-digit code + TTL

# 4. Zero-Leak Subprocess Execution
$VAULT exec aws-prod -- aws s3 sync ./build s3://my-prod-bucket/
$VAULT exec github -- gh repo list

# 5. Session & Cookie Caching (for Browser Automation)
$VAULT session-save google --cookies-json '[{"name": "SID", "value": "xyz"}]'
$VAULT session-get google --json

# 6. Autonomous Password Generation & Rotation
$VAULT generate --length 32 --json
$VAULT rotate github --length 28      # updates vault & records history

# 7. Snapshots & Disaster Recovery
$VAULT snapshots
$VAULT restore 0                      # rollback to latest snapshot

# 8. Security Health Audit & Breach Scanner
$VAULT audit --check-pwned

# 9. Multi-Format Import & Export
$VAULT import bitwarden ~/bw_export.json
$VAULT import 1password-csv ~/1p_export.csv
$VAULT import dotenv .env.production
$VAULT export json --output ~/vault_export.json

# 10. Ecosystem Consolidation & Sustainable Playwright Cloud/OAuth Provisioner (v3.0)
$VAULT sync-ecosystem --json
$VAULT oauth-refresh --dry-run
$VAULT oauth-refresh youtube_channel_reality_decode
$VAULT providers
$VAULT provision google-api-key --account google_insilos --project-id project-3e385278-cd08-450e-ba0
$VAULT provision google-oauth-client --account google_insilos --project-id project-3e385278-cd08-450e-ba0
$VAULT provision youtube-oauth --account google_insilos --channel reality_decode --headed
$VAULT provision google-security --account google_zenhunter --headed
$VAULT provision mcp-cloud-key --account google_zenhunter --provider openrouter
```

---

## Agent Usage & Integration Procedures

### 1. Zero-Friction 2FA Login
When logging into a service requiring 2FA:
1. Fetch credentials with TOTP in one call:
   ```bash
   VAULT_JSON=$(python $VAULT_PATH get <service> --with-totp --json)
   ```
2. Extract `username`, `password`, and `totp.code`.
3. Submit the credentials to the browser or CLI tool.

### 2. Zero-Leak Command Execution
When running CLI tools or scripts that need API keys or passwords:
```bash
python $VAULT_PATH exec <service> -- <command-to-run>
```
The child process will automatically receive:
- `VAULT_USERNAME`, `VAULT_PASSWORD`, `VAULT_TOTP_CODE`
- `<SERVICE>_USER`, `<SERVICE>_PASSWORD`, `<SERVICE>_TOTP_CODE`
- `VAULT_<FIELD_NAME>` for each custom field.

### 3. Programmatic Python SDK in Skills
```python
from skills.account_vault.scripts.vault import AccountVault

vault = AccountVault()
cred = vault.get("github")
otp_code = vault.get_totp("github")
cookies = vault.get_session("google")
```

---

## Security Model

- **Encryption**: AES-256-GCM authenticated encryption.
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 200,000 iterations and unique 16-byte cryptographically secure salt.
- **Passphrase Storage**: Never stored inside the vault file; only derived at runtime.
- **Snapshots**: Point-in-time encrypted snapshots created before every mutating action (`add`, `rm`, `rotate`, `import`, `set-passphrase`).
- **k-Anonymity Breach Check**: Only sends the first 5 characters of SHA-1 hash to HaveIBeenPwned API; full password is never exposed to network.
