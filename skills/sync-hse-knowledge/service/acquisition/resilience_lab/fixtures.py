"""Resilience Lab Test Fixtures and Scenarios (Section 18.3)."""

from typing import Dict, Any


SCENARIO_FIXTURES: Dict[str, Dict[str, Any]] = {
    "normal_200": {
        "status_code": 200,
        "headers": {"content-type": "text/html; charset=utf-8"},
        "body": "<html><body><h1>Luật An toàn vệ sinh lao động 84/2015/QH13</h1><p>Quy định chi tiết...</p></body></html>"
    },
    "not_modified_304": {
        "status_code": 304,
        "headers": {"etag": "\"33a64df551425fcc3\""},
        "body": ""
    },
    "rate_limit_429": {
        "status_code": 429,
        "headers": {"retry-after": "2", "content-type": "application/json"},
        "body": "{\"error\": \"Too many requests\"}"
    },
    "server_error_503": {
        "status_code": 503,
        "headers": {"content-type": "text/plain"},
        "body": "Service Unavailable - Cổng pháp luật đang bảo trì"
    },
    "cloudflare_turnstile": {
        "status_code": 403,
        "headers": {"server": "cloudflare", "content-type": "text/html"},
        "body": "<html><head><script src=\"https://challenges.cloudflare.com/turnstile/v0/api.js\"></script></head><body><div class=\"cf-turnstile\"></div></body></html>"
    },
    "js_rendering_required": {
        "status_code": 200,
        "headers": {"content-type": "text/html"},
        "body": "<!DOCTYPE html><html><body><div id=\"root\"></div><script src=\"/bundle.js\"></script></body></html>"
    }
}
