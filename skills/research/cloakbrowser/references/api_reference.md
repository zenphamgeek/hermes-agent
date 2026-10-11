# CloakBrowser API Reference

This document describes how to use `cloakbrowser` programmatically in Python workflows.

## Basic Usage

CloakBrowser provides `launch` and `launch_context` as drop-in replacements for Playwright's Chromium launcher.

```python
from cloakbrowser import launch

# Launch stealth Chromium browser
browser = launch(headless=True, humanize=True)
page = browser.new_page()

page.goto("https://bot.sannysoft.com")
print("Title:", page.title())

# Always close the browser when finished
browser.close()
```

## `launch()` Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `headless` | `bool` | `True` | Run headless or headed (`False`). |
| `humanize` | `bool` | `False` | Enable natural Bézier mouse paths, variable keystroke cadence, and scroll momentum. |
| `human_preset` | `str` | `"default"` | Preset configuration (`"default"`, `"fast"`, `"careful"`). |
| `timezone` | `str \| None` | `None` | IANA timezone (e.g. `"America/New_York"`). Synchronizes browser clock and Intl APIs. |
| `locale` | `str \| None` | `None` | BCP 47 locale (e.g. `"en-US"`). Configures navigator language and UI headers. |
| `proxy` | `str \| dict \| None` | `None` | Proxy URL (`"http://user:pass@host:port"`) or Playwright proxy dictionary. |
| `geoip` | `bool` | `False` | Automatically align timezone and locale with proxy egress IP. |
| `args` | `list[str] \| None` | `None` | Additional Chromium CLI flags. |
| `stealth_args` | `bool` | `True` | Include C++ stealth fingerprint flags (leave `True`). |

## Convenience: `launch_context()`

Creates both browser and context with viewport, user-agent, and permissions configured:

```python
from cloakbrowser import launch_context

context = launch_context(
    headless=True,
    humanize=True,
    timezone="America/Los_Angeles",
    locale="en-US",
)
page = context.new_page()
page.goto("https://protected-service.com")
content = page.content()
context.close()
```

## Humanized Interactions

When `humanize=True` is enabled, standard Playwright methods (`page.click()`, `page.fill()`, `page.type()`, `page.mouse.wheel()`) are automatically wrapped with natural variations:
- Cursor trajectories follow randomized Bézier curves rather than linear instantaneous jumps.
- Typing speed exhibits human Gaussian delay distributions between keypresses.
- Scroll events include acceleration and decelerating momentum.

## Handling Cloudflare Turnstile Challenges

Cloudflare Turnstile often presents an interactive widget or automated challenge. With CloakBrowser:
1. Allow initial page load to complete.
2. Wait for challenge solver:
```python
# Wait for the challenge wrapper to clear
page.wait_for_load_state("networkidle", timeout=15000)
try:
    # If a turnstile iframe is present, allow it to complete verification
    turnstile = page.locator("iframe[src*='challenges.cloudflare.com']")
    if turnstile.count() > 0:
        page.wait_for_timeout(4000)
except Exception:
    pass
```
