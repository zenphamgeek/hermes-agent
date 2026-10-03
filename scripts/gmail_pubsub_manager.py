#!/usr/bin/env python3
"""
Hermes Agent - Native Gmail Pub/Sub Watcher & Realtime Subscriber Daemon.

Workflow:
  1. `python scripts/gmail_pubsub_manager.py --setup-watch`
     - Authenticates with Google OAuth2 for `inteligentsilos@gmail.com`
     - Calls `gmail.users().watch()` to bind INBOX to `projects/project-3e385278-cd08-450e-ba0/topics/gmail-notifications`
  2. `python scripts/gmail_pubsub_manager.py --listen`
     - Runs daemon subscribing to `projects/project-3e385278-cd08-450e-ba0/subscriptions/gmail-notifications-sub`
     - Real-time Email arrival -> Fetch Email Content -> Gemini AI Summary -> Telegram Alert -> Downstream API Feed.
"""

import os
import sys
import json
import time
import base64
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Hermes webhook route — replaces fake-AI EventBusPipeline

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/pubsub"
]

HERMES_DIR = Path.home() / ".hermes"
CLIENT_SECRET_FILE = HERMES_DIR / "gmail_client_secret.json"
TOKEN_FILE = HERMES_DIR / "gmail_token.json"
PROJECT_ID = "project-3e385278-cd08-450e-ba0"
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/gmail-notifications"
SUBSCRIPTION_NAME = f"projects/{PROJECT_ID}/subscriptions/gmail-notifications-sub"


def get_gmail_credentials() -> Optional[Credentials]:
    """Loads or refreshes Gmail OAuth2 credentials."""
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"[Auth] Could not load token file: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
                print("🔄 [Auth] Gmail token refreshed successfully.")
            except Exception as e:
                print(f"[Auth] Token refresh failed: {e}")
                creds = None
        else:
            if not CLIENT_SECRET_FILE.exists():
                print(f"❌ [Auth] Missing {CLIENT_SECRET_FILE}. Please download client secret first.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            print(f"✅ [Auth] New Gmail token saved to {TOKEN_FILE}")

    return creds


def setup_gmail_watch():
    """Binds Gmail INBOX push notifications to Google Cloud Pub/Sub Topic."""
    print("=" * 70)
    print("⚡ [Gmail Watch] Registering Gmail Push Notifications to Cloud Pub/Sub...")
    print("=" * 70)

    creds = get_gmail_credentials()
    if not creds:
        print("❌ [Gmail Watch] Failed to obtain Gmail credentials.")
        return False

    service = build("gmail", "v1", credentials=creds)

    watch_request = {
        "topicName": TOPIC_NAME,
        "labelIds": ["INBOX"]
    }

    try:
        watch_response = service.users().watch(userId="me", body=watch_request).execute()
        history_id = watch_response.get("historyId")
        expiration = watch_response.get("expiration")
        exp_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(expiration) / 1000))

        print("🎉 [Gmail Watch] SUCCESS! Gmail INBOX is now watching and publishing to:")
        print(f"   • Topic: {TOPIC_NAME}")
        print(f"   • Initial History ID: {history_id}")
        print(f"   • Expiration Date: {exp_time_str}")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"❌ [Gmail Watch] Error registering watch: {e}")
        return False


def get_latest_email_content(service) -> Dict[str, Any]:
    """Fetches the latest email message from Gmail INBOX."""
    try:
        results = service.users().messages().list(userId="me", maxResults=1, labelIds=["INBOX"]).execute()
        messages = results.get("messages", [])
        if not messages:
            return {}

        msg_id = messages[0]["id"]
        msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()

        headers = msg.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
        snippet = msg.get("snippet", "")

        # Try to extract plain body text
        body = snippet
        parts = msg.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break

        return {
            "id": msg_id,
            "sender": sender,
            "subject": subject,
            "body": body,
            "snippet": snippet,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"[Gmail] Error fetching message: {e}")
        return {}


