"""Offline test doubles and fixtures for resilience testing."""

from typing import Dict, Tuple

CHALLENGE_FIXTURE = """
<!DOCTYPE html>
<html>
<head><title>Just a moment...</title></head>
<body>
<div class="cf-turnstile" data-sitekey="1x00000000000000000000AA"></div>
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
<p>Checking if the site connection is secure. DDoS protection by Cloudflare.</p>
</body>
</html>
"""

RATE_LIMIT_FIXTURE = """
{"error": "Too Many Requests", "retry_after": 2}
"""

SERVER_ERROR_FIXTURE = """
{"error": "Internal Server Error"}
"""

SUCCESS_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head><title>Biểu thuế XNK 2026</title></head>
<body>
<h1>Biểu thuế xuất nhập khẩu Việt Nam</h1>
<table>
  <tr><th>Mã HS</th><th>Mô tả</th><th>Thuế suất</th></tr>
  <tr><td>8471.30.20</td><td>Máy tính xách tay</td><td>0%</td></tr>
</table>
</body>
</html>
"""

def get_fixture_response(scenario: str) -> Tuple[int, Dict[str, str], str]:
    if scenario == "challenge":
        return (403, {"cf-mitigated": "challenge", "content-type": "text/html"}, CHALLENGE_FIXTURE)
    elif scenario == "rate_limit":
        return (429, {"retry-after": "1", "content-type": "application/json"}, RATE_LIMIT_FIXTURE)
    elif scenario == "server_error":
        return (503, {"content-type": "application/json"}, SERVER_ERROR_FIXTURE)
    elif scenario == "not_modified":
        return (304, {"etag": '"abc123"'}, "")
    elif scenario == "success":
        return (200, {"content-type": "text/html; charset=utf-8"}, SUCCESS_HTML_FIXTURE)
    else:
        return (404, {}, "Not Found")
