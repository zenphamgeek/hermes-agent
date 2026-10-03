#!/usr/bin/env python3
"""
scripts/manage_modal_tokens.py
==============================
Hermes Agent - Modal Token Auto-Parser & Multi-Group Manager.

Features:
- Smart parser for raw modal CLI commands, TOML blocks, key-value pairs, or free text
- Groups tokens by managing Email account (e.g. just.ask.mr.zen@gmail.com, nhatrophamvu@gmail.com)
- Safely appends new tokens to modal_token_profile.md under the respective email section
- Optionally syncs/activates profiles into ~/.modal.toml
- Emits structured JSON for Dashboard UI consumption
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path("/home/zen/hermes-agent")
MD_PATH = WORKSPACE_ROOT / "modal_token_profile.md"
TOML_PATH = Path(os.path.expanduser("~/.modal.toml"))
OUTPUT_JSON = WORKSPACE_ROOT / "output" / "modal_fleet_status.json"

DEFAULT_EMAILS = [
    "just.ask.mr.zen@gmail.com",
    "nhatrophamvu@gmail.com",
    "mojopham@gmail.com",
    "zenonmind@gmail.com"
]


def parse_token_input(raw_text: str, default_account: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Intelligently parses raw text into structured token entries.
    Supports:
    - CLI commands: modal token set --token-id ak-... --token-secret as-... --profile=...
    - TOML blocks: [profile] \\n token_id = "ak-..." \\n token_secret = "as-..."
    - Key-Value / Freeform text containing ak- and as- tokens
    """
    results = []
    current_email = default_account or DEFAULT_EMAILS[0]
    
    # Check if text contains an explicit email header or mention
    header_email_m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
    if header_email_m:
        current_email = header_email_m.group(0)

    # 1. Parse TOML sections: [profile_name] followed by token_id and token_secret
    toml_sections = re.findall(r"\[([A-Za-z0-9_-]+)\]\s*([^\[]+)", raw_text)
    if toml_sections:
        for prof, body in toml_sections:
            tid_m = re.search(r"\b(ak-[A-Za-z0-9_-]{10,})\b", body)
            tsec_m = re.search(r"\b(as-[A-Za-z0-9_-]{10,})\b", body)
            em_m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", body)
            if tid_m or tsec_m:
                results.append({
                    "account": em_m.group(0) if em_m else current_email,
                    "profile": prof,
                    "token_id": tid_m.group(1) if tid_m else None,
                    "token_secret": tsec_m.group(1) if tsec_m else None,
                    "format": "toml"
                })

    # 2. Parse CLI modal token set commands
    cmd_matches = re.finditer(r"modal\s+token\s+set[^\n]+", raw_text)
    for m in cmd_matches:
        line = m.group(0)
        tid = re.search(r"--token-id\s+([^\s]+)", line)
        tsec = re.search(r"--token-secret\s+([^\s]+)", line)
        prof = re.search(r"--profile=([^\s]+)", line)
        em_m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line)
        results.append({
            "account": em_m.group(0) if em_m else current_email,
            "profile": prof.group(1) if prof else "default",
            "token_id": tid.group(1) if tid else None,
            "token_secret": tsec.group(1) if tsec else None,
            "format": "modal_cli"
        })

    # 3. Fallback: Line-by-line or freeform regex pairing if no TOML or CLI commands matched
    if not results:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        for line in lines:
            tid_m = re.search(r"\b(ak-[A-Za-z0-9_-]{10,})\b", line)
            tsec_m = re.search(r"\b(as-[A-Za-z0-9_-]{10,})\b", line)
            em_m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line)
            prof_m = re.search(r"(?:profile|workspace)[:=]\s*([A-Za-z0-9_-]+)", line, re.I)
            
            if tid_m or tsec_m:
                results.append({
                    "account": em_m.group(0) if em_m else current_email,
                    "profile": prof_m.group(1) if prof_m else "default",
                    "token_id": tid_m.group(1) if tid_m else None,
                    "token_secret": tsec_m.group(1) if tsec_m else None,
                    "format": "freeform"
                })
                
    # 4. If still nothing matched, grab any ak- and as- in text
    if not results:
        tids = re.findall(r"\b(ak-[A-Za-z0-9_-]{10,})\b", raw_text)
        tsecs = re.findall(r"\b(as-[A-Za-z0-9_-]{10,})\b", raw_text)
        for i in range(max(len(tids), len(tsecs))):
            results.append({
                "account": current_email,
                "profile": f"profile_{i+1}",
                "token_id": tids[i] if i < len(tids) else None,
                "token_secret": tsecs[i] if i < len(tsecs) else None,
                "format": "raw_tokens"
            })
            
    return results


