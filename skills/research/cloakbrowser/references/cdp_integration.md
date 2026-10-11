# CDP Integration & Multiplexing with Hermes Agent

CloakBrowser provides `cloakserve`, a CDP multiplexer that routes Chrome DevTools Protocol connections to isolated browser instances per fingerprint seed.

## Architecture

```
Hermes Agent (browser_tool / agent-browser)
       │
       ▼ (CDP over WebSocket / HTTP)
cloakserve (Port 9222)
  ├── Seed "task_1" ──> Stealth Chromium Process 1 (Fingerprint A)
  └── Seed "task_2" ──> Stealth Chromium Process 2 (Fingerprint B)
```

## Running the CDP Server

You can start `cloakserve` using the bundled runner:

```bash
python3 skills/research/cloakbrowser/scripts/cloak_runner.py serve --port 9222
```

The daemon listens on `http://127.0.0.1:9222`.

## Connecting Hermes Native Browser Tools

Hermes Agent natively supports external CDP connections via the `BROWSER_CDP_URL` environment variable or `/browser connect`:

```bash
# Option 1: Live connection in terminal session
export BROWSER_CDP_URL="http://127.0.0.1:9222?fingerprint=hermes_main&timezone=America/New_York&locale=en-US"

# Option 2: Within Hermes CLI
/browser connect http://127.0.0.1:9222?fingerprint=hermes_main
```

Once connected, all native browser commands:
- `browser_navigate`
- `browser_snapshot`
- `browser_click`
- `browser_type`

operate directly within the stealth Chromium session.

## Environment Patching for Local `agent-browser`

If Hermes runs in local headless mode using `agent-browser` (without CDP), you can redirect `agent-browser` to execute CloakBrowser's stealth Chromium binary directly:

```bash
eval $(python3 skills/research/cloakbrowser/scripts/cloak_runner.py agent-browser-env)
```

This sets:
- `AGENT_BROWSER_EXECUTABLE_PATH`: absolute path to the patched Chromium binary.
- `AGENT_BROWSER_ARGS`: default C++ stealth flags (`--disable-blink-features=AutomationControlled`, fingerprint seeding, etc.).
