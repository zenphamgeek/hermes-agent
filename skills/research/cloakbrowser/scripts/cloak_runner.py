#!/usr/bin/env python3
"""CLI runner for CloakBrowser stealth automation.

Provides command-line primitives for:
  - doctor: diagnostic check for CloakBrowser installation and stealth binary
  - fetch: retrieve clean page text, markdown, or HTML from bot-protected pages
  - screenshot: capture high-fidelity full-page screenshots
  - extract: extract structured text or attributes via CSS selectors
  - eval: execute JS expressions within a stealth browser session
  - serve: launch CDP multiplexer daemon (cloakserve)
  - agent-browser-env: print shell export commands for Hermes agent-browser

Exit codes:
  0: Operation succeeded
  1: Execution error / failure
  2: Invalid arguments
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Silence non-fatal environment warnings for clean CLI output
os.environ.setdefault("CLOAKBROWSER_SUPPRESS_FONT_WARNING", "1")


def _html_to_markdown(html_content: str) -> str:
    """Lightweight clean converter from HTML to readable markdown."""
    text = html_content
    # Remove scripts, styles, comments
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", "", text)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", "", text)
    text = re.sub(r"(?is)<!--.*?-->", "", text)
    text = re.sub(r"(?is)<svg[^>]*>.*?</svg>", "", text)

    # Convert headings
    text = re.sub(r"(?i)<h1[^>]*>(.*?)</h1>", r"\n# \1\n", text)
    text = re.sub(r"(?i)<h2[^>]*>(.*?)</h2>", r"\n## \1\n", text)
    text = re.sub(r"(?i)<h3[^>]*>(.*?)</h3>", r"\n### \1\n", text)
    text = re.sub(r"(?i)<h[4-6][^>]*>(.*?)</h[4-6]>", r"\n#### \1\n", text)

    # Convert links and formatting
    text = re.sub(r'(?i)<a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', r"[\2](\1)", text)
    text = re.sub(r"(?i)<strong[^>]*>(.*?)</strong>", r"**\1**", text)
    text = re.sub(r"(?i)<b[^>]*>(.*?)</b>", r"**\1**", text)
    text = re.sub(r"(?i)<em[^>]*>(.*?)</em>", r"*\1*", text)
    text = re.sub(r"(?i)<i[^>]*>(.*?)</i>", r"*\1*", text)
    text = re.sub(r"(?i)<code[^>]*>(.*?)</code>", r"`\1`", text)

    # Paragraphs and line breaks
    text = re.sub(r"(?i)<li[^>]*>(.*?)</li>", r"\n- \1", text)
    text = re.sub(r"(?i)<p[^>]*>(.*?)</p>", r"\n\n\1\n\n", text)
    text = re.sub(r"(?i)<br\s*/?>", r"\n", text)
    text = re.sub(r"(?i)<hr\s*/?>", r"\n---\n", text)

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)

    # Normalize whitespace
    lines = [line.strip() for line in text.splitlines()]
    compact: List[str] = []
    blank = False
    for line in lines:
        if line:
            compact.append(line)
            blank = False
        elif not blank:
            compact.append("")
            blank = True
    return "\n".join(compact).strip()


def run_doctor(args: argparse.Namespace) -> int:
    """Check CloakBrowser python package, binary installation, and launch."""
    result: Dict[str, Any] = {
        "ok": False,
        "package_installed": False,
        "binary_installed": False,
        "binary_path": None,
        "version": None,
        "tier": None,
        "stealth_launch_ok": False,
        "error": None,
    }

    try:
        import cloakbrowser  # noqa: F401
        from cloakbrowser.download import binary_info, ensure_binary

        result["package_installed"] = True
        info = binary_info()
        result["version"] = info.get("version")
        result["tier"] = info.get("tier")

        # Auto-download binary if not yet present
        bin_path = ensure_binary()
        result["binary_installed"] = bool(bin_path and Path(bin_path).is_file())
        result["binary_path"] = bin_path

        # Test launch
        from cloakbrowser import launch

        browser = launch(headless=True)
        page = browser.new_page()
        page.goto("data:text/html,<html><head><title>CloakOK</title></head><body>OK</body></html>")
        title = page.title()
        browser.close()

        if title == "CloakOK":
            result["stealth_launch_ok"] = True
            result["ok"] = True
        else:
            result["error"] = f"Unexpected launch title: {title}"

    except Exception as exc:
        result["error"] = str(exc)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status_symbol = "✓" if result["ok"] else "✗"
        print(f"[{status_symbol}] CloakBrowser Doctor Status:")
        print(f"  Package: {'Installed' if result['package_installed'] else 'Missing'}")
        print(f"  Binary:  {'Installed' if result['binary_installed'] else 'Missing'} ({result['binary_path']})")
        print(f"  Version: {result['version']} (Tier: {result['tier']})")
        print(f"  Launch:  {'Passed' if result['stealth_launch_ok'] else 'Failed'}")
        if result["error"]:
            print(f"  Error:   {result['error']}")

    return 0 if result["ok"] else 1


def run_fetch(args: argparse.Namespace) -> int:
    """Fetch URL and output content in requested format."""
    try:
        from cloakbrowser import launch

        browser = launch(
            headless=True,
            humanize=args.humanize,
            proxy=args.proxy,
            timezone=args.timezone,
            locale=args.locale,
        )
        page = browser.new_page()

        timeout_ms = int(args.timeout * 1000)
        page.goto(args.url, timeout=timeout_ms, wait_until="domcontentloaded")

        # Wait for challenges or specific selectors
        if args.wait_selector:
            page.wait_for_selector(args.wait_selector, timeout=timeout_ms)
        else:
            page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 10000))

        # Check for Cloudflare Turnstile iframes and allow short settle
        try:
            cf_frames = page.locator("iframe[src*='challenges.cloudflare.com']")
            if cf_frames.count() > 0:
                time.sleep(3.0)
        except Exception:
            pass

        content = page.content()
        title = page.title()
        browser.close()

        output_str: str
        if args.format == "html":
            output_str = content
        elif args.format == "markdown":
            output_str = f"# {title}\n\n" + _html_to_markdown(content)
        else:  # text
            output_str = _html_to_markdown(content)

        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output_str, encoding="utf-8")
            if not args.quiet:
                print(f"Saved {len(output_str)} bytes to {args.out}")
        else:
            print(output_str)

        return 0

    except Exception as exc:
        print(f"Error fetching {args.url}: {exc}", file=sys.stderr)
        return 1


def run_screenshot(args: argparse.Namespace) -> int:
    """Take screenshot of protected URL."""
    try:
        from cloakbrowser import launch

        browser = launch(
            headless=True,
            humanize=args.humanize,
            proxy=args.proxy,
            timezone=args.timezone,
            locale=args.locale,
        )
        page = browser.new_page()

        timeout_ms = int(args.timeout * 1000)
        page.goto(args.url, timeout=timeout_ms, wait_until="domcontentloaded")

        if args.wait_selector:
            page.wait_for_selector(args.wait_selector, timeout=timeout_ms)
        else:
            page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 10000))

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_path), full_page=args.full_page)
        browser.close()

        if not args.quiet:
            print(f"Screenshot saved to {args.out}")
        return 0

    except Exception as exc:
        print(f"Error taking screenshot of {args.url}: {exc}", file=sys.stderr)
        return 1


def run_extract(args: argparse.Namespace) -> int:
    """Extract structured CSS selector elements or attributes."""
    try:
        from cloakbrowser import launch

        browser = launch(headless=True, humanize=args.humanize, proxy=args.proxy)
        page = browser.new_page()

        timeout_ms = int(args.timeout * 1000)
        page.goto(args.url, timeout=timeout_ms, wait_until="domcontentloaded")
        page.wait_for_selector(args.selector, timeout=timeout_ms)

        locators = page.locator(args.selector)
        count = locators.count()
        results: List[Dict[str, Any]] = []

        for i in range(count):
            loc = locators.nth(i)
            if args.attribute:
                val = loc.get_attribute(args.attribute) or ""
            else:
                val = loc.inner_text().strip()
            results.append({"index": i, "value": val})

        browser.close()

        if args.json:
            print(json.dumps({"url": args.url, "selector": args.selector, "count": count, "matches": results}, indent=2))
        else:
            for item in results:
                print(f"[{item['index']}] {item['value']}")

        return 0

    except Exception as exc:
        print(f"Error extracting selector '{args.selector}' on {args.url}: {exc}", file=sys.stderr)
        return 1


def run_eval(args: argparse.Namespace) -> int:
    """Evaluate JavaScript within stealth browser session."""
    try:
        from cloakbrowser import launch

        browser = launch(headless=True, humanize=args.humanize, proxy=args.proxy)
        page = browser.new_page()

        timeout_ms = int(args.timeout * 1000)
        page.goto(args.url, timeout=timeout_ms, wait_until="domcontentloaded")
        eval_result = page.evaluate(args.code)
        browser.close()

        if isinstance(eval_result, (dict, list)):
            print(json.dumps(eval_result, indent=2))
        else:
            print(str(eval_result))

        return 0

    except Exception as exc:
        print(f"Error evaluating JS on {args.url}: {exc}", file=sys.stderr)
        return 1


def run_serve(args: argparse.Namespace) -> int:
    """Launch CDP multiplexer daemon (cloakserve)."""
    try:
        port = args.port
        print(f"Starting CloakBrowser CDP multiplexer on port {port}...")
        cmd = [sys.executable, "-m", "cloakbrowser.bin.cloakserve", f"--port={port}"]
        # Fallback to direct script if module invocation varies
        proc = subprocess.Popen(cmd)
        print(f"CDP multiplexer running with PID {proc.pid}")
        print(f"Connect via CDP: http://127.0.0.1:{port}?fingerprint=default")
        if args.wait:
            proc.wait()
        return 0
    except Exception as exc:
        print(f"Error starting CDP multiplexer: {exc}", file=sys.stderr)
        return 1


def run_agent_browser_env(args: argparse.Namespace) -> int:
    """Print export commands to route Hermes agent-browser through CloakBrowser."""
    try:
        from cloakbrowser.config import get_default_stealth_args
        from cloakbrowser.download import ensure_binary

        binary_path = ensure_binary()
        stealth_args = ",".join(get_default_stealth_args())

        print(f'export AGENT_BROWSER_EXECUTABLE_PATH="{binary_path}"')
        print(f'export AGENT_BROWSER_ARGS="{stealth_args}"')
        return 0
    except Exception as exc:
        print(f"Error generating agent-browser env: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CloakBrowser stealth automation CLI for Hermes Agent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Check installation & stealth binary health")
    p_doctor.add_argument("--json", action="store_true", help="Output diagnostic result as JSON")

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Retrieve protected page text/markdown/html")
    p_fetch.add_argument("url", help="Target URL")
    p_fetch.add_argument("--format", choices=["markdown", "text", "html"], default="markdown", help="Output format")
    p_fetch.add_argument("--wait-selector", help="CSS selector to await")
    p_fetch.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds")
    p_fetch.add_argument("--humanize", action="store_true", help="Enable human interaction patterns")
    p_fetch.add_argument("--proxy", help="Proxy URL or specification")
    p_fetch.add_argument("--timezone", help="IANA timezone")
    p_fetch.add_argument("--locale", help="BCP 47 locale")
    p_fetch.add_argument("--out", help="Save output to file")
    p_fetch.add_argument("--quiet", action="store_true", help="Suppress progress logs")

    # screenshot
    p_screenshot = subparsers.add_parser("screenshot", help="Capture screenshot of protected page")
    p_screenshot.add_argument("url", help="Target URL")
    p_screenshot.add_argument("--out", default="/tmp/cloak_screenshot.png", help="Output path")
    p_screenshot.add_argument("--full-page", action="store_true", help="Capture full scrollable page")
    p_screenshot.add_argument("--wait-selector", help="CSS selector to await")
    p_screenshot.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds")
    p_screenshot.add_argument("--humanize", action="store_true", help="Enable human interaction patterns")
    p_screenshot.add_argument("--proxy", help="Proxy URL or specification")
    p_screenshot.add_argument("--timezone", help="IANA timezone")
    p_screenshot.add_argument("--locale", help="BCP 47 locale")
    p_screenshot.add_argument("--quiet", action="store_true", help="Suppress progress logs")

    # extract
    p_extract = subparsers.add_parser("extract", help="Extract elements via CSS selector")
    p_extract.add_argument("url", help="Target URL")
    p_extract.add_argument("--selector", required=True, help="CSS selector")
    p_extract.add_argument("--attribute", help="Element attribute to extract (default: inner text)")
    p_extract.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds")
    p_extract.add_argument("--humanize", action="store_true", help="Enable human interaction patterns")
    p_extract.add_argument("--proxy", help="Proxy URL or specification")
    p_extract.add_argument("--json", action="store_true", help="Output results in JSON")

    # eval
    p_eval = subparsers.add_parser("eval", help="Evaluate JS expression within page")
    p_eval.add_argument("url", help="Target URL")
    p_eval.add_argument("--code", required=True, help="JavaScript code expression to evaluate")
    p_eval.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds")
    p_eval.add_argument("--humanize", action="store_true", help="Enable human interaction patterns")
    p_eval.add_argument("--proxy", help="Proxy URL or specification")

    # serve
    p_serve = subparsers.add_parser("serve", help="Start CDP multiplexer daemon")
    p_serve.add_argument("--port", type=int, default=9222, help="CDP port (default: 9222)")
    p_serve.add_argument("--wait", action="store_true", help="Wait in foreground")

    # agent-browser-env
    subparsers.add_parser("agent-browser-env", help="Print export commands for Hermes agent-browser")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 2

    dispatch = {
        "doctor": run_doctor,
        "fetch": run_fetch,
        "screenshot": run_screenshot,
        "extract": run_extract,
        "eval": run_eval,
        "serve": run_serve,
        "agent-browser-env": run_agent_browser_env,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 2

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
