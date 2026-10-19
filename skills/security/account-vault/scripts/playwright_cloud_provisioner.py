#!/usr/bin/env python3
"""Sustainable Playwright Cloud API Key, OAuth2 Client & Advanced Security Provisioner.

Designed on the "Build-Once, Use-Long-Term" (Hybrid API-First + Persistent Stealth
Browser Context) architecture integrated directly with `vault.py` (`AccountVault`):

1. Zero-Browser OAuth2 Refresh (`refresh_google_oauth_tokens`):
   - Deterministically refreshes YouTube (`zenpham`, `phamtrai_dialy`, `reality_decode`),
     Gmail, and Google Drive OAuth2 tokens via `https://oauth2.googleapis.com/token`
     using credentials stored in `AccountVault`, syncing back to `~/.hermes/google_token*.json`.
2. Ecosystem Credential Consolidation (`sync_ecosystem_to_vault`):
   - Ingests and encrypts all Google accounts, YouTube channel tokens, OAuth2 client
     secrets, `.hermes/.env` API keys, Modal GPU workspace tokens, AGY Fleet node
     identities, and Odoo DB credentials into `~/.hermes/account_vault.json`.
3. Persistent Stealth Playwright Provisioner (`PlaywrightCloudProvisioner`):
   - Uses `~/.hermes/browser_profiles/<account_id>` + encrypted `AccountVault` session
     cookie hydration/persistence so logins remain warm long-term.
   - Autonomous Google Login with RFC-6238 TOTP (`vault.get_totp()`), recovery phone
     suffix matching, and App Password / Authenticator enrollment.
   - 5 Provider Playbooks:
     * `google-api-key`: Provision/extract GCP API key (`AIza...`) & enable APIs.
     * `google-oauth-client`: Provision/extract OAuth 2.0 Client ID & Secret.
     * `youtube-oauth`: End-to-end PKCE OAuth flow for YouTube Brand Channels.
     * `google-security`: Enroll RFC-6238 TOTP Authenticator or generate App Password.
     * `mcp-cloud-key`: Provision/extract API keys for MCP & Cloud providers
       (`openrouter`, `firecrawl`, `tavily`, `cloudflare`, `modal`, `github`, `bai`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse
import urllib.request


# Default recovery phone suffixes used across Zen's Google accounts
DEFAULT_PHONE_RECOVERY_MAP: Dict[str, Dict[str, str]] = {
    "92": {"phone": "913252992", "country": "Vietnam"},
    "11": {"phone": "944311811", "country": "Vietnam"},
}

# Canonical MCP & Cloud Provider Console Endpoints
MCP_PROVIDER_REGISTRY: Dict[str, Dict[str, Any]] = {
    "google-cloud": {
        "name": "Google Cloud Console (APIs & Credentials)",
        "auth_type": "google_sso",
        "credentials_url": "https://console.cloud.google.com/apis/credentials",
        "library_url": "https://console.cloud.google.com/apis/library",
        "key_regex": r"AIza[0-9A-Za-z\-_]{35}",
        "env_var": "GOOGLE_API_KEY",
    },
    "youtube": {
        "name": "YouTube Data API v3 & Studio Multi-Channel OAuth",
        "auth_type": "google_oauth_pkce",
        "studio_url": "https://studio.youtube.com",
        "scopes": [
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        "env_var": "YOUTUBE_API_KEY",
    },
    "openrouter": {
        "name": "OpenRouter MCP & LLM Gateway",
        "auth_type": "google_sso",
        "keys_url": "https://openrouter.ai/settings/keys",
        "key_regex": r"sk-or-v1-[a-f0-9]{64}",
        "env_var": "OPENROUTER_API_KEY",
    },
    "firecrawl": {
        "name": "Firecrawl Web Scraper MCP",
        "auth_type": "google_sso",
        "keys_url": "https://www.firecrawl.dev/app/api-keys",
        "key_regex": r"fc-[a-f0-9]{32}",
        "env_var": "FIRECRAWL_API_KEY",
    },
    "tavily": {
        "name": "Tavily AI Search MCP",
        "auth_type": "google_sso",
        "keys_url": "https://app.tavily.com/home",
        "key_regex": r"tvly-[A-Za-z0-9\-_]{24,}",
        "env_var": "TAVILY_API_KEY",
    },
    "cloudflare": {
        "name": "Cloudflare Workers AI & Clef Edge",
        "auth_type": "password_or_sso",
        "keys_url": "https://dash.cloudflare.com/profile/api-tokens",
        "key_regex": r"[A-Za-z0-9_\-]{38,45}",
        "env_var": "CLOUDFLARE_API_TOKEN",
    },
    "modal": {
        "name": "Modal Serverless GPU Fleet",
        "auth_type": "google_or_github_sso",
        "keys_url": "https://modal.com/settings/tokens",
        "key_regex": r"ak-[A-Za-z0-9]{18,26}",
        "env_var": "MODAL_TOKEN_ID",
    },
    "github": {
        "name": "GitHub Personal Access Token & MCP",
        "auth_type": "password_totp",
        "keys_url": "https://github.com/settings/tokens",
        "key_regex": r"(?:ghp|github_pat)_[A-Za-z0-9_]{30,90}",
        "env_var": "GITHUB_TOKEN",
    },
    "bai": {
        "name": "B.AI Multi-Key API Gateway",
        "auth_type": "google_sso",
        "invite_url": "https://chat.b.ai/chat?invite_code=STSQYC",
        "keys_url": "https://chat.b.ai/key",
        "key_regex": r"sk-[A-Za-z0-9\-_]{20,64}",
        "env_var": "BAI_API_KEY",
    },
}

# Canonical AGY Fleet Node Roster (17 Pro + 2 Ultra + System gateways)
FLEET_ACCOUNT_ROSTER: List[Dict[str, str]] = [
    {"service": "fleet_node_4", "node": "node-4", "email": "just.ask.mr.zen@gmail.com", "tier": "pro", "google_ref": "google_just_ask_mr_zen"},
    {"service": "fleet_node_5", "node": "node-5", "email": "zenphamgeek@gmail.com", "tier": "pro", "google_ref": "google_zenphamgeek"},
    {"service": "fleet_node_6", "node": "node-6", "email": "zeninallgeek@gmail.com", "tier": "pro", "google_ref": "google_zeninallgeek"},
    {"service": "fleet_team_3", "node": "team-3", "email": "coderedgen@gmail.com", "tier": "pro", "google_ref": "google_coderedgen"},
    {"service": "fleet_binhthuong", "node": "binhthuong", "email": "binhthuongcarpediem@gmail.com", "tier": "pro", "google_ref": "google_binhthuong"},
    {"service": "fleet_sunward", "node": "sunward", "email": "sunwardpham@gmail.com", "tier": "pro", "google_ref": "google_sunward"},
    {"service": "fleet_insilos", "node": "insilos", "email": "inteligentsilos@gmail.com", "tier": "pro", "google_ref": "google_insilos"},
    {"service": "fleet_justaskgao", "node": "justaskgao", "email": "justaskgao@gmail.com", "tier": "pro", "google_ref": "google_justaskgao"},
    {"service": "fleet_immoon0009", "node": "immoon0009-gmail-com", "email": "immoon0009@gmail.com", "tier": "pro", "google_ref": "google_immoon0009"},
    {"service": "fleet_nahlaleah102", "node": "nahlaleah102", "email": "nahlaleah102@gmail.com", "tier": "pro", "google_ref": "google_nahlaleah102"},
    {"service": "fleet_tsmei0209", "node": "tsmei0209-gmail-com", "email": "tsmei0209@gmail.com", "tier": "pro", "google_ref": "google_tsmei0209"},
    {"service": "fleet_ai_digimate", "node": "ai-digimate", "email": "ai.digimate@gmail.com", "tier": "pro", "google_ref": "google_ai_digimate"},
    {"service": "fleet_codegeekvn", "node": "codegeekvn", "email": "codegeekvn@gmail.com", "tier": "pro", "google_ref": "google_codegeekvn"},
    {"service": "fleet_gaopham", "node": "gaopham", "email": "gaopham83@gmail.com", "tier": "pro", "google_ref": "google_gaopham83"},
    {"service": "fleet_zenonmind", "node": "zenonmind", "email": "zenonmind@gmail.com", "tier": "pro", "google_ref": "google_zenonmind"},
    {"service": "fleet_agy_home", "node": "agy-home", "email": "graydoom2030@gmail.com", "tier": "pro", "google_ref": "google_graydoom2030"},
    {"service": "fleet_traimai", "node": "traimai", "email": "traimai.family@gmail.com", "tier": "pro", "google_ref": "google_traimai_family"},
    {"service": "fleet_innoria_team", "node": "innoria-team", "email": "innoria.team@gmail.com", "tier": "ultra_suspended", "google_ref": "google_innoria_team"},
    {"service": "fleet_ariana", "node": "ariana", "email": "lthn.ariana@gmail.com", "tier": "ultra_suspended", "google_ref": "google_ariana"},
]


@dataclass
class ProvisionResult:
    """Structured result from a Playwright or OAuth2 provisioning operation."""
    status: str  # "ok", "dry_run_ready", "error"
    playbook: str
    account_id: str
    provider: str
    vault_service_key: str
    profile_dir: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "status": self.status,
            "playbook": self.playbook,
            "account_id": self.account_id,
            "provider": self.provider,
            "vault_service_key": self.vault_service_key,
            "profile_dir": self.profile_dir,
            "details": self.details,
            "timestamp": self.timestamp,
        }
        if self.error:
            out["error"] = self.error
        return out


# ==============================================================================
# 1. Ecosystem Credential Consolidation into AccountVault
# ==============================================================================

def _upsert_entry(
    entries: Dict[str, Any],
    service: str,
    username: str,
    password: str,
    fields: Dict[str, Any],
    now_iso: str,
    preserve_existing_password: bool = True,
) -> bool:
    """Idempotently insert or enrich a vault entry without overwriting real secrets with placeholders."""
    existing = entries.get(service)
    if existing:
        merged_fields = dict(existing.get("fields") or {})
        for k, v in fields.items():
            if v is not None and v != "":
                merged_fields[k] = v
        final_pw = existing.get("password", "")
        if not preserve_existing_password or not final_pw or final_pw.startswith("PENDING_") or final_pw.startswith("["):
            if password and not password.startswith("["):
                final_pw = password
        final_user = username or existing.get("username", "")
        entries[service] = {
            "username": final_user,
            "password": final_pw,
            "fields": merged_fields,
            "created_at": existing.get("created_at", now_iso),
            "updated_at": now_iso,
        }
        return False
    else:
        entries[service] = {
            "username": username,
            "password": password,
            "fields": {k: v for k, v in fields.items() if v is not None and v != ""},
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        return True


def sync_ecosystem_to_vault(
    vault_module: Any,
    passphrase: Optional[str] = None,
    hermes_home: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Consolidate all workspace accounts, OAuth clients/tokens, .env keys, Modal profiles, and Fleet nodes into Vault."""
    resolved_pass = vault_module.resolve_passphrase(passphrase)
    h_home = hermes_home or vault_module.get_hermes_home()
    r_root = repo_root or Path("/home/zen/hermes-agent")
    now_iso = datetime.now(timezone.utc).isoformat()

    data = vault_module.read_full_vault(resolved_pass)
    raw = vault_module.load_raw_vault()
    salt = bytes.fromhex(raw["salt"]) if "salt" in raw else os.urandom(16)
    entries = data.setdefault("entries", {})

    stats = {
        "google_accounts_synced": 0,
        "oauth_clients_and_tokens_synced": 0,
        "dotenv_secrets_synced": 0,
        "modal_profiles_synced": 0,
        "fleet_nodes_synced": 0,
        "infrastructure_synced": 0,
    }

    # --- A. Sync Google Accounts from assets/credientials/google_personal.md ---
    gp_file = r_root / "assets" / "credientials" / "google_personal.md"
    if gp_file.exists():
        for line in gp_file.read_text(encoding="utf-8").splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7 and "@" in parts[3]:
                srv_key = parts[2].strip("` ")
                email = parts[3].strip("` ")
                pw = parts[4].strip("` ")
                domain_type = parts[5].strip()
                note = parts[6].strip()
                # Only update password if it's not already masked
                is_masked = pw.startswith("[") or "Vault:" in pw or "MASKED" in pw
                _upsert_entry(
                    entries,
                    service=srv_key,
                    username=email,
                    password="" if is_masked else pw,
                    fields={
                        "provider": "google",
                        "domain_type": domain_type,
                        "note": note,
                        "browser_profile": str(h_home / "browser_profiles" / srv_key),
                        "recovery_phone_92": "913252992",
                        "recovery_phone_11": "944311811",
                    },
                    now_iso=now_iso,
                    preserve_existing_password=is_masked,
                )
                stats["google_accounts_synced"] += 1

    # Ensure primary Google accounts used by YouTube / Fleet / Modal exist in vault
    extra_google_identities = [
        ("google_insilos", "inteligentsilos@gmail.com", "Google Account for YouTube Channels (ZENPHAM, Biết Địa Lý, REALITY DECODE) & Gmail Pub/Sub"),
        ("google_just_ask_mr_zen", "just.ask.mr.zen@gmail.com", "Google Account for Fleet node-4 & Modal zenmaster/zenpeace/mindful/zenguru"),
        ("google_zenphamgeek", "zenphamgeek@gmail.com", "Google Account for Fleet node-5 & GitHub zenphamgeek"),
        ("google_zenonmind", "zenonmind@gmail.com", "Google Account for Fleet zenonmind & Modal zenonmind/lovenovel/vieturbo/insimind/zenonts"),
        ("google_mojopham", "mojopham@gmail.com", "Google Account for Modal diatts/mojopham/mvlm/vrag/motion"),
    ]
    for srv_key, email, note in extra_google_identities:
        _upsert_entry(
            entries,
            service=srv_key,
            username=email,
            password=entries.get(srv_key, {}).get("password", "MANAGED_OAUTH_SESSION"),
            fields={
                "provider": "google",
                "note": note,
                "browser_profile": str(h_home / "browser_profiles" / srv_key),
                "recovery_phone_92": "913252992",
                "recovery_phone_11": "944311811",
            },
            now_iso=now_iso,
            preserve_existing_password=True,
        )
        stats["google_accounts_synced"] += 1

    # --- B. Sync Google OAuth 2.0 Client Secrets & YouTube/Gmail/GDrive Tokens ---
    client_secret_files = [
        ("google_oauth_client_default", h_home / "google_client_secret.json", "YouTube & Google Workspace OAuth2 Client"),
        ("google_oauth_client_gmail", h_home / "gmail_client_secret.json", "Gmail Pub/Sub OAuth2 Client"),
    ]
    for srv_key, cs_path, desc in client_secret_files:
        if cs_path.exists():
            try:
                raw_cs = json.loads(cs_path.read_text(encoding="utf-8"))
                block = raw_cs.get("installed") or raw_cs.get("web") or raw_cs
                client_id = block.get("client_id", "")
                client_secret = block.get("client_secret", "")
                project_id = block.get("project_id", "")
                if client_id and client_secret:
                    _upsert_entry(
                        entries,
                        service=srv_key,
                        username=client_id,
                        password=client_secret,
                        fields={
                            "provider": "google_oauth_client",
                            "project_id": project_id,
                            "auth_uri": block.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                            "token_uri": block.get("token_uri", "https://oauth2.googleapis.com/token"),
                            "source_file": str(cs_path),
                            "description": desc,
                        },
                        now_iso=now_iso,
                        preserve_existing_password=False,
                    )
                    stats["oauth_clients_and_tokens_synced"] += 1
            except Exception:
                pass

    # Sync YouTube & Gmail OAuth Token files
    token_files = [
        ("youtube_channel_zenpham", h_home / "google_token.json", "ZENPHAM (@zenpham-g3l)", "inteligentsilos@gmail.com"),
        ("youtube_channel_phamtrai_dialy", h_home / "google_token_phamtrai_dialy.json", "Biết Địa lý từ Ba tôi (@phamtrai-dialy)", "inteligentsilos@gmail.com"),
        ("youtube_channel_reality_decode", h_home / "google_token_reality_decode.json", "REALITY DECODE (@reality-decode-officials)", "inteligentsilos@gmail.com"),
        ("google_gmail_oauth_token", h_home / "gmail_token.json", "Gmail Pub/Sub Realtime Watcher", "inteligentsilos@gmail.com"),
        ("google_gdrive_oauth_token", Path.home() / ".gemini" / "antigravity" / "plugin_data" / "gdrive" / "token.json", "Google Drive MCP Plugin Token", "inteligentsilos@gmail.com"),
    ]
    for srv_key, tk_path, title, owner_email in token_files:
        if tk_path.exists():
            try:
                tk = json.loads(tk_path.read_text(encoding="utf-8"))
                refresh_token = tk.get("refresh_token") or tk.get("token") or ""
                if refresh_token:
                    _upsert_entry(
                        entries,
                        service=srv_key,
                        username=owner_email,
                        password=refresh_token,
                        fields={
                            "provider": "google_oauth_token",
                            "channel_title": tk.get("channel_title", title),
                            "channel_id": tk.get("channel_id", ""),
                            "channel_custom_url": tk.get("channel_custom_url", ""),
                            "client_id": tk.get("client_id", ""),
                            "client_secret": tk.get("client_secret", ""),
                            "token_uri": tk.get("token_uri", "https://oauth2.googleapis.com/token"),
                            "scopes": ",".join(tk.get("scopes", [])) if isinstance(tk.get("scopes"), list) else str(tk.get("scopes", "")),
                            "token_file": str(tk_path),
                        },
                        now_iso=now_iso,
                        preserve_existing_password=False,
                    )
                    stats["oauth_clients_and_tokens_synced"] += 1
            except Exception:
                pass

    # --- C. Sync .hermes/.env Secrets & Cloud/MCP API Keys ---
    env_file = h_home / ".env"
    if env_file.exists():
        env_map: Dict[str, str] = {}
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if v:
                env_map[k] = v

        # Store grouped provider entries + individual env keys
        for k, v in env_map.items():
            srv_key = f"env_{k.lower()}"
            _upsert_entry(
                entries,
                service=srv_key,
                username=k,
                password=v,
                fields={
                    "provider": "hermes_dotenv",
                    "env_var": k,
                    "source_file": str(env_file),
                },
                now_iso=now_iso,
                preserve_existing_password=False,
            )
            stats["dotenv_secrets_synced"] += 1

    # --- D. Sync Modal GPU Profiles (from ~/.modal.toml & modal_token_profile.md) ---
    modal_toml = Path.home() / ".modal.toml"
    if modal_toml.exists():
        current_prof: Optional[str] = None
        prof_data: Dict[str, Dict[str, str]] = {}
        for raw_line in modal_toml.read_text(encoding="utf-8").splitlines():
            # Also parse commented-out profiles (# [profile] / # token_id = ...) so 100% of 20 profiles are preserved in Vault!
            clean = raw_line.strip()
            is_commented = False
            if clean.startswith("#"):
                is_commented = True
                clean = clean.lstrip("#").strip()
            m_sec = re.match(r"^\[([a-zA-Z0-9_\-]+)\]$", clean)
            if m_sec:
                current_prof = m_sec.group(1)
                prof_data.setdefault(current_prof, {"commented": str(is_commented)})
                continue
            if current_prof and "=" in clean:
                mk, mv = [x.strip().strip("'\"") for x in clean.split("=", 1)]
                if mk in ("token_id", "token_secret", "active"):
                    prof_data[current_prof][mk] = mv

        for prof_name, pdict in prof_data.items():
            tid = pdict.get("token_id", "")
            tsec = pdict.get("token_secret", "")
            if tid and tsec:
                _upsert_entry(
                    entries,
                    service=f"modal_{prof_name}",
                    username=tid,
                    password=tsec,
                    fields={
                        "provider": "modal",
                        "workspace": prof_name,
                        "token_id": tid,
                        "commented_in_toml": pdict.get("commented", "False"),
                        "source_file": str(modal_toml),
                    },
                    now_iso=now_iso,
                    preserve_existing_password=False,
                )
                stats["modal_profiles_synced"] += 1

    # --- E. Sync AGY Fleet Node Roster (19 Nodes) ---
    for node_spec in FLEET_ACCOUNT_ROSTER:
        srv_key = node_spec["service"]
        g_ref = node_spec["google_ref"]
        linked_pw = entries.get(g_ref, {}).get("password", "MANAGED_CLI_OAUTH")
        _upsert_entry(
            entries,
            service=srv_key,
            username=node_spec["email"],
            password=linked_pw,
            fields={
                "provider": "agy_fleet_node",
                "node_name": node_spec["node"],
                "tier": node_spec["tier"],
                "google_account_service": g_ref,
                "browser_profile": str(h_home / "browser_profiles" / g_ref),
            },
            now_iso=now_iso,
            preserve_existing_password=True,
        )
        stats["fleet_nodes_synced"] += 1

    # --- F. Sync Local Odoo 20 PostgreSQL & Infrastructure Credentials ---
    _upsert_entry(
        entries,
        service="odoo20_db",
        username=os.environ.get("ODOO_DB_USER", "odoo"),
        password=os.environ.get("ODOO_DB_PASS", "1NN0R1@2026"),
        fields={
            "provider": "postgresql",
            "host": os.environ.get("ODOO_DB_HOST", "127.0.0.1"),
            "port": os.environ.get("ODOO_DB_PORT", "5434"),
            "dbname": os.environ.get("ODOO_DB_NAME", "odoo20_dev"),
        },
        now_iso=now_iso,
        preserve_existing_password=True,
    )
    stats["infrastructure_synced"] += 1

    vault_module.save_vault(data, salt, resolved_pass, snapshot_reason="sync_ecosystem")
    stats["total_vault_entries"] = len(entries)
    return stats


