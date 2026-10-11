#!/usr/bin/env python3
"""
Hermes Agent — Gmail Email Fetcher for Webhook Route Script.

Reads GCP Pub/Sub push payload from stdin (JSON with message.data base64),
decodes historyId, fetches actual email content from Gmail API.

Outputs enriched JSON: sender, subject, body, attachments, metadata.

Webhook route script: runs PRE-agent, enriches push payload.
"""

import json
import os
import sys
import base64
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
HERMES_DIR = Path.home() / ".hermes"
TOKEN_FILE = HERMES_DIR / "gmail_token.json"
CLIENT_SECRET_FILE = HERMES_DIR / "gmail_client_secret.json"
ATTACHMENTS_DIR = HERMES_DIR / "data" / "email-attachments"
MAX_MESSAGES = 5


def get_gmail_credentials() -> Optional[Credentials]:
    """Load Gmail OAuth credentials. Returns None if unavailable."""
    if not TOKEN_FILE.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    except Exception:
        return None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
            except Exception:
                return None
        else:
            return None
    return creds


def decode_push_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Decode GCP Pub/Sub push message.data (base64)."""
    msg = payload.get("message", {})
    raw_data = msg.get("data", "")
    gcp_message_id = msg.get("messageId", "")
    publish_time = msg.get("publishTime", "")

    if not raw_data:
        return {"emailAddress": "", "historyId": "", "gcp_message_id": gcp_message_id}

    try:
        decoded = base64.b64decode(raw_data).decode("utf-8")
        data = json.loads(decoded)
    except Exception:
        data = {"_raw_data": raw_data}

    data["gcp_message_id"] = gcp_message_id
    data["publish_time"] = publish_time
    data["subscription"] = payload.get("subscription", "")
    return data


def fetch_email_by_id(service, msg_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single email by Gmail message ID."""
    try:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
    except Exception:
        return None

    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

    sender = headers.get("from", "Unknown")
    subject = headers.get("subject", "(No Subject)")
    date_str = headers.get("date", "")
    message_id = headers.get("message-id", msg_id)

    # Extract body
    body = msg.get("snippet", "")
    parts = msg.get("payload", {}).get("parts", [])
    if not parts:
        mime = msg.get("payload", {}).get("mimeType", "")
        if mime == "text/plain":
            data = msg.get("payload", {}).get("body", {}).get("data", "")
            if data:
                try:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                except Exception:
                    body = msg.get("snippet", "")
    else:
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    try:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    except Exception:
                        pass
                    break

    # Attachments
    attachments = []
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    for part in parts:
        filename = part.get("filename", "")
        if not filename:
            continue
        body_data = part.get("body", {})
        data = body_data.get("data", "")
        att_id = body_data.get("attachmentId", "")
        size = body_data.get("size", 0)
        if not data and att_id:
            try:
                att = (
                    service.users()
                    .messages()
                    .attachments()
                    .get(userId="me", messageId=msg_id, id=att_id)
                    .execute()
                )
                data = att.get("data", "")
            except Exception:
                pass
        if data:
            file_path = ATTACHMENTS_DIR / f"{msg_id}_{filename}"
            try:
                raw_bytes = base64.urlsafe_b64decode(data)
                file_path.write_bytes(raw_bytes)
            except Exception:
                file_path = None
        else:
            file_path = None
        attachments.append({
            "file_name": filename,
            "size_bytes": size,
            "mime_type": part.get("mimeType", ""),
            "path": str(file_path) if file_path else "",
        })

    return {
        "id": msg_id,
        "message_id": message_id,
        "sender": sender,
        "subject": subject,
        "body": body,
        "date": date_str,
        "attachments": attachments,
    }


def fetch_history_messages(service, history_id: str) -> List[Dict[str, Any]]:
    """Fetch messages from Gmail history since given historyId."""
    try:
        history = (
            service.users()
            .history()
            .list(userId="me", startHistoryId=history_id, maxResults=10)
            .execute()
        )
    except Exception:
        return []

    messages = []
    seen_ids = set()
    for record in history.get("history", []):
        for msg_added in record.get("messagesAdded", []):
            msg = msg_added.get("message", {})
            msg_id = msg.get("id", "")
            if msg_id and msg_id not in seen_ids:
                seen_ids.add(msg_id)
                email_data = fetch_email_by_id(service, msg_id)
                if email_data:
                    messages.append(email_data)
                if len(messages) >= MAX_MESSAGES:
                    return messages
    return messages


def main():
    payload = json.loads(sys.stdin.read())

    # Decode push data
    push_data = decode_push_data(payload)
    history_id = push_data.get("historyId", "")
    gcp_msg_id = push_data.get("gcp_message_id", "")
    email_address = push_data.get("emailAddress", "inteligentsilos@gmail.com")

    # Get credentials
    creds = get_gmail_credentials()
    if not creds:
        # No Gmail credentials — pass through with available info
        output = {
            "source": "gmail.pubsub",
            "email_address": email_address,
            "history_id": history_id,
            "gcp_message_id": gcp_msg_id,
            "messages": [],
            "error": "No Gmail credentials available",
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(0)

    service = build("gmail", "v1", credentials=creds)

    if history_id:
        messages = fetch_history_messages(service, history_id)
    else:
        # Fallback: fetch latest INBOX message
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=1, labelIds=["INBOX"])
            .execute()
        )
        msg_list = results.get("messages", [])
        messages = []
        for m in msg_list[:1]:
            email_data = fetch_email_by_id(service, m["id"])
            if email_data:
                messages.append(email_data)

    output = {
        "source": "gmail.pubsub",
        "email_address": email_address,
        "history_id": history_id,
        "gcp_message_id": gcp_msg_id,
        "messages": messages,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