# Canonical 4 Groups of 5 Workspaces each (from Modal UI Screenshots)
CANONICAL_GROUPS = {
    "just.ask.mr.zen@gmail.com": [
        "just-ask-mr-zen", "zenpeace", "mindful", "zenmaster", "zenguru"
    ],
    "nhatrophamvu@gmail.com": [
        "nhatrophamvu", "asmr", "vi2vi", "pvvsf", "phi4"
    ],
    "mojopham@gmail.com": [
        "mojopham", "diatts", "mvlm", "motion", "vrag"
    ],
    "zenonmind@gmail.com": [
        "lovenovel", "vieturbo", "zenonmind", "insimind", "zenonts"
    ]
}


def load_grouped_tokens() -> Dict[str, List[Dict[str, Any]]]:
    """Loads all 20 workspaces grouped into the exact 4 Canonical Email Groups matching user screenshots."""
    import toml
    toml_data = {}
    if TOML_PATH.exists():
        try:
            with open(TOML_PATH) as f:
                toml_data = toml.load(f)
        except Exception:
            pass

    # Map of all known tokens across md and toml
    known_tokens = {
        # Group 1: just.ask.mr.zen@gmail.com
        "just-ask-mr-zen": {"token_id": "ak-L6SRQL5dssrHfxEXCMnCKw", "token_secret": "as-JSRbJxaeFilPuzgbDpprlN", "desc": "Account Personal Root"},
        "zenpeace": {"token_id": "ak-Gf6lhri7cwO6XJzLb2tV3o", "token_secret": "as-2hE3BGGApmVzNdyBoTJS0F", "desc": "Video SF / Model Endpoint"},
        "mindful": {"token_id": "ak-SEEtXauFsj0MPEoJl6qieV", "token_secret": "as-KLn9qKhifaMvO11YqgDWlO", "desc": "Video SF / Model Endpoint"},
        "zenmaster": {"token_id": "ak-UKWM8dXrfr785aktfx0fzB", "token_secret": None, "desc": "Video API / Waiting Secret"},
        "zenguru": {"token_id": "ak-gVxxmKrYoGNv1xkNkZw5vS", "token_secret": "as-pirwCsw1APhhb7KeyVM2jG", "desc": "Video SF / Model Endpoint"},

        # Group 2: nhatrophamvu@gmail.com
        "nhatrophamvu": {"token_id": "ak-jJQAEzy5HZqosu3xwyYt2g", "token_secret": "as-d0CUiq0DUTWhyUSVRMH3wY", "desc": "Account Personal Root"},
        "asmr": {"token_id": "ak-s00pn3deyU0MuAnehcCAmM", "token_secret": "as-e6F7TPJdDClxU7Xo1vjkDr", "desc": "Audio ASMR / Image SF"},
        "vi2vi": {"token_id": "ak-otWpKBHY3SmdjJLcil1Nbf", "token_secret": "as-NqNvIirc2qR6DncT2738US", "desc": "SwapFace / Image SF"},
        "pvvsf": {"token_id": "ak-hGi0Z650fPEpcExNvk5lOP", "token_secret": "as-AaLlkm87lxwqggBYxX751q", "desc": "SwapFace Production"},
        "phi4": {"token_id": "ak-21afbBX503EFP6CPAuTOux", "token_secret": "as-9J85ce4Fd1ihkj0weRhGAm", "desc": "Phi4 Model Endpoint"},

        # Group 3: mojopham@gmail.com
        "mojopham": {"token_id": "ak-5jZWdzpMPhsJmbHCYxakOF", "token_secret": "as-L3Wf3mYOy2v4XmiyigbY2u", "desc": "Enterprise OCR & Serve"},
        "diatts": {"token_id": "ak-5JPSYDtrvZHK03KbgiuZjo", "token_secret": "as-lx1qx8UQEH9TwLx5lRKN0q", "desc": "Dialogue TTS / SwapFace"},
        "mvlm": {"token_id": "ak-P6hw0mpmgjXVR3LdbdSptc", "token_secret": "as-3SdtvKkaFLLbPCXbwSO3KE", "desc": "Multimodal Vision VLM"},
        "motion": {"token_id": "ak-jloGdXl26829Nu4ppzWPZT", "token_secret": "as-uFSOqVpyzLt8554b960wqx", "desc": "Motion Geometry / SwapFace"},
        "vrag": {"token_id": "ak-UjdguKfy9ud6GaHgUrz36m", "token_secret": "as-dCMyS7lM8lDjNux7xZ13CI", "desc": "Video RAG / SwapFace"},

        # Group 4: zenonmind@gmail.com
        "lovenovel": {"token_id": None, "token_secret": None, "desc": "LoveNovel Video / Story Model"},
        "vieturbo": {"token_id": None, "token_secret": None, "desc": "VieTurbo Fast Inference"},
        "zenonmind": {"token_id": None, "token_secret": None, "desc": "Account Personal Root"},
        "insimind": {"token_id": None, "token_secret": None, "desc": "InsiMind Intelligence Worker"},
        "zenonts": {"token_id": None, "token_secret": None, "desc": "Active in Screenshot ✓"},
    }

    result: Dict[str, List[Dict[str, Any]]] = {}

    for email, profiles in CANONICAL_GROUPS.items():
        result[email] = []
        for prof in profiles:
            entry = known_tokens.get(prof, {"token_id": None, "token_secret": None, "desc": "Modal Workspace"})
            
            # Check if active in TOML
            in_toml = False
            is_active = False
            tid = entry["token_id"]
            tsec = entry["token_secret"]
            
            if prof in toml_data:
                in_toml = True
                is_active = toml_data[prof].get("active", False)
                # If TOML has different active key, use toml key
                if toml_data[prof].get("token_id"):
                    tid = toml_data[prof].get("token_id")
                if toml_data[prof].get("token_secret"):
                    tsec = toml_data[prof].get("token_secret")

            result[email].append({
                "profile": prof,
                "token_id": tid,
                "token_secret": tsec,
                "desc": entry.get("desc", ""),
                "in_toml": in_toml,
                "is_active_fleet": is_active
            })

    return result


