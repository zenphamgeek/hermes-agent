#!/usr/bin/env python3
"""
Hermes Agent — Odoo ERP Envelope POST.

Reads JSON envelope from stdin, POSTs to Odoo ingest endpoint with HMAC + API key.

Usage:
  echo '<envelope_json>' | python3 post_odoo.py

Returns the Odoo response as JSON on stdout.
Exit code 0 on success, 1 on failure.
"""

import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request

ODOO_ENDPOINT = os.environ.get(
    "ODOO_ENDPOINT",
    "http://10.123.214.220:8069/api/v1/pubsub/ingest",
)
ERP_API_KEY = os.environ.get(
    "ERP_API_KEY",
    "insilos_sec_key_2026_pubsub",
)
WEBHOOK_SECRET = os.environ.get(
    "WEBHOOK_SECRET",
    "",
)


def compute_hmac(body: str, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest."""
    return "sha256=" + hmac.new(
        secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()


def main():
    raw_body = sys.stdin.read()
    if not raw_body.strip():
        print(json.dumps({"status": "error", "message": "Empty input"}))
        sys.exit(1)

    # Validate JSON
    try:
        envelope = json.loads(raw_body)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)

    # Validate required fields
    required = ["event_id", "event_type", "payload"]
    missing = [f for f in required if f not in envelope]
    if missing:
        print(
            json.dumps(
                {"status": "error", "message": f"Missing fields: {missing}"}
            )
        )
        sys.exit(1)

    # Compute HMAC
    hmac_sig = compute_hmac(raw_body, WEBHOOK_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-ERP-API-Key": ERP_API_KEY,
        "X-Hermes-Signature": hmac_sig,
    }

    req = urllib.request.Request(
        ODOO_ENDPOINT,
        data=raw_body.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_response = resp.read().decode("utf-8")
            result = json.loads(raw_response)
            result["_http_status"] = resp.status
            print(json.dumps(result, ensure_ascii=False))
            if result.get("status") == "success":
                sys.exit(0)
            sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        print(
            json.dumps(
                {
                    "status": "error",
                    "http_status": e.code,
                    "message": str(e),
                    "body": body,
                }
            )
        )
        sys.exit(1)
    except Exception as e:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": str(e)[:300],
                }
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