def _pubsub_pull_rest(creds, max_messages: int = 5) -> list:
    """Pulls messages from Pub/Sub subscription using REST API with OAuth credentials."""
    import urllib.request
    import urllib.error
    if creds.expired:
        creds.refresh(Request())

    url = f"https://pubsub.googleapis.com/v1/{SUBSCRIPTION_NAME}:pull"
    payload = json.dumps({"maxMessages": max_messages, "returnImmediately": True}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            msgs = result.get("receivedMessages", [])
            if msgs:
                print(f"[Pub/Sub REST Pull] Got {len(msgs)} message(s)!")
            return msgs
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[Pub/Sub REST Pull] HTTP {e.code}: {body[:300]}")
        return []
    except Exception as e:
        # Timeout on empty queue is normal with returnImmediately=false
        if "timed out" in str(e).lower():
            return []
        print(f"[Pub/Sub REST Pull] Error: {e}")
        print(f"[Pub/Sub REST Pull] Error: {e}")
        return []


def _pubsub_ack_rest(creds, ack_ids: list):
    """Acknowledges messages via REST API."""
    import urllib.request
    if not ack_ids:
        return
    if creds.expired:
        creds.refresh(Request())

    url = f"https://pubsub.googleapis.com/v1/{SUBSCRIPTION_NAME}:acknowledge"
    payload = json.dumps({"ackIds": ack_ids}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    except Exception as e:
        print(f"[Pub/Sub REST Ack] Error: {e}")


def _forward_to_webhook(raw_data_b64: str, msg_id: str, subscription: str) -> bool:
    """Forward raw Pub/Sub message to Hermes webhook route (like GCP push)."""
    import hashlib, hmac, urllib.request, urllib.error
    webhook_url = os.environ.get("WEBHOOK_FORWARD_URL", "http://127.0.0.1:8644/webhooks/email-inbound")
    # Read route secret from webhook_subscriptions.json
    secret = ""
    try:
        subs_path = Path.home() / ".hermes" / "webhook_subscriptions.json"
        if subs_path.exists():
            subs = json.loads(subs_path.read_text())
            secret = subs.get("email-inbound", {}).get("secret", "")
    except Exception:
        pass
    if not secret:
        secret = os.environ.get("WEBHOOK_SECRET", "")
    # Build push payload: {message: {data, messageId}, subscription}
    push_payload = {
        "message": {"data": raw_data_b64, "messageId": msg_id},
        "subscription": subscription or SUBSCRIPTION_NAME,
    }
    body = json.dumps(push_payload, ensure_ascii=False).encode("utf-8")
    # HMAC V2: timestamp.body
    ts = str(int(time.time()))
    signed_content = ts.encode() + b"." + body
    sig = hmac.new(secret.encode(), signed_content, hashlib.sha256).hexdigest()
    req = urllib.request.Request(
        webhook_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature-V2": sig,
            "X-Webhook-Timestamp": ts,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            status = result.get("status", "?")
            print(f"   → Webhook: {status} (delivery={result.get('delivery_id', '?')})")
            return True
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")[:200]
        print(f"   → Webhook HTTP {e.code}: {body_err}")
        return False
    except Exception as e:
        print(f"   → Webhook error: {e}")
        return False


def start_pubsub_listener():
    """Poll Pub/Sub → forward to Hermes webhook route (replaces fake-AI pipeline)."""
    print("=" * 70)
    print(f"🎧 [Hermes Pub/Sub Daemon] Forwarding to webhook: {SUBSCRIPTION_NAME}")
    print("   Pull → POST to Hermes webhook route (agent processes email + Odoo + Telegram)")
    print("   Press Ctrl+C to stop.")
    print("=" * 70)

    creds = get_gmail_credentials()
    if not creds:
        print("❌ [Pub/Sub Daemon] Cannot start without Gmail credentials.")
        return

    poll_interval = 5
    print(f"   Polling every {poll_interval}s...")

    try:
        while True:
            messages = _pubsub_pull_rest(creds, max_messages=10)
            if messages:
                ack_ids = []
                for received in messages:
                    msg = received.get("message", {})
                    msg_id = msg.get("messageId", "?")
                    raw_data_b64 = msg.get("data", "")
                    ack_id = received.get("ackId")
                    sub = received.get("subscription", "")

                    print(f"\n📩 [Pub/Sub] Message ID: {msg_id}")
                    _forward_to_webhook(raw_data_b64, msg_id, sub)

                    if ack_id:
                        ack_ids.append(ack_id)

                _pubsub_ack_rest(creds, ack_ids)
                print(f"✅ [Pub/Sub] {len(ack_ids)} message(s) acknowledged.")

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n🛑 [Pub/Sub Daemon] Stopped.")


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent Native Gmail Pub/Sub Manager")
    parser.add_argument("--setup-watch", action="store_true", help="Authenticate and register Gmail watch() with Cloud Pub/Sub")
    parser.add_argument("--listen", action="store_true", help="Start background subscriber daemon")
    parser.add_argument("--status", action="store_true", help="Check current watch and credentials status")
    args = parser.parse_args()

    if args.setup_watch:
        setup_gmail_watch()
    elif args.listen:
        start_pubsub_listener()
    else:
        print("Hermes Gmail Pub/Sub Manager")
        print(f"Token file: {TOKEN_FILE} (Exists: {TOKEN_FILE.exists()})")
        print(f"Client secret: {CLIENT_SECRET_FILE} (Exists: {CLIENT_SECRET_FILE.exists()})")
        print(f"Topic: {TOPIC_NAME}")
        print(f"Subscription: {SUBSCRIPTION_NAME}")
        print("\nRun with --setup-watch to activate Gmail watch, or --listen to start daemon.")


if __name__ == "__main__":
    main()
