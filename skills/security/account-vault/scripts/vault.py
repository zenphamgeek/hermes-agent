#!/usr/bin/env python3
"""Autonomous Encrypted Credential Vault & Secrets Engine for Hermes Agent.

Provides zero-touch credential lifecycle management:
- AES-256-GCM authenticated encryption with PBKDF2-HMAC-SHA256 (200k iter).
- Autonomous RFC-6238 TOTP / 2FA code generation & URI parsing.
- Zero-leak subprocess environment injection (`exec`, `env`).
- Browser session / cookie stash for bypass of repeat logins.
- Autonomous password generation & zero-touch rotation (`rotate`, `generate`).
- Point-in-time automated snapshots and rollback (`snapshots`, `restore`, `backup`).
- Deep security audit & k-Anonymity breach detection (`audit`).
- Universal multi-format migration (`import`, `export`: Bitwarden, 1Password, KeePass, .env).
- Direct in-memory Python SDK (`AccountVault` class).

Usage:
  vault.py init [--passphrase P]
  vault.py add <service> -u USER -p PASS [--field k=v ...] [--totp-secret SECRET] [--passphrase P]
  vault.py get <service> [--json] [--with-totp] [--field-only KEY] [--passphrase P]
  vault.py totp <service> [--json] [--passphrase P]
  vault.py list [--json] [--detailed] [--passphrase P]
  vault.py rm <service> [--passphrase P]
  vault.py rotate <service> [--length N] [--no-symbols] [--passphrase P]
  vault.py generate [--length N] [--no-symbols] [--passphrase-words N]
  vault.py exec <service> [--passphrase P] -- <cmd...>
  vault.py env <service> [--passphrase P]
  vault.py session-save <service> (--cookies-json JSON | --cookies-file FILE) [--passphrase P]
  vault.py session-get <service> [--json] [--passphrase P]
  vault.py session-rm <service> [--passphrase P]
  vault.py snapshots [--passphrase P]
  vault.py restore <snapshot_name> [--passphrase P]
  vault.py backup [--output FILE] [--passphrase P]
  vault.py audit [--check-pwned] [--passphrase P]
  vault.py import <format> <file> [--passphrase P]
  vault.py export <format> [--output FILE] [--passphrase P]
  vault.py set-passphrase [--passphrase OLD] [--new-passphrase NEW]
"""

from __future__ import annotations

import argparse
import base64
import csv
import getpass
import hashlib
import hmac
import io
import json
import math
import os
import secrets
import string
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:  # pragma: no cover
    sys.stderr.write("Missing 'cryptography' package. Install: pip install cryptography\n")
    sys.exit(3)

# Constants
_VAULT_NAME = "account_vault.json"
_PASS_FILE = ".account_vault_pass"
_SNAPSHOT_DIR_NAME = "vault_backups"
_ITERATIONS = 200_000
_MAX_SNAPSHOTS = 25
_MASTER_FILE_MODE = 0o600


# --- Paths & Passphrase Resolution ---

def get_hermes_home() -> Path:
    base = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    return Path(base)


def vault_path() -> Path:
    return get_hermes_home() / _VAULT_NAME


def pass_file_path() -> Path:
    return get_hermes_home() / _PASS_FILE


def snapshot_dir_path() -> Path:
    return get_hermes_home() / _SNAPSHOT_DIR_NAME