def append_token_to_md(account: str, profile: str, token_id: str, token_secret: str) -> bool:
    """Appends a new token command under the correct email section in modal_token_profile.md."""
    if not MD_PATH.exists():
        return False
        
    content = MD_PATH.read_text()
    
    cmd = f"modal token set --token-id {token_id} --token-secret {token_secret}"
    if profile and profile != "default":
        cmd += f" --profile={profile}"
        
    # Check if this exact token already exists
    if token_id in content:
        print(f"[*] Token {token_id} already exists in {MD_PATH.name}")
        return True
        
    # Find matching account header
    account_pattern = re.compile(rf"(#\s*[-]+\s*{re.escape(account)}[^\n]*)", re.IGNORECASE)
    match = account_pattern.search(content)
    
    if match:
        insert_pos = match.end()
        new_content = content[:insert_pos] + f"\n\n{cmd}\n" + content[insert_pos:]
    else:
        # Create new email section at bottom
        new_section = f"\n\n# ---- {account}\tpro\t\n{cmd}\n"
        new_content = content + new_section
        
    MD_PATH.write_text(new_content)
    print(f"[✓] Successfully appended token {token_id} for profile '{profile}' under '{account}' in {MD_PATH.name}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modal Token Multi-Group Manager")
    parser.add_argument("--parse", type=str, help="Raw string to parse")
    parser.add_argument("--account", type=str, default="nhatrophamvu@gmail.com", help="Email group to assign")
    parser.add_argument("--list-grouped", action="store_true", help="List tokens grouped by email account (JSON)")
    parser.add_argument("--add", nargs=4, metavar=("ACCOUNT", "PROFILE", "TOKEN_ID", "TOKEN_SECRET"), help="Add a new token entry")
    
    args = parser.parse_args()
    
    if args.list_grouped:
        grouped = load_grouped_tokens()
        print(json.dumps(grouped, indent=2))
    elif args.parse:
        res = parse_token_input(args.parse, default_account=args.account)
        print(json.dumps(res, indent=2))
    elif args.add:
        acc, prof, tid, tsec = args.add
        append_token_to_md(acc, prof, tid, tsec)
    else:
        parser.print_help()