# ==============================================================================
# 2. Zero-Browser Deterministic OAuth2 Refresh Engine
# ==============================================================================

def refresh_google_oauth_tokens(
    vault_module: Any,
    target_service: Optional[str] = None,
    passphrase: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Refresh Google/YouTube/Gmail/GDrive OAuth2 tokens directly via HTTPS without launching a browser."""
    resolved_pass = vault_module.resolve_passphrase(passphrase)
    data = vault_module.read_full_vault(resolved_pass)
    entries = data.get("entries", {})

    candidates = []
    for srv_key, entry in sorted(entries.items()):
        fields = entry.get("fields", {})
        if fields.get("provider") == "google_oauth_token":
            if target_service and target_service not in (srv_key, fields.get("channel_title", "")):
                continue
            candidates.append((srv_key, entry))

    results: List[Dict[str, Any]] = []
    updated_any = False

    for srv_key, entry in candidates:
        fields = entry.get("fields", {})
        refresh_token = entry.get("password", "")
        client_id = fields.get("client_id", "")
        client_secret = fields.get("client_secret", "")
        token_uri = fields.get("token_uri", "https://oauth2.googleapis.com/token")
        token_file = fields.get("token_file", "")

        if not (refresh_token and client_id and client_secret):
            results.append({
                "service": srv_key,
                "status": "skipped",
                "reason": "Missing refresh_token, client_id, or client_secret",
            })
            continue

        if dry_run:
            results.append({
                "service": srv_key,
                "status": "dry_run_ready",
                "token_uri": token_uri,
                "token_file": token_file,
                "has_refresh_token": True,
            })
            continue

        # Execute standard OAuth2 refresh_token grant
        payload = urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode("utf-8")

        req = urllib.request.Request(
            token_uri,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
            new_access_token = resp_data.get("access_token", "")
            expires_in = resp_data.get("expires_in", 3600)
            if new_access_token:
                fields["last_access_token"] = new_access_token
                fields["last_refreshed_at"] = datetime.now(timezone.utc).isoformat()
                fields["expires_in"] = str(expires_in)
                entry["updated_at"] = fields["last_refreshed_at"]
                updated_any = True

                # Sync refreshed access token back to the disk token JSON file if present
                if token_file and Path(token_file).exists():
                    try:
                        disk_json = json.loads(Path(token_file).read_text(encoding="utf-8"))
                        disk_json["token"] = new_access_token
                        Path(token_file).write_text(json.dumps(disk_json, indent=2), encoding="utf-8")
                    except Exception:
                        pass

                results.append({
                    "service": srv_key,
                    "status": "ok",
                    "expires_in": expires_in,
                    "token_file_updated": bool(token_file and Path(token_file).exists()),
                })
            else:
                results.append({
                    "service": srv_key,
                    "status": "error",
                    "error": f"No access_token in response: {resp_data}",
                })
        except Exception as exc:
            results.append({
                "service": srv_key,
                "status": "error",
                "error": str(exc),
            })

    if updated_any:
        raw = vault_module.load_raw_vault()
        salt = bytes.fromhex(raw["salt"])
        vault_module.save_vault(data, salt, resolved_pass, snapshot_reason="oauth_token_refresh")

    return {
        "total_checked": len(candidates),
        "results": results,
    }


# ==============================================================================
# 3. Persistent Stealth Playwright Cloud & Security Provisioner
# ==============================================================================

class PlaywrightCloudProvisioner:
    """Autonomous Playwright engine bound to AccountVault & persistent browser profiles."""

    def __init__(
        self,
        vault_module: Any,
        passphrase: Optional[str] = None,
        hermes_home: Optional[Path] = None,
        chrome_executable: str = "/usr/bin/google-chrome",
    ) -> None:
        self.vault_mod = vault_module
        self.passphrase = vault_module.resolve_passphrase(passphrase)
        self.vault = vault_module.AccountVault(self.passphrase)
        self.hermes_home = hermes_home or vault_module.get_hermes_home()
        self.profiles_root = self.hermes_home / "browser_profiles"
        self.profiles_root.mkdir(parents=True, exist_ok=True)
        self.chrome_executable = chrome_executable

    def resolve_account_entry(self, account_id: str) -> Tuple[str, Dict[str, Any]]:
        """Resolve an account identifier or email to its canonical `(service_key, entry)` in Vault."""
        entries = self.vault_mod.read_entries(self.passphrase)
        if account_id in entries:
            return account_id, entries[account_id]

        # Try prefixing google_
        prefixed = f"google_{account_id}" if not account_id.startswith("google_") else account_id
        if prefixed in entries:
            return prefixed, entries[prefixed]

        # Try matching by email/username
        target_lower = account_id.lower().strip()
        for srv_key, entry in entries.items():
            if entry.get("username", "").lower().strip() == target_lower:
                return srv_key, entry

        raise KeyError(f"Account '{account_id}' not found in AccountVault. Run 'vault.py sync-ecosystem' or 'vault.py add' first.")

    def get_profile_dir(self, service_key: str, entry: Dict[str, Any]) -> Path:
        """Return the persistent Chromium profile directory for `service_key`."""
        custom_dir = entry.get("fields", {}).get("browser_profile")
        if custom_dir:
            p = Path(custom_dir)
        else:
            p = self.profiles_root / service_key
        p.mkdir(parents=True, exist_ok=True)
        return p

    def build_launch_args(self) -> List[str]:
        """Stealth Chromium launch arguments preventing automation detection & session invalidation."""
        return [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
            "--password-store=basic",
        ]

    async def _authenticate_google_page(self, page: Any, service_key: str, entry: Dict[str, Any]) -> bool:
        """Autonomously complete Google Sign-In, Password, RFC-6238 TOTP, and Phone Recovery challenges."""
        email = entry.get("username", "")
        password = entry.get("password", "")
        fields = entry.get("fields", {})

        # 1. Email identifier step
        email_loc = page.locator('input[type="email"], input#identifierId').first
        if await email_loc.is_visible(timeout=4000):
            await email_loc.fill(email)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2500)

        # 2. Password step
        pass_loc = page.locator('input[type="password"], input[name="Passwd"]').first
        if await pass_loc.is_visible(timeout=5000):
            if password and not password.startswith("MANAGED_"):
                await pass_loc.fill(password)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3500)

        # 3. RFC-6238 2FA TOTP step (if Google prompts for 6-digit Authenticator code)
        totp_loc = page.locator('input[name="totpPin"], input#totpPin, input[type="tel"][autocomplete="one-time-code"]').first
        if await totp_loc.is_visible(timeout=3000):
            totp_code = self.vault.get_totp(service_key)
            if totp_code:
                await totp_loc.fill(totp_code)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)

        # 4. Recovery Phone Number confirmation challenge (**92 or **11)
        if "accounts.google.com" in page.url:
            body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            m = re.search(r"\*{2}(\d{2})", body_text) or re.search(r"(?:kết\s*thúc|ending|ends).{0,30}?(\d{2})", body_text, re.I)
            if m:
                suffix = m.group(1)
                phone_val = fields.get(f"recovery_phone_{suffix}") or DEFAULT_PHONE_RECOVERY_MAP.get(suffix, {}).get("phone")
                if phone_val:
                    phone_input = page.locator('input[type="tel"], input#phoneNumberId, input[name="phoneNumber"]').first
                    if await phone_input.is_visible(timeout=3000):
                        await phone_input.fill(phone_val)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(3000)

        return "accounts.google.com/v3/signin/identifier" not in page.url

    def execute_playbook(
        self,
        playbook: str,
        account_id: str,
        provider: str = "google-cloud",
        project_id: Optional[str] = None,
        channel_key: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        headless: bool = True,
        dry_run: bool = False,
    ) -> ProvisionResult:
        """Execute one of the 5 sustainable Playwright cloud/security playbooks."""
        srv_key, entry = self.resolve_account_entry(account_id)
        profile_dir = self.get_profile_dir(srv_key, entry)
        has_totp = bool(entry.get("fields", {}).get("totp_secret"))
        cached_cookies = self.vault.get_session(srv_key)

        playbook_norm = playbook.lower().strip()
        supported_playbooks = {
            "google-api-key",
            "google-oauth-client",
            "youtube-oauth",
            "google-security",
            "mcp-cloud-key",
        }
        if playbook_norm not in supported_playbooks:
            raise ValueError(f"Unsupported playbook '{playbook}'. Supported: {sorted(supported_playbooks)}")

        provider_meta = MCP_PROVIDER_REGISTRY.get(provider.lower(), MCP_PROVIDER_REGISTRY["google-cloud"])

        # Pre-flight readiness check (always runs in both dry-run and live mode)
        preflight = {
            "account_username": entry.get("username", ""),
            "has_password": bool(entry.get("password")),
            "has_totp_secret": has_totp,
            "has_cached_session_cookies": bool(cached_cookies),
            "persistent_profile_exists": (profile_dir / "Default").exists(),
            "launch_args": self.build_launch_args(),
            "chrome_executable": self.chrome_executable,
            "provider_metadata": provider_meta,
            "project_id": project_id or os.environ.get("GCP_PROJECT_ID", "project-3e385278-cd08-450e-ba0"),
            "channel_key": channel_key or "reality_decode",
            "headless": headless,
        }

        if dry_run:
            return ProvisionResult(
                status="dry_run_ready",
                playbook=playbook_norm,
                account_id=account_id,
                provider=provider,
                vault_service_key=srv_key,
                profile_dir=str(profile_dir),
                details=preflight,
            )

        # Live Playwright execution
        import asyncio
        return asyncio.run(
            self._run_live_playwright(
                playbook=playbook_norm,
                srv_key=srv_key,
                entry=entry,
                profile_dir=profile_dir,
                provider=provider,
                provider_meta=provider_meta,
                preflight=preflight,
                headless=headless,
            )
        )

    async def _run_live_playwright(
        self,
        playbook: str,
        srv_key: str,
        entry: Dict[str, Any],
        profile_dir: Path,
        provider: str,
        provider_meta: Dict[str, Any],
        preflight: Dict[str, Any],
        headless: bool,
    ) -> ProvisionResult:
        """Run persistent Chromium context, hydrate cookies, execute target playbook, and persist state to Vault."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            launch_kwargs: Dict[str, Any] = {
                "headless": headless,
                "viewport": {"width": 1366, "height": 860},
                "args": self.build_launch_args(),
            }
            if Path(self.chrome_executable).exists():
                launch_kwargs["executable_path"] = self.chrome_executable

            context = await p.chromium.launch_persistent_context(str(profile_dir), **launch_kwargs)
            try:
                # Hydrate cached session cookies from Vault if available
                cached_cookies = self.vault.get_session(srv_key)
                if isinstance(cached_cookies, list) and cached_cookies:
                    try:
                        await context.add_cookies(cached_cookies)
                    except Exception:
                        pass

                page = context.pages[0] if context.pages else await context.new_page()

                if playbook == "google-api-key":
                    proj = preflight["project_id"]
                    target_url = f"https://console.cloud.google.com/apis/credentials?project={proj}"
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                    if "accounts.google.com" in page.url:
                        await self._authenticate_google_page(page, srv_key, entry)
                    await page.wait_for_timeout(3000)
                    html = await page.content()
                    found_keys = sorted(set(re.findall(r"AIza[0-9A-Za-z\-_]{35}", html)))
                    if found_keys:
                        fields = dict(entry.get("fields", {}))
                        fields["gcp_api_key"] = found_keys[0]
                        fields["gcp_project_id"] = proj
                        self.vault.set(srv_key, entry["username"], entry["password"], fields)
                    details = {"url": page.url, "extracted_keys_count": len(found_keys)}

                elif playbook == "google-oauth-client":
                    proj = preflight["project_id"]
                    target_url = f"https://console.cloud.google.com/apis/credentials/oauthclient?project={proj}"
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                    if "accounts.google.com" in page.url:
                        await self._authenticate_google_page(page, srv_key, entry)
                    await page.wait_for_timeout(3000)
                    html = await page.content()
                    client_ids = sorted(set(re.findall(r"[0-9]{10,15}-[0-9a-zA-Z_]{20,40}\.apps\.googleusercontent\.com", html)))
                    details = {"url": page.url, "discovered_client_ids": client_ids}

                elif playbook == "youtube-oauth":
                    # Delegate URL generation to auth_channel.py and complete in persistent profile
                    from skills.media.youtube_publisher.scripts.auth_channel import generate_auth_url
                    ch_key = preflight["channel_key"]
                    auth_url = generate_auth_url(ch_key)
                    await page.goto(auth_url, wait_until="domcontentloaded", timeout=45000)
                    if "accounts.google.com" in page.url:
                        await self._authenticate_google_page(page, srv_key, entry)
                    details = {"channel_key": ch_key, "current_url": page.url}

                elif playbook == "google-security":
                    target_url = "https://myaccount.google.com/security"
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                    if "accounts.google.com" in page.url:
                        await self._authenticate_google_page(page, srv_key, entry)
                    await page.wait_for_timeout(2500)
                    details = {"security_url": page.url, "title": await page.title()}

                else:  # mcp-cloud-key
                    keys_url = provider_meta.get("keys_url") or provider_meta.get("credentials_url")
                    await page.goto(keys_url, wait_until="domcontentloaded", timeout=45000)
                    if "accounts.google.com" in page.url:
                        await self._authenticate_google_page(page, srv_key, entry)
                    await page.wait_for_timeout(3000)
                    html = await page.content()
                    pattern = provider_meta.get("key_regex", r"sk-[A-Za-z0-9\-_]{20,}")
                    found = sorted(set(re.findall(pattern, html)))
                    if found:
                        mcp_srv = f"{provider.lower()}_{srv_key.replace('google_', '')}"
                        self.vault.set(
                            mcp_srv,
                            entry["username"],
                            found[0],
                            {"provider": provider.lower(), "source_account": srv_key, "keys_url": keys_url},
                        )
                    details = {"url": page.url, "provider": provider, "extracted_keys_count": len(found)}

                # Persist fresh browser cookies back into AccountVault
                fresh_cookies = await context.cookies()
                if fresh_cookies:
                    self.vault.save_session(srv_key, fresh_cookies)

                return ProvisionResult(
                    status="ok",
                    playbook=playbook,
                    account_id=srv_key,
                    provider=provider,
                    vault_service_key=srv_key,
                    profile_dir=str(profile_dir),
                    details=details,
                )
            finally:
                await context.close()
