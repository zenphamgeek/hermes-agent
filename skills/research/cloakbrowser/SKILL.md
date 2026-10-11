---
name: cloakbrowser
description: Stealth Chromium for bot detection and Cloudflare bypass.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
  - linux
  - macos
metadata:
  tags:
    - browser
    - stealth
    - anti-bot
    - scraping
    - cloudflare
    - automation
  hermes:
    tags:
      - browser
      - stealth
      - anti-bot
      - scraping
      - cloudflare
      - automation
    related_skills:
      - blocked-page-recovery
      - website-mirror
      - electron-ide-cdp-automation
---

# CloakBrowser Skill

Operate a stealth Chromium distribution patched at the C++ source level
(73 patches) to pass bot-detection frameworks (Cloudflare Turnstile, DataDome,
FingerprintJS, CreepJS, Kasada) with humanized interaction patterns and CDP
multiplexing.

## When to Use

- Accessing websites guarded by Cloudflare Turnstile, Cloudflare Challenge,
  DataDome, or Akamai where standard HTTP requests or basic headless browsers
  fail with 403 Forbidden or captcha interstitials.
- Extracting clean DOM, markdown, or high-fidelity screenshots from
  bot-protected web applications.
- Running persistent or multiplexed CDP browser sessions through `cloakserve`
  bridged to native Hermes browser tools.
- Automating web flows requiring human-like mouse movements, variable typing
  cadence, and natural scroll momentum.

Do NOT use for:
- Standard public web APIs or static pages that load cleanly with standard
  HTTP clients.
- Bulk scraping of thousands of pages where lightweight requests or public
  feeds suffice.

## How to Run

Invoke the bundled CLI runner using the `terminal` tool:

```bash
# Verify environment and stealth binary
python3 skills/research/cloakbrowser/scripts/cloak_runner.py doctor

# Fetch protected page content as clean text or markdown
python3 skills/research/cloakbrowser/scripts/cloak_runner.py fetch "https://example.com" --format markdown

# Capture full-page screenshot of protected page
python3 skills/research/cloakbrowser/scripts/cloak_runner.py screenshot "https://example.com" --out /tmp/page.png

# Extract structured elements via CSS selector
python3 skills/research/cloakbrowser/scripts/cloak_runner.py extract "https://example.com" --selector "article" --json

# Start CDP multiplexer for native Hermes browser connection
python3 skills/research/cloakbrowser/scripts/cloak_runner.py serve --port 9222
```

## Quick Reference

| Task | Command |
|---|---|
| Health Check | `python3 skills/research/cloakbrowser/scripts/cloak_runner.py doctor` |
| Text/Markdown Fetch | `python3 skills/research/cloakbrowser/scripts/cloak_runner.py fetch <URL> [--format text\|markdown\|html]` |
| Full-Page Screenshot | `python3 skills/research/cloakbrowser/scripts/cloak_runner.py screenshot <URL> --out <PATH> [--full-page]` |
| CSS Extraction | `python3 skills/research/cloakbrowser/scripts/cloak_runner.py extract <URL> --selector <CSS> [--json]` |
| JS Evaluation | `python3 skills/research/cloakbrowser/scripts/cloak_runner.py eval <URL> --code <JS>` |
| CDP Bridge Server | `python3 skills/research/cloakbrowser/scripts/cloak_runner.py serve [--port 9222]` |
| Native Agent Env | `eval $(python3 skills/research/cloakbrowser/scripts/cloak_runner.py agent-browser-env)` |

## Procedure

### 1. Check environment and stealth binary

Run the self-diagnostic check to verify that `cloakbrowser` is available
and that the stealth Chromium binary is installed on the host.

```bash
python3 skills/research/cloakbrowser/scripts/cloak_runner.py doctor
```

If the binary is missing, `doctor` automatically downloads and configures
the matching patched Chromium binary.

Done when the command outputs JSON indicating `ready: true` and the binary path is verified.

### 2. Choose operating mode

Select the appropriate mode for the task:

- **Direct Extraction (One-shot)**: Use `fetch`, `extract`, or `screenshot` for
  retrieving content directly without managing persistent sessions.
- **Native Browser Tool Bridge (Interactive)**: Start the CDP daemon using
  `serve`, then point Hermes native browser tools to `http://localhost:9222?fingerprint=<seed>&humanize=true`.
- **Custom Playwright Script**: Write a focused Python automation script importing
  `from cloakbrowser import launch` for complex multi-step workflows.

Done when the execution route matches the target site's interaction requirements.

### 3. Execute stealth navigation and bypass

For one-shot content recovery:

```bash
python3 skills/research/cloakbrowser/scripts/cloak_runner.py fetch "https://target-site.com" \
  --format markdown \
  --wait-selector "main, article, #content" \
  --timeout 30 \
  --humanize
```

The runner automatically navigates with stealth arguments, waits for Cloudflare
Turnstile or security interstitials to settle, and extracts the target content.

Done when the target content is returned without captcha or 403 blocks.

### 4. Extract structured content or screenshot

Save structured data or visual proof as requested:

- For structured DOM nodes: use `extract --selector "..." --json`.
- For visual evidence: use `screenshot --out <output_path> --full-page`.

Done when the extracted artifacts are saved to the target location and non-empty.

## Pitfalls

- **Viewport Mismatch**: Passing a custom viewport size can cause detectable canvas
  fingerprint anomalies. Use default viewport or pass `--humanize` to let the
  stealth engine align window metrics.
- **Aggressive Timeouts**: Cloudflare Turnstile challenges typically take 3 to 7
  seconds to complete autonomous verification. Set `--timeout` to at least 30 seconds
  when accessing heavily guarded endpoints.
- **Proxy Consistency**: If routing through a residential or datacenter proxy,
  always pass `--timezone` or use `--geoip` to match the browser's reported timezone
  and locale to the proxy egress IP.
- **Process Cleanup**: The runner terminates browser processes cleanly on exit.
  When using `serve`, terminate the daemon when the session finishes.

## Verification

1. Run diagnostic:
   ```bash
   python3 skills/research/cloakbrowser/scripts/cloak_runner.py doctor
   ```
2. Verify stealth bot detection bypass on a public test page:
   ```bash
   python3 skills/research/cloakbrowser/scripts/cloak_runner.py eval "https://bot.sannysoft.com" \
     --code "JSON.stringify({webdriver: navigator.webdriver, plugins: navigator.plugins.length})"
   ```
   Ensure `webdriver` returns `false` (or `undefined`) and plugins length is greater than 0.

## References

- [CloakBrowser API Reference](references/api_reference.md)
- [CDP Integration & Multiplexing](references/cdp_integration.md)