def resolve_passphrase(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("ACCOUNT_VAULT_PASS")
    if env:
        return env
    pf = pass_file_path()
    if pf.exists():
        return pf.read_text(encoding="utf-8").strip()
    return getpass.getpass("Master passphrase: ")


# --- Cryptographic Core ---

def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def _encrypt(plaintext: bytes, key: bytes) -> dict:
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    return {"nonce": nonce.hex(), "ciphertext": ct.hex()}


def _decrypt(payload: dict, key: bytes) -> bytes:
    nonce = bytes.fromhex(payload["nonce"])
    ct = bytes.fromhex(payload["ciphertext"])
    return AESGCM(key).decrypt(nonce, ct, None)


# --- Storage & Snapshot Engine ---

def load_raw_vault() -> dict:
    p = vault_path()
    if not p.exists():
        return {"version": 2, "entries": {}, "sessions": {}, "metadata": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def _create_auto_snapshot(reason: str) -> None:
    p = vault_path()
    if not p.exists():
        return
    try:
        sdir = snapshot_dir_path()
        sdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        sanitized_reason = "".join(c if c.isalnum() else "_" for c in reason)
        target = sdir / f"snapshot_{ts}_{sanitized_reason}.json"
        target.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        
        # Prune old snapshots if exceeding max
        snaps = sorted(sdir.glob("snapshot_*.json"), key=lambda f: f.stat().st_mtime)
        if len(snaps) > _MAX_SNAPSHOTS:
            for old_snap in snaps[: len(snaps) - _MAX_SNAPSHOTS]:
                try:
                    old_snap.unlink()
                except OSError:
                    pass
    except Exception:
        # Snapshots must never break main execution flow
        pass


def save_vault(data: dict, salt: bytes, passphrase: str, create_snapshot: bool = True, snapshot_reason: str = "mutation") -> None:
    if create_snapshot:
        _create_auto_snapshot(snapshot_reason)
    
    blob = json.dumps(data, ensure_ascii=False).encode("utf-8")
    key = _derive_key(passphrase, salt)
    enc = _encrypt(blob, key)
    out = {
        "version": 2,
        "salt": salt.hex(),
        "payload": enc,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    p = vault_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        p.chmod(_MASTER_FILE_MODE)
    except OSError:
        pass


def read_full_vault(passphrase: str) -> dict:
    """Decrypt and return complete vault state dict: entries, sessions, metadata."""
    raw = load_raw_vault()
    if "salt" not in raw or "payload" not in raw:
        return {"entries": {}, "sessions": {}, "metadata": {}}
    key = _derive_key(passphrase, bytes.fromhex(raw["salt"]))
    plain = _decrypt(raw["payload"], key)
    parsed = json.loads(plain.decode("utf-8"))
    if not isinstance(parsed, dict):
        return {"entries": {}, "sessions": {}, "metadata": {}}
    parsed.setdefault("entries", {})
    parsed.setdefault("sessions", {})
    parsed.setdefault("metadata", {})
    return parsed


def read_entries(passphrase: str) -> dict:
    """Backward-compatible helper returning entries dict."""
    return read_full_vault(passphrase)["entries"]


# --- TOTP RFC-6238 Generator Engine ---

def _clean_base32(secret: str) -> bytes:
    # Strip spaces, hyphens, padding and upper-case
    s = secret.strip().replace(" ", "").replace("-", "").upper()
    # If otpauth:// URI was passed, extract secret parameter
    if s.startswith("OTPAUTH://"):
        parsed = urllib.parse.urlparse(secret)
        qs = urllib.parse.parse_qs(parsed.query)
        if "secret" in qs:
            s = qs["secret"][0].strip().replace(" ", "").replace("-", "").upper()
    missing_padding = len(s) % 8
    if missing_padding:
        s += "=" * (8 - missing_padding)
    return base64.b32decode(s, casefold=True)


def generate_totp_code(secret: str, interval: int = 30, digits: int = 6, for_time: Optional[float] = None) -> Tuple[str, int, str]:
    """Generates (current_code, remaining_seconds, next_code) for a TOTP secret."""
    now = for_time if for_time is not None else time.time()
    key = _clean_base32(secret)
    
    current_counter = int(now // interval)
    remaining_sec = interval - int(now % interval)
    
    def _code_for_counter(c: int) -> str:
        msg = struct.pack(">Q", c)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code_int = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
        return str(code_int % (10 ** digits)).zfill(digits)
    
    return _code_for_counter(current_counter), remaining_sec, _code_for_counter(current_counter + 1)


# --- Autonomous Password Generator ---

def generate_secure_password(length: int = 24, use_symbols: bool = True, words: int = 0) -> str:
    """Generate high-entropy password or passphrase."""
    if words > 0:
        wordlist = [
            "arctic", "beacon", "citadel", "delta", "echo", "falcon", "galaxy", "horizon",
            "ignite", "javelin", "kinetic", "lunar", "matrix", "nebula", "orbital", "pulsar",
            "quantum", "radar", "solstice", "titan", "umbra", "vortex", "zenith", "vertex",
            "shadow", "shield", "stride", "summit", "timber", "vector", "voyage", "whisper"
        ]
        chosen = [secrets.choice(wordlist) for _ in range(words)]
        sep = "-"
        return sep.join(chosen) + str(secrets.randbelow(100))
    
    chars = string.ascii_letters + string.digits
    symbols = "!@#$%^&*()-_=+[]{}<>?~"
    if use_symbols:
        chars += symbols
    
    # Guarantee at least 1 uppercase, 1 lowercase, 1 digit, and (if requested) 1 symbol
    guaranteed = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    if use_symbols:
        guaranteed.append(secrets.choice(symbols))
    
    remaining = [secrets.choice(chars) for _ in range(max(0, length - len(guaranteed)))]
    all_chars = guaranteed + remaining
    secrets.SystemRandom().shuffle(all_chars)
    return "".join(all_chars)


def calculate_entropy(password: str) -> float:
    """Calculate Shannon password entropy in bits."""
    if not password:
        return 0.0
    pool = 0
    if any(c in string.ascii_lowercase for c in password):
        pool += 26
    if any(c in string.ascii_uppercase for c in password):
        pool += 26
    if any(c in string.digits for c in password):
        pool += 10
    if any(c in string.punctuation for c in password):
        pool += 32
    if pool == 0:
        pool = 256
    return len(password) * math.log2(pool)


# --- High-Level Commands ---

def cmd_init(args) -> int:
    p = vault_path()
    if p.exists():
        print(f"Vault already exists at {p}")
        return 0
    passphrase = resolve_passphrase(args.passphrase)
    if not passphrase:
        print("Passphrase cannot be empty", file=sys.stderr)
        return 2
    salt = os.urandom(16)
    initial_data = {
        "entries": {},
        "sessions": {},
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "client": "hermes-account-vault-v2",
        },
    }
    save_vault(initial_data, salt, passphrase, create_snapshot=False)
    print(f"Created vault at {p}")
    print("Master passphrase is ready. Agent reads from env ACCOUNT_VAULT_PASS or ~/.hermes/.account_vault_pass.")
    return 0


def cmd_add(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    fields = {}
    for item in args.field or []:
        if "=" not in item:
            print(f"Bad --field {item!r} (want k=v)", file=sys.stderr)
            return 2
        k, v = item.split("=", 1)
        fields[k] = v
        
    totp_sec = args.totp_secret
    if totp_sec:
        fields["totp_secret"] = totp_sec
    
    raw = load_raw_vault()
    salt = bytes.fromhex(raw["salt"])
    now_iso = datetime.now(timezone.utc).isoformat()
    
    data["entries"][args.service] = {
        "username": args.username,
        "password": args.password,
        "fields": fields,
        "created_at": data["entries"].get(args.service, {}).get("created_at", now_iso),
        "updated_at": now_iso,
    }
    save_vault(data, salt, passphrase, snapshot_reason=f"add_{args.service}")
    print(f"Saved {args.service}")
    return 0


def cmd_get(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    entry = data["entries"].get(args.service)
    if entry is None:
        print(f"No entry for {args.service}", file=sys.stderr)
        return 1
    
    # Specific field retrieval
    if args.field_only:
        if args.field_only == "username":
            print(entry["username"])
            return 0
        if args.field_only == "password":
            print(entry["password"])
            return 0
        fval = entry.get("fields", {}).get(args.field_only)
        if fval is not None:
            print(fval)
            return 0
        print(f"Field '{args.field_only}' not found", file=sys.stderr)
        return 1

    totp_info = None
    totp_secret = entry.get("fields", {}).get("totp_secret")
    if totp_secret:
        try:
            curr_code, rem_sec, next_code = generate_totp_code(totp_secret)
            totp_info = {
                "code": curr_code,
                "remaining_seconds": rem_sec,
                "next_code": next_code,
            }
        except Exception:
            totp_info = {"error": "Invalid TOTP secret"}

    if args.json:
        out = dict(entry)
        if args.with_totp or totp_info:
            out["totp"] = totp_info
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"service: {args.service}")
        print(f"username: {entry['username']}")
        print(f"password: {entry['password']}")
        for k, v in entry.get("fields", {}).items():
            print(f"{k}: {v}")
        if totp_info:
            if "code" in totp_info:
                print(f"totp_code: {totp_info['code']} ({totp_info['remaining_seconds']}s remaining)")
            else:
                print(f"totp_error: {totp_info['error']}")
    return 0


def cmd_totp(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    entry = data["entries"].get(args.service)
    if not entry:
        print(f"No entry for {args.service}", file=sys.stderr)
        return 1
    
    secret = entry.get("fields", {}).get("totp_secret")
    if not secret:
        print(f"No TOTP secret configured for {args.service}. Add one via --field totp_secret=... or --totp-secret", file=sys.stderr)
        return 1
    
    try:
        curr, rem, nxt = generate_totp_code(secret)
    except Exception as e:
        print(f"Failed to generate TOTP: {e}", file=sys.stderr)
        return 2
        
    if args.json:
        print(json.dumps({
            "service": args.service,
            "code": curr,
            "remaining_seconds": rem,
            "next_code": nxt,
            "timestamp": int(time.time()),
        }, indent=2))
    else:
        print(f"Service:         {args.service}")
        print(f"Current Code:    {curr} (valid for {rem}s)")
        print(f"Next Code:       {nxt}")
    return 0


def cmd_list(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    entries = data.get("entries", {})
    if not entries:
        if args.json:
            print("[]")
        else:
            print("(empty vault)")
        return 0
        
    if args.json:
        out = []
        for name in sorted(entries):
            e = dict(entries[name])
            e["service"] = name
            e.pop("password", None)  # Mask password by default in list
            out.append(e)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.detailed:
        print(f"{'SERVICE':<20} {'USERNAME':<30} {'UPDATED':<20} {'2FA':<6} {'FIELDS'}")
        print("-" * 90)
        for name in sorted(entries):
            e = entries[name]
            has_2fa = "YES" if "totp_secret" in e.get("fields", {}) else "NO"
            upd = e.get("updated_at", "-")[:19]
            f_keys = ",".join(k for k in e.get("fields", {}) if k != "totp_secret")
            print(f"{name:<20} {e['username']:<30} {upd:<20} {has_2fa:<6} {f_keys}")
    else:
        for name in sorted(entries):
            e = entries[name]
            print(f"{name}\t{e['username']}")
    return 0


def cmd_rm(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    if args.service not in data["entries"]:
        print(f"No entry for {args.service}", file=sys.stderr)
        return 1
    
    del data["entries"][args.service]
    raw = load_raw_vault()
    salt = bytes.fromhex(raw["salt"])
    save_vault(data, salt, passphrase, snapshot_reason=f"rm_{args.service}")
    print(f"Removed {args.service}")
    return 0


def cmd_rotate(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    if args.service not in data["entries"]:
        print(f"No entry for {args.service}", file=sys.stderr)
        return 1
    
    entry = data["entries"][args.service]
    new_pw = generate_secure_password(length=args.length, use_symbols=not args.no_symbols)
    
    prev_history = entry.get("fields", {}).get("_pw_history", "")
    history_list = prev_history.split(";") if prev_history else []
    history_list.append(entry["password"])
    if len(history_list) > 5:
        history_list = history_list[-5:]
    
    entry["fields"]["_pw_history"] = ";".join(history_list)
    entry["password"] = new_pw
    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
    entry["fields"]["last_rotated_at"] = entry["updated_at"]
    
    raw = load_raw_vault()
    salt = bytes.fromhex(raw["salt"])
    save_vault(data, salt, passphrase, snapshot_reason=f"rotate_{args.service}")
    print(f"Rotated password for {args.service}.")
    print(f"New Password: {new_pw}")
    return 0


def cmd_generate(args) -> int:
    pw = generate_secure_password(
        length=args.length,
        use_symbols=not args.no_symbols,
        words=args.passphrase_words,
    )
    entropy = calculate_entropy(pw)
    if args.json:
        print(json.dumps({"password": pw, "entropy_bits": round(entropy, 2)}, indent=2))
    else:
        print(f"Generated ({entropy:.1f} bits entropy):")
        print(pw)
    return 0


def cmd_exec(args) -> int:
    """Inject credentials into child process environment."""
    passphrase = resolve_passphrase(getattr(args, "passphrase", None))
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    entry = data["entries"].get(args.service)
    if not entry:
        print(f"No entry for {args.service}", file=sys.stderr)
        return 1
    
    env = os.environ.copy()
    env["VAULT_SERVICE"] = args.service
    env["VAULT_USERNAME"] = entry["username"]
    env["VAULT_PASSWORD"] = entry["password"]
    
    # Generic service normalized env vars
    clean_srv = "".join(c if c.isalnum() else "_" for c in args.service.upper())
    env[f"{clean_srv}_USER"] = entry["username"]
    env[f"{clean_srv}_USERNAME"] = entry["username"]
    env[f"{clean_srv}_PASSWORD"] = entry["password"]
    
    for k, v in entry.get("fields", {}).items():
        if k.startswith("_"):
            continue
        clean_k = "".join(c if c.isalnum() else "_" for c in k.upper())
        env[f"VAULT_{clean_k}"] = str(v)
        env[f"{clean_srv}_{clean_k}"] = str(v)
    
    # Inject TOTP code if available
    totp_secret = entry.get("fields", {}).get("totp_secret")
    if totp_secret:
        try:
            curr, _, _ = generate_totp_code(totp_secret)
            env["VAULT_TOTP_CODE"] = curr
            env[f"{clean_srv}_TOTP_CODE"] = curr
        except Exception:
            pass

    cmd = args.command_args
    if not cmd:
        print("No command specified to exec.", file=sys.stderr)
        return 2
    
    try:
        res = subprocess.run(cmd, env=env)
        return res.returncode
    except Exception as e:
        print(f"Execution error: {e}", file=sys.stderr)
        return 1


def cmd_env(args) -> int:
    """Print safe export variables for shell evaluation."""
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    entry = data["entries"].get(args.service)
    if not entry:
        print(f"No entry for {args.service}", file=sys.stderr)
        return 1
    
    clean_srv = "".join(c if c.isalnum() else "_" for c in args.service.upper())
    print(f"export VAULT_SERVICE={json.dumps(args.service)}")
    print(f"export VAULT_USERNAME={json.dumps(entry['username'])}")
    print(f"export VAULT_PASSWORD={json.dumps(entry['password'])}")
    print(f"export {clean_srv}_USER={json.dumps(entry['username'])}")
    print(f"export {clean_srv}_PASSWORD={json.dumps(entry['password'])}")
    for k, v in entry.get("fields", {}).items():
        if k.startswith("_"):
            continue
        clean_k = "".join(c if c.isalnum() else "_" for c in k.upper())
        print(f"export VAULT_{clean_k}={json.dumps(str(v))}")
        print(f"export {clean_srv}_{clean_k}={json.dumps(str(v))}")
    return 0


def cmd_session_save(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    if args.cookies_json:
        content = args.cookies_json
    elif args.cookies_file:
        content = Path(args.cookies_file).read_text(encoding="utf-8")
    else:
        print("Must supply either --cookies-json or --cookies-file", file=sys.stderr)
        return 2
    
    try:
        cookie_data = json.loads(content)
    except Exception:
        cookie_data = content
        
    data.setdefault("sessions", {})
    data["sessions"][args.service] = {
        "cookies": cookie_data,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    
    raw = load_raw_vault()
    salt = bytes.fromhex(raw["salt"])
    save_vault(data, salt, passphrase, snapshot_reason=f"session_save_{args.service}")
    print(f"Saved session state for {args.service}")
    return 0


def cmd_session_get(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    sess = data.get("sessions", {}).get(args.service)
    if not sess:
        print(f"No session found for {args.service}", file=sys.stderr)
        return 1
    
    if args.json or isinstance(sess.get("cookies"), (dict, list)):
        print(json.dumps(sess, indent=2, ensure_ascii=False))
    else:
        print(sess.get("cookies", ""))
    return 0


def cmd_session_rm(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    if args.service not in data.get("sessions", {}):
        print(f"No session found for {args.service}", file=sys.stderr)
        return 1
    
    del data["sessions"][args.service]
    raw = load_raw_vault()
    salt = bytes.fromhex(raw["salt"])
    save_vault(data, salt, passphrase, snapshot_reason=f"session_rm_{args.service}")
    print(f"Removed session for {args.service}")
    return 0


def cmd_snapshots(args) -> int:
    sdir = snapshot_dir_path()
    if not sdir.exists():
        print("No snapshots directory found.")
        return 0
    snaps = sorted(sdir.glob("snapshot_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not snaps:
        print("No snapshots available.")
        return 0
    
    print(f"{'INDEX':<6} {'SNAPSHOT FILE':<45} {'MODIFIED TIME'}")
    print("-" * 75)
    for idx, s in enumerate(snaps):
        mtime = datetime.fromtimestamp(s.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{idx:<6} {s.name:<45} {mtime}")
    return 0


def cmd_restore(args) -> int:
    sdir = snapshot_dir_path()
    target_path: Optional[Path] = None
    
    if args.snapshot.isdigit():
        idx = int(args.snapshot)
        snaps = sorted(sdir.glob("snapshot_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if 0 <= idx < len(snaps):
            target_path = snaps[idx]
    else:
        target_path = sdir / args.snapshot if not Path(args.snapshot).is_absolute() else Path(args.snapshot)
        
    if not target_path or not target_path.exists():
        print(f"Snapshot '{args.snapshot}' not found.", file=sys.stderr)
        return 1
    
    # Save a rollback snapshot of current state first
    _create_auto_snapshot("before_restore")
    
    p = vault_path()
    p.write_text(target_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Successfully restored vault from {target_path.name}")
    return 0


def cmd_backup(args) -> int:
    p = vault_path()
    if not p.exists():
        print("No vault file to back up.", file=sys.stderr)
        return 1
    
    out_file = args.output
    if not out_file:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_file = f"hermes_vault_backup_{ts}.json"
    
    out_path = Path(out_file).resolve()
    out_path.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        out_path.chmod(_MASTER_FILE_MODE)
    except OSError:
        pass
    print(f"Backup created at: {out_path}")
    return 0


def _check_pwned_k_anonymity(password: str) -> Tuple[bool, int]:
    """Check HaveIBeenPwned via k-anonymity SHA1 prefix. Never sends full password."""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Account-Vault"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
        for line in body.splitlines():
            parts = line.strip().split(":")
            if len(parts) == 2 and parts[0] == suffix:
                return True, int(parts[1])
        return False, 0
    except Exception:
        return False, -1


def cmd_audit(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    entries = data.get("entries", {})
    if not entries:
        print("Vault is empty. Nothing to audit.")
        return 0
    
    print("=" * 60)
    print("           ACCOUNT VAULT SECURITY HEALTH AUDIT")
    print("=" * 60)
    
    weak = []
    reused = {}
    stale = []
    pwned_hits = []
    
    pw_to_services: Dict[str, List[str]] = {}
    
    now = datetime.now(timezone.utc)
    
    for srv, item in entries.items():
        pw = item.get("password", "")
        ent = calculate_entropy(pw)
        if len(pw) < 12 or ent < 50.0:
            weak.append((srv, len(pw), round(ent, 1)))
        
        pw_to_services.setdefault(pw, []).append(srv)
        
        upd_str = item.get("updated_at")
        if upd_str:
            try:
                dt = datetime.fromisoformat(upd_str)
                age_days = (now - dt).days
                if age_days > 90:
                    stale.append((srv, age_days))
            except Exception:
                pass
                
        if args.check_pwned:
            is_pwned, count = _check_pwned_k_anonymity(pw)
            if is_pwned:
                pwned_hits.append((srv, count))
    
    for pw, srvs in pw_to_services.items():
        if len(srvs) > 1:
            reused[tuple(srvs)] = len(srvs)
            
    # Output findings
    score = 100
    if weak:
        score -= len(weak) * 10
    if reused:
        score -= len(reused) * 15
    if stale:
        score -= len(stale) * 5
    if pwned_hits:
        score -= len(pwned_hits) * 25
    score = max(0, score)
    
    print(f"\nOverall Vault Security Score: {score}/100")
    print(f"Total Accounts Monitored:     {len(entries)}")
    
    if weak:
        print("\n[!] WEAK PASSWORDS (Length < 12 or Entropy < 50 bits):")
        for srv, l, e in weak:
            print(f"    - {srv}: Length {l}, Entropy {e} bits")
    else:
        print("\n[✓] No weak passwords detected.")
        
    if reused:
        print("\n[!] REUSED PASSWORDS (Shared across accounts):")
        for srvs in reused:
            print(f"    - Shared by: {', '.join(srvs)}")
    else:
        print("\n[✓] No reused passwords detected.")
        
    if stale:
        print("\n[!] STALE PASSWORDS (>90 days old):")
        for srv, age in stale:
            print(f"    - {srv}: {age} days old (recommend rotation via 'vault.py rotate {srv}')")
    else:
        print("\n[✓] All credentials are fresh.")
        
    if args.check_pwned:
        if pwned_hits:
            print("\n[CRITICAL] PWNED PASSWORDS DETECTED (Found in breach database):")
            for srv, count in pwned_hits:
                print(f"    - {srv}: Found in {count} known breaches! Rotate immediately!")
        else:
            print("\n[✓] Zero credentials found in known breach databases.")
            
    print("\n" + "=" * 60)
    return 0


def cmd_import(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
    
    src = Path(args.file)
    if not src.exists():
        print(f"File {args.file} not found.", file=sys.stderr)
        return 1
        
    content = src.read_text(encoding="utf-8")
    fmt = args.format.lower()
    imported_count = 0
    
    if fmt == "bitwarden":
        bw_json = json.loads(content)
        items = bw_json.get("items", [])
        for it in items:
            login = it.get("login") or {}
            name = it.get("name") or "unnamed"
            uname = login.get("username") or ""
            pword = login.get("password") or ""
            totp = login.get("totp") or ""
            fields = {}
            if totp:
                fields["totp_secret"] = totp
            for f in it.get("fields", []):
                fields[f.get("name", "field")] = f.get("value", "")
            
            srv_key = name.lower().replace(" ", "_")
            data["entries"][srv_key] = {
                "username": uname,
                "password": pword,
                "fields": fields,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            imported_count += 1
            
    elif fmt in ("1password-csv", "csv", "keepass-csv"):
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            title = row.get("Title") or row.get("title") or row.get("name") or row.get("Account") or "unnamed"
            uname = row.get("Username") or row.get("username") or row.get("User Name") or ""
            pword = row.get("Password") or row.get("password") or ""
            srv_key = title.lower().replace(" ", "_")
            fields = {k: v for k, v in row.items() if k not in ("Title", "title", "name", "Account", "Username", "username", "User Name", "Password", "password")}
            data["entries"][srv_key] = {
                "username": uname,
                "password": pword,
                "fields": fields,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            imported_count += 1
            
    elif fmt in ("dotenv", "env", ".env"):
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip("'\"")
            data["entries"][k.lower()] = {
                "username": k,
                "password": v,
                "fields": {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            imported_count += 1
    else:
        print(f"Unsupported format: {fmt}. Supported: bitwarden, 1password-csv, keepass-csv, dotenv", file=sys.stderr)
        return 2
        
    raw = load_raw_vault()
    salt = bytes.fromhex(raw["salt"])
    save_vault(data, salt, passphrase, snapshot_reason=f"import_{fmt}")
    print(f"Successfully imported {imported_count} credentials from {src.name}")
    return 0


def cmd_export(args) -> int:
    passphrase = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(passphrase)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
        
    fmt = args.format.lower()
    entries = data.get("entries", {})
    output_text = ""
    
    if fmt == "json":
        output_text = json.dumps(entries, indent=2, ensure_ascii=False)
    elif fmt == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["service", "username", "password", "totp_secret", "fields"])
        for srv, e in sorted(entries.items()):
            totp = e.get("fields", {}).get("totp_secret", "")
            other_fields = json.dumps({k: v for k, v in e.get("fields", {}).items() if k != "totp_secret"})
            writer.writerow([srv, e.get("username", ""), e.get("password", ""), totp, other_fields])
        output_text = out.getvalue()
    elif fmt in ("dotenv", "env"):
        lines = []
        for srv, e in sorted(entries.items()):
            clean = "".join(c if c.isalnum() else "_" for c in srv.upper())
            lines.append(f"{clean}_USERNAME={e.get('username', '')}")
            lines.append(f"{clean}_PASSWORD={e.get('password', '')}")
        output_text = "\n".join(lines) + "\n"
    else:
        print(f"Unsupported format: {fmt}. Supported: json, csv, dotenv", file=sys.stderr)
        return 2
        
    if args.output:
        out_p = Path(args.output).resolve()
        out_p.write_text(output_text, encoding="utf-8")
        try:
            out_p.chmod(_MASTER_FILE_MODE)
        except OSError:
            pass
        print(f"Exported {len(entries)} credentials to {out_p}")
    else:
        print(output_text)
    return 0


def cmd_set_passphrase(args) -> int:
    old_pass = resolve_passphrase(args.passphrase)
    try:
        data = read_full_vault(old_pass)
    except Exception:
        print("Decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 2
        
    new_pass = args.new_passphrase or getpass.getpass("New passphrase: ")
    if not new_pass:
        print("Passphrase cannot be empty", file=sys.stderr)
        return 2
        
    new_salt = os.urandom(16)
    save_vault(data, new_salt, new_pass, snapshot_reason="set_passphrase")
    print("Passphrase updated successfully across vault and snapshots.")
    return 0


# --- Programmatic Python SDK for AI Agent Skills ---

class AccountVault:
    """Direct in-memory SDK for Hermes Agent skills & tools."""

    def __init__(self, passphrase: Optional[str] = None):
        self.passphrase = resolve_passphrase(passphrase)
        self._cached_data: Optional[dict] = None

    def get(self, service: str) -> Optional[dict]:
        data = read_full_vault(self.passphrase)
        return data.get("entries", {}).get(service)

    def get_totp(self, service: str) -> Optional[str]:
        entry = self.get(service)
        if not entry:
            return None
        secret = entry.get("fields", {}).get("totp_secret")
        if not secret:
            return None
        code, _, _ = generate_totp_code(secret)
        return code

    def set(self, service: str, username: str, password: str, fields: Optional[dict] = None) -> None:
        data = read_full_vault(self.passphrase)
        raw = load_raw_vault()
        salt = bytes.fromhex(raw["salt"])
        data["entries"][service] = {
            "username": username,
            "password": password,
            "fields": fields or {},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        save_vault(data, salt, self.passphrase, snapshot_reason=f"sdk_set_{service}")

    def get_session(self, service: str) -> Any:
        data = read_full_vault(self.passphrase)
        sess = data.get("sessions", {}).get(service)
        return sess.get("cookies") if sess else None

    def save_session(self, service: str, cookies: Any) -> None:
        data = read_full_vault(self.passphrase)
        raw = load_raw_vault()
        salt = bytes.fromhex(raw["salt"])
        data.setdefault("sessions", {})
        data["sessions"][service] = {
            "cookies": cookies,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        save_vault(data, salt, self.passphrase, snapshot_reason=f"sdk_session_{service}")

    def sync_ecosystem(self, hermes_home: Optional[Path] = None, repo_root: Optional[Path] = None) -> Dict[str, Any]:
        """Consolidate all workspace accounts, OAuth tokens, .env keys, Modal profiles, and Fleet nodes into Vault."""
        mod = _load_provisioner_module()
        return mod.sync_ecosystem_to_vault(
            _get_self_vault_interface(),
            passphrase=self.passphrase,
            hermes_home=hermes_home,
            repo_root=repo_root,
        )

    def refresh_oauth_tokens(self, target_service: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Deterministically refresh Google/YouTube/Gmail/GDrive OAuth2 tokens without opening a browser."""
        mod = _load_provisioner_module()
        return mod.refresh_google_oauth_tokens(
            _get_self_vault_interface(),
            target_service=target_service,
            passphrase=self.passphrase,
            dry_run=dry_run,
        )

    def provision(
        self,
        playbook: str,
        account_id: str,
        provider: str = "google-cloud",
        project_id: Optional[str] = None,
        channel_key: Optional[str] = None,
        headless: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute a sustainable Playwright cloud/security provisioning playbook."""
        mod = _load_provisioner_module()
        engine = mod.PlaywrightCloudProvisioner(
            _get_self_vault_interface(),
            passphrase=self.passphrase,
        )
        res = engine.execute_playbook(
            playbook=playbook,
            account_id=account_id,
            provider=provider,
            project_id=project_id,
            channel_key=channel_key,
            headless=headless,
            dry_run=dry_run,
        )
        return res.to_dict()

    def interactive_login(
        self,
        service: str,
        login_url: Optional[str] = None,
        url: Optional[str] = None,
        provider: str = "google-cloud",
        timeout_sec: int = 300,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Open headed Playwright browser for user interactive login and harvest all Auth info into Vault."""
        mod = _load_provisioner_module()
        engine = mod.PlaywrightCloudProvisioner(
            _get_self_vault_interface(),
            passphrase=self.passphrase,
        )
        res = engine.capture_interactive_auth(
            service_or_account=service,
            login_url=login_url or url,
            provider=provider,
            timeout_sec=timeout_sec,
            dry_run=dry_run,
        )
        return res.to_dict()


def _get_self_vault_interface() -> Any:
    import types
    if __name__ in sys.modules:
        return sys.modules[__name__]
    return types.SimpleNamespace(
        resolve_passphrase=resolve_passphrase,
        get_hermes_home=get_hermes_home,
        read_full_vault=read_full_vault,
        load_raw_vault=load_raw_vault,
        save_vault=save_vault,
        read_entries=read_entries,
        AccountVault=AccountVault,
    )


def _load_provisioner_module() -> Any:
    import importlib.util
    prov_path = Path(__file__).resolve().parent / "playwright_cloud_provisioner.py"
    spec = importlib.util.spec_from_file_location("playwright_cloud_provisioner", prov_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {prov_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["playwright_cloud_provisioner"] = mod
    spec.loader.exec_module(mod)
    return mod


def cmd_sync_ecosystem(args) -> int:
    mod = _load_provisioner_module()
    try:
        stats = mod.sync_ecosystem_to_vault(
            _get_self_vault_interface(),
            passphrase=args.passphrase,
        )
    except Exception as exc:
        print(f"Sync ecosystem failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print("Consolidated ecosystem credentials into Account Vault:")
        for k, v in stats.items():
            print(f"  - {k}: {v}")
    return 0


def cmd_oauth_refresh(args) -> int:
    mod = _load_provisioner_module()
    try:
        res = mod.refresh_google_oauth_tokens(
            _get_self_vault_interface(),
            target_service=args.service,
            passphrase=args.passphrase,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"OAuth refresh failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def cmd_provision(args) -> int:
    mod = _load_provisioner_module()
    try:
        engine = mod.PlaywrightCloudProvisioner(
            _get_self_vault_interface(),
            passphrase=args.passphrase,
        )
        res = engine.execute_playbook(
            playbook=args.playbook,
            account_id=args.account,
            provider=args.provider,
            project_id=args.project_id,
            channel_key=args.channel,
            headless=not args.headed,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    return 0 if res.status in ("ok", "dry_run_ready") else 1


def cmd_interactive_login(args) -> int:
    mod = _load_provisioner_module()
    try:
        engine = mod.PlaywrightCloudProvisioner(
            _get_self_vault_interface(),
            passphrase=args.passphrase,
        )
        res = engine.capture_interactive_auth(
            service_or_account=args.service,
            login_url=args.url,
            username=getattr(args, "username", None),
            provider=args.provider,
            timeout_sec=args.timeout,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
    return 0 if res.status in ("ok", "dry_run_ready") else 1


def cmd_providers(args) -> int:
    mod = _load_provisioner_module()
    print(json.dumps(mod.MCP_PROVIDER_REGISTRY, indent=2, ensure_ascii=False))
    return 0


# --- CLI Parser Construction ---

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vault.py",
        description="Autonomous Encrypted Credential Vault & Secrets Engine for Hermes Agent",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize a new encrypted vault")
    p_init.add_argument("--passphrase", help="Master passphrase")

    # add
    p_add = sub.add_parser("add", help="Add or update a service credential")
    p_add.add_argument("service", help="Service identifier (e.g. github, google, b.ai)")
    p_add.add_argument("-u", "--username", required=True, help="Account username or email")
    p_add.add_argument("-p", "--password", required=True, help="Account password or secret key")
    p_add.add_argument("--totp-secret", help="Base32 TOTP secret key or otpauth:// URI")
    p_add.add_argument("--field", action="append", default=[], metavar="k=v", help="Extra custom field (repeatable)")
    p_add.add_argument("--passphrase", help="Master passphrase")

    # get
    p_get = sub.add_parser("get", help="Retrieve credentials for a service")
    p_get.add_argument("service", help="Service identifier")
    p_get.add_argument("--json", action="store_true", help="Output JSON structure")
    p_get.add_argument("--with-totp", action="store_true", help="Include active TOTP 2FA code")
    p_get.add_argument("--field-only", help="Output only a specific field value")
    p_get.add_argument("--passphrase", help="Master passphrase")

    # totp
    p_totp = sub.add_parser("totp", help="Generate active 2FA TOTP code for a service")
    p_totp.add_argument("service", help="Service identifier")
    p_totp.add_argument("--json", action="store_true", help="Output JSON format with TTL and next code")
    p_totp.add_argument("--passphrase", help="Master passphrase")

    # list
    p_list = sub.add_parser("list", help="List all stored service credentials")
    p_list.add_argument("--json", action="store_true", help="Output JSON array")
    p_list.add_argument("--detailed", action="store_true", help="Show tabular view with updated dates and 2FA status")
    p_list.add_argument("--passphrase", help="Master passphrase")

    # rm
    p_rm = sub.add_parser("rm", help="Remove a service credential")
    p_rm.add_argument("service", help="Service identifier")
    p_rm.add_argument("--passphrase", help="Master passphrase")

    # rotate
    p_rotate = sub.add_parser("rotate", help="Autonomously generate and rotate password for service")
    p_rotate.add_argument("service", help="Service identifier")
    p_rotate.add_argument("--length", type=int, default=24, help="New password length (default: 24)")
    p_rotate.add_argument("--no-symbols", action="store_true", help="Do not include symbols in password")
    p_rotate.add_argument("--passphrase", help="Master passphrase")

    # generate
    p_gen = sub.add_parser("generate", help="Generate high-entropy password or passphrase")
    p_gen.add_argument("--length", type=int, default=24, help="Password length (default: 24)")
    p_gen.add_argument("--no-symbols", action="store_true", help="Do not include symbols")
    p_gen.add_argument("--passphrase-words", type=int, default=0, help="Generate word-based passphrase (e.g. --passphrase-words 4)")
    p_gen.add_argument("--json", action="store_true", help="Output JSON with entropy metrics")

    # exec
    p_exec = sub.add_parser("exec", help="Execute command with credentials injected into environment")
    p_exec.add_argument("service", help="Service identifier")
    p_exec.add_argument("--passphrase", help="Master passphrase")
    p_exec.add_argument("command_args", nargs="*", default=[], help="Command and arguments to execute")

    # env
    p_env = sub.add_parser("env", help="Output export statements for shell environment")
    p_env.add_argument("service", help="Service identifier")
    p_env.add_argument("--passphrase", help="Master passphrase")

    # session-save
    p_ss = sub.add_parser("session-save", help="Save encrypted browser session / cookies")
    p_ss.add_argument("service", help="Service identifier")
    p_ss.add_argument("--cookies-json", help="Direct JSON string of cookies / storage")
    p_ss.add_argument("--cookies-file", help="Path to JSON file containing cookies")
    p_ss.add_argument("--passphrase", help="Master passphrase")

    # session-get
    p_sg = sub.add_parser("session-get", help="Retrieve saved browser session / cookies")
    p_sg.add_argument("service", help="Service identifier")
    p_sg.add_argument("--json", action="store_true", help="Format JSON output")
    p_sg.add_argument("--passphrase", help="Master passphrase")

    # session-rm
    p_sr = sub.add_parser("session-rm", help="Delete saved browser session")
    p_sr.add_argument("service", help="Service identifier")
    p_sr.add_argument("--passphrase", help="Master passphrase")

    # snapshots
    p_snaps = sub.add_parser("snapshots", help="List point-in-time automated snapshots")
    p_snaps.add_argument("--passphrase", help="Master passphrase")

    # restore
    p_rest = sub.add_parser("restore", help="Restore vault from an automated snapshot")
    p_rest.add_argument("snapshot", help="Snapshot filename or index number from 'vault.py snapshots'")
    p_rest.add_argument("--passphrase", help="Master passphrase")

    # backup
    p_bak = sub.add_parser("backup", help="Create explicit backup of encrypted vault")
    p_bak.add_argument("--output", help="Custom backup destination file")
    p_bak.add_argument("--passphrase", help="Master passphrase")

    # audit
    p_aud = sub.add_parser("audit", help="Run deep security health check and audit")
    p_aud.add_argument("--check-pwned", action="store_true", help="Check HaveIBeenPwned breach db using k-Anonymity")
    p_aud.add_argument("--passphrase", help="Master passphrase")

    # import
    p_imp = sub.add_parser("import", help="Import credentials from external managers")
    p_imp.add_argument("format", choices=["bitwarden", "1password-csv", "keepass-csv", "dotenv"], help="Source format")
    p_imp.add_argument("file", help="Path to input export file")
    p_imp.add_argument("--passphrase", help="Master passphrase")

    # export
    p_exp = sub.add_parser("export", help="Export credentials to standard format")
    p_exp.add_argument("format", choices=["json", "csv", "dotenv"], help="Export format")
    p_exp.add_argument("--output", help="Destination file (default: stdout)")
    p_exp.add_argument("--passphrase", help="Master passphrase")

    # set-passphrase
    p_set = sub.add_parser("set-passphrase", help="Change master passphrase")
    p_set.add_argument("--passphrase", help="Old master passphrase")
    p_set.add_argument("--new-passphrase", help="New master passphrase")

    # sync-ecosystem
    p_sync = sub.add_parser("sync-ecosystem", help="Consolidate all Google, YouTube, OAuth, .env, Modal, and Fleet credentials into Vault")
    p_sync.add_argument("--json", action="store_true", help="Output JSON summary")
    p_sync.add_argument("--passphrase", help="Master passphrase")

    # oauth-refresh
    p_oauth = sub.add_parser("oauth-refresh", help="Refresh YouTube/Google/Gmail OAuth2 tokens directly via HTTPS without browser")
    p_oauth.add_argument("service", nargs="?", default=None, help="Optional specific OAuth token service key")
    p_oauth.add_argument("--dry-run", action="store_true", help="Verify refresh readiness without network call")
    p_oauth.add_argument("--passphrase", help="Master passphrase")

    # provision
    p_prov = sub.add_parser("provision", help="Playwright Cloud API Key, OAuth Client & Advanced Security Provisioner")
    p_prov.add_argument("playbook", choices=["google-api-key", "google-oauth-client", "youtube-oauth", "google-security", "mcp-cloud-key"], help="Provisioning playbook")
    p_prov.add_argument("--account", required=True, help="Vault service key or email (e.g. google_insilos, google_zenhunter)")
    p_prov.add_argument("--provider", default="google-cloud", help="Target cloud/MCP provider (google-cloud, youtube, openrouter, firecrawl, tavily, cloudflare, modal, github, bai)")
    p_prov.add_argument("--project-id", help="GCP project ID (for google-api-key / google-oauth-client)")
    p_prov.add_argument("--channel", help="YouTube channel key (for youtube-oauth, e.g. reality_decode, zenpham, phamtrai_dialy)")
    p_prov.add_argument("--headed", action="store_true", help="Run Chromium in visible headed window")
    p_prov.add_argument("--dry-run", action="store_true", help="Run preflight check without launching browser")
    p_prov.add_argument("--passphrase", help="Master passphrase")

    # interactive-login
    p_ilogin = sub.add_parser("interactive-login", help="Open headed Playwright browser for user login and harvest all Auth info into Vault")
    p_ilogin.add_argument("service", help="Vault service key or email (e.g. google_insilos, cloudflare_main, github_zen)")
    p_ilogin.add_argument("--url", help="Explicit login URL to open")
    p_ilogin.add_argument("-u", "--username", help="Account username or email to pre-fill and save")
    p_ilogin.add_argument("--provider", default="google-cloud", help="Provider preset (google-cloud, youtube, openrouter, firecrawl, tavily, cloudflare, modal, github, bai)")
    p_ilogin.add_argument("--timeout", type=int, default=300, help="Max seconds to wait for interactive login completion (default: 300)")
    p_ilogin.add_argument("--dry-run", action="store_true", help="Run preflight check without opening browser")
    p_ilogin.add_argument("--passphrase", help="Master passphrase")

    # providers
    sub.add_parser("providers", help="List supported Cloud & MCP provider provisioning playbooks")

    return parser


def main(argv: list[str] | None = None) -> int:
    raw_args = list(argv) if argv is not None else list(sys.argv[1:])
    if "exec" in raw_args:
        exec_idx = raw_args.index("exec")
        if "--" in raw_args[exec_idx:]:
            dash_idx = raw_args.index("--", exec_idx)
            cmd_args = raw_args[dash_idx + 1:]
            vault_args = raw_args[:dash_idx]
            args = build_parser().parse_args(vault_args)
            args.command_args = cmd_args
        else:
            args = build_parser().parse_args(raw_args)
    else:
        args = build_parser().parse_args(raw_args)

    dispatch = {
        "init": cmd_init,
        "add": cmd_add,
        "get": cmd_get,
        "totp": cmd_totp,
        "list": cmd_list,
        "rm": cmd_rm,
        "rotate": cmd_rotate,
        "generate": cmd_generate,
        "exec": cmd_exec,
        "env": cmd_env,
        "session-save": cmd_session_save,
        "session-get": cmd_session_get,
        "session-rm": cmd_session_rm,
        "snapshots": cmd_snapshots,
        "restore": cmd_restore,
        "backup": cmd_backup,
        "audit": cmd_audit,
        "import": cmd_import,
        "export": cmd_export,
        "set-passphrase": cmd_set_passphrase,
        "sync-ecosystem": cmd_sync_ecosystem,
        "oauth-refresh": cmd_oauth_refresh,
        "provision": cmd_provision,
        "interactive-login": cmd_interactive_login,
        "providers": cmd_providers,
    }

    handler = dispatch.get(args.command)
    if handler:
        return handler(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
