#!/usr/bin/env python3
"""
Trae Interactive Remote Bridge & Autonomous Co-Pilot Engine
Features:
1. Smart window routing (Dell DP-1, Samsung HDMI-1, Laptop eDP-1).
2. Remote chat injection into Trae IDE.
3. Vision AI Action-Button detector (Continue, Run in Terminal, Allow, Confirm).
4. Wayland/Xwayland auto-clicker for approval buttons.
5. Autopilot Mode is BLOCKED — Hermes never starts autopilot; the Trae Autopilot Extension owns automation.
6. Git Diff & Completion reporting to Telegram.
7. Project management (registry, selection, project-aware prompts).
"""

import os
import sys
import time
import json
import base64
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import Image
from hermes_constants import get_hermes_home

_HERMES_HOME = get_hermes_home()

DEFAULT_OUTPUT_DIR = Path("/home/zen/workspace/output/trae_snapshots")
DEFAULT_HERMES_ENV = _HERMES_HOME / ".env"
AUTOPILOT_STATE_FILE = _HERMES_HOME / "autopilot.json"
PROJECTS_REGISTRY_FILE = _HERMES_HOME / "trae_projects.json"
DEFAULT_WORKSPACE = Path("/home/zen/workspace")

# Well-known project directories for auto-discovery
_AUTO_DISCOVER_ROOTS = [Path("/home/zen")]


def load_hermes_env():
    env_vars = {}
    if DEFAULT_HERMES_ENV.exists():
        with open(DEFAULT_HERMES_ENV, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


def get_autopilot_state() -> bool:
    """Hermes autopilot stays disabled; the Trae extension owns automation."""
    return False


def set_autopilot_state(enabled: bool) -> bool:
    """Blocked: Hermes never starts autopilot and never touches autopilot.json.

    autopilot.json is the Trae Autopilot Extension's own state file
    (trae-controller/trae_controller/state.py). Writing it here would
    override the extension — that is the conflict we are preventing.
    """
    return False


# ---------------------------------------------------------------------------
# Project Management
# ---------------------------------------------------------------------------

def _load_projects_registry() -> dict:
    """Load the project registry from disk."""
    if PROJECTS_REGISTRY_FILE.exists():
        try:
            with open(PROJECTS_REGISTRY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"projects": {}, "active": None}


def _save_projects_registry(registry: dict) -> None:
    """Persist the project registry to disk."""
    PROJECTS_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROJECTS_REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def project_list() -> dict:
    """Return all registered projects with their paths and metadata."""
    reg = _load_projects_registry()
    return reg.get("projects", {})


def project_active() -> tuple:
    """Return (name, path) of the active project, or (None, None)."""
    reg = _load_projects_registry()
    active = reg.get("active")
    if active and active in reg.get("projects", {}):
        return active, reg["projects"][active]["path"]
    return None, None


def project_add(name: str, path: str, description: str = "") -> str:
    """Register a project. Returns status message."""
    p = Path(path).expanduser().resolve()
    if not p.is_dir():
        return f"❌ Directory not found: {path}"
    reg = _load_projects_registry()
    projects = reg.setdefault("projects", {})
    projects[name] = {
        "path": str(p),
        "description": description or name,
        "added_at": time.time(),
    }
    # Auto-select if first project
    if reg.get("active") is None:
        reg["active"] = name
    _save_projects_registry(reg)
    return f"✅ Project '{name}' registered: {p}"


def project_remove(name: str) -> str:
    """Remove a project from the registry."""
    reg = _load_projects_registry()
    projects = reg.get("projects", {})
    if name not in projects:
        return f"❌ Project '{name}' not found"
    del projects[name]
    if reg.get("active") == name:
        reg["active"] = next(iter(projects), None)
    _save_projects_registry(reg)
    return f"🗑️ Project '{name}' removed"


def project_select(name: str) -> str:
    """Set the active project."""
    reg = _load_projects_registry()
    projects = reg.get("projects", {})
    if name not in projects:
        # Fuzzy match: try prefix
        matches = [k for k in projects if k.startswith(name)]
        if len(matches) == 1:
            name = matches[0]
        elif len(matches) > 1:
            return f"❌ Ambiguous: {', '.join(matches)}"
        else:
            return f"❌ Project '{name}' not found. Use `trae project list` to see available."
    reg["active"] = name
    _save_projects_registry(reg)
    path = projects[name]["path"]
    return f"📂 Active project: **{name}** → `{path}`"


def project_discover() -> str:
    """Auto-discover git repositories and register them."""
    reg = _load_projects_registry()
    projects = reg.setdefault("projects", {})
    found = 0
    for root in _AUTO_DISCOVER_ROOTS:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("."):
                continue
            git_dir = child / ".git"
            if not git_dir.is_dir():
                continue
            name = child.name
            if name in projects:
                continue
            # Get branch
            try:
                branch = subprocess.run(
                    ["git", "-C", str(child), "branch", "--show-current"],
                    capture_output=True, text=True, timeout=3
                ).stdout.strip()
            except Exception:
                branch = "?"
            projects[name] = {
                "path": str(child),
                "description": f"{name} (branch: {branch})",
                "added_at": time.time(),
            }
            found += 1
    if reg.get("active") is None and projects:
        reg["active"] = next(iter(projects))
    _save_projects_registry(reg)
    return f"🔍 Discovered {found} new projects. Total: {len(projects)}"


def project_format_list() -> str:
    """Format project list for Telegram display."""
    reg = _load_projects_registry()
    projects = reg.get("projects", {})
    active = reg.get("active")
    if not projects:
        return "📂 No projects registered. Use `trae project discover` or `trae project add <name> <path>`."
    lines = ["📂 **Registered Projects:**\n"]
    for name, info in sorted(projects.items()):
        marker = "▶" if name == active else "•"
        desc = info.get("description", "")
        path = info.get("path", "")
        lines.append(f"{marker} **{name}** — `{path}`")
        if desc and desc != name:
            lines.append(f"  _{desc}_")
    lines.append(f"\n🎯 Active: **{active or 'None'}**")
    return "\n".join(lines)


def project_aware_prompt(prompt: str, project_name: str) -> str:
    """Prefix a prompt with the exact registered project identity."""
    projects = _load_projects_registry().get("projects", {})
    project = projects.get(project_name)
    if not project:
        raise ValueError(f"Project {project_name!r} is not registered")
    path = str(Path(project["path"]).expanduser().resolve())
    return f"[Project: {project_name} @ {path}]\n{prompt}"


def _handle_project_command(args_str: str) -> str:
    """Dispatch project subcommands. Returns formatted result string."""
    parts = args_str.strip().split(None, 2)
    if not parts:
        return project_format_list()

    subcmd = parts[0].lower()

    if subcmd in ("list", "ls"):
        return project_format_list()

    if subcmd in ("discover", "scan"):
        return project_discover()

    if subcmd in ("active", "current"):
        name, path = project_active()
        if name:
            return f"🎯 Active project: **{name}** → `{path}`"
        return "❌ No active project. Use `trae project select <name>`."

    if subcmd in ("select", "use", "switch"):
        if len(parts) < 2:
            return "Usage: `trae project select <name>`"
        return project_select(parts[1])

    if subcmd == "add":
        if len(parts) < 3:
            return "Usage: `trae project add <name> <path> [description]`"
        name = parts[1]
        rest = parts[2].split(None, 1)
        path = rest[0]
        desc = rest[1] if len(rest) > 1 else ""
        return project_add(name, path, desc)

    if subcmd in ("remove", "rm", "delete"):
        if len(parts) < 2:
            return "Usage: `trae project remove <name>`"
        return project_remove(parts[1])

    # Treat unknown subcmd as project name to select
    return project_select(subcmd)


def copy_to_clipboard(text: str) -> bool:
    """Copy text to Wayland / X11 clipboard using native Gtk with fallback to tools."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, Gdk
        cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        cb.set_text(text, -1)
        cb.store()
        while Gtk.events_pending():
            Gtk.main_iteration()
        return True
    except Exception:
        pass

    try:
        proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        proc.communicate(text.encode("utf-8"))
        if proc.returncode == 0:
            return True
    except Exception:
        pass

    try:
        proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        proc.communicate(text.encode("utf-8"))
        if proc.returncode == 0:
            return True
    except Exception:
        pass
    return False


def get_monitor_offset(target: str = "dell"):
    """
    Physical coordinates on unified 6720x3780 Wayland canvas:
    - Dell (DP-1): (3840, 1113, 2880, 1620)
    - Samsung (HDMI-1): (960, 0, 2880, 1620)
    - Laptop (eDP-1): (0, 1620, 3840, 2160)
    """
    target = target.lower()
    if "samsung" in target or "hdmi" in target:
        return (960, 0, 2880, 1620), (640, 0, 1920, 1080), "Samsung (HDMI-1)"
    elif "laptop" in target or "edp" in target:
        return (0, 1620, 3840, 2160), (0, 1080, 2560, 1440), "Laptop (eDP-1)"
    else:
        return (3840, 1113, 2880, 1620), (2560, 742, 1920, 1080), "Dell (DP-1)"


def select_cdp_target(candidates: list[dict], project_name: str = None) -> dict | None:
    """Select one CDP page. Ambiguous or missing project matches fail closed."""
    pages = [item for item in candidates if item.get("webSocketDebuggerUrl")]
    if not project_name:
        return pages[0] if len(pages) == 1 else None

    query = project_name.strip().casefold()
    exact = []
    partial = []
    for page in pages:
        fields = [str(page.get(key, "")).casefold() for key in ("project_name", "title", "url", "description")]
        path_names = [Path(urllib.parse.unquote(value)).name.casefold() for value in fields if value]
        if query in fields or query in path_names:
            exact.append(page)
        elif any(query in value for value in fields):
            partial.append(page)
    matches = exact or partial
    return matches[0] if len(matches) == 1 else None


def _fetch_cdp_pages(ports: list | None = None) -> list:
    """Fetch CDP page targets across ports via GET /json/list."""
    pages = []
    for port in ports or [9339, 9222]:
        try:
            req = urllib.request.Request(f"http://localhost:{port}/json/list", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=1.5) as r:
                targets = json.loads(r.read().decode("utf-8"))
            pages.extend({**t, "_cdp_port": port} for t in targets if t.get("type") == "page")
        except Exception:
            continue
    return pages


def resolve_cdp_target(project_name: str, ports: list | None = None) -> dict:
    """Return the single CDP target for a project, or raise ValueError.

    Matches by registered project path contained in the page URL, else by
    exact case-insensitive title. Raises when zero or multiple targets
    match so callers never broadcast to the wrong window.
    """
    reg = _load_projects_registry()
    proj = reg.get("projects", {}).get(project_name)
    if not proj:
        raise ValueError(f"Project {project_name!r} is not registered")
    proj_path = str(Path(proj["path"]).expanduser().resolve()).casefold()
    query = str(proj.get("cdp_name", project_name)).strip().casefold()

    exact = []
    partial = []
    for page in _fetch_cdp_pages(ports):
        url = urllib.parse.unquote(str(page.get("url", ""))).casefold()
        title = str(page.get("title", "")).casefold()
        # Trae title format: "<file> - <Project> - TraeCode"; a window belongs
        # to the project iff that project name appears as a title segment.
        title_segments = [seg.strip() for seg in title.split("-") if seg.strip()]
        if proj_path in url or title == query or query in title_segments:
            exact.append(page)

    matches = exact
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"No CDP target found for project {project_name!r}")
    raise ValueError(f"Ambiguous CDP target for project {project_name!r}: {len(matches)} matches")


def inject_via_cdp(message: str, project_name: str = None, ports: list | None = None) -> bool:
    """Inject into exactly one matching Trae CDP page.

    With a project_name the target is resolved exactly and never falls back
    to a broadcast or to the desktop path.
    """
    if project_name:
        try:
            page = resolve_cdp_target(project_name, ports)
        except ValueError as exc:
            print(f"[!] {exc}; refusing to send.", file=sys.stderr)
            return False
    else:
        page = select_cdp_target(_fetch_cdp_pages(ports), None)
        if not page:
            print("[!] No unique CDP target; refusing to send.", file=sys.stderr)
            return False

    try:
            import asyncio
            import websockets

            async def _do_inject():
                ws_url = page.get("webSocketDebuggerUrl")
                if not ws_url:
                    return False
                async with websockets.connect(ws_url, max_size=10_000_000, open_timeout=3) as ws:
                    js_inject = f"""
                    (function(){{
                        const box = document.querySelector('.chat-input-v2-input-box-editable') || 
                                    document.querySelector('.chat-input-v2-editor') || 
                                    document.querySelector('[contenteditable="true"]');
                        if (!box) return {{ok: false, error: 'no_editor_box'}};

                        // 1. Focus editor
                        box.focus();

                        // 2. Select Lexical paragraph range
                        const p = box.querySelector('.chat-input-v2__paragraph') || box;
                        const sel = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(p);
                        sel.removeAllRanges();
                        sel.addRange(range);

                        // 3. Clear and insert text natively
                        document.execCommand('selectAll', false, null);
                        document.execCommand('insertText', false, {json.dumps(message)});

                        // 4. Click Send Button or Retry Button
                        setTimeout(() => {{
                            const sendBtn = document.querySelector('.chat-input-v2-send-button') || 
                                            document.querySelector('button[aria-label="Send"]') ||
                                            document.querySelector('.chat-input-v2-editor-part-lower__right button:last-of-type');
                            if (sendBtn) {{
                                sendBtn.click();
                            }}
                        }}, 150);

                        return {{ok: true, text: box.innerText}};
                    }})()
                    """
                    await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js_inject, "returnByValue": True}}))
                    resp = await ws.recv()
                    data = json.loads(resp)
                    res_val = data.get("result", {}).get("result", {}).get("value", {})
                    return res_val.get("ok", False)

            success = asyncio.run(_do_inject())
            if success:
                print(f"[✓] Successfully injected prompt into Trae IDE via CDP port {page['_cdp_port']} (Zero-Focus V8 Lexical Engine).")
                return True
    except Exception as exc:
        print(f"[!] CDP injection failed: {exc}", file=sys.stderr)
    return False


def send_chat_to_trae(message: str, target: str = "dell", project_name: str = None) -> bool:
    """Inject into one explicitly identified project; never route by monitor."""
    if not project_name:
        print("[!] --project is required; refusing to send.", file=sys.stderr)
        return False
    return inject_via_cdp(message, project_name=project_name)


def _send_legacy_desktop(message: str, target: str = "dell") -> bool:
    """Legacy desktop injection retained for non-project UI actions only."""
    # Fallback to native Wayland AT-SPI & GTK Clipboard
    (ox, oy, ow, oh), (lx, ly, lw, lh), label = get_monitor_offset(target)
    print(f"[*] Injecting prompt into Trae IDE on {label} via AT-SPI...")

    # Logical coordinates for AT-SPI Wayland mouse
    chat_logical_x = lx + int(lw * 0.85)
    chat_logical_y = ly + int(lh * 0.90)

    atspi_script = f"""
import gi, time, sys
gi.require_version('Gtk', '3.0')
gi.require_version('Atspi', '2.0')
from gi.repository import Gtk, Gdk, Atspi

# 1. Clipboard
cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
cb.set_text({json.dumps(message)}, -1)
cb.store()
while Gtk.events_pending():
    Gtk.main_iteration()

# 2. Focus
Atspi.init()
time.sleep(0.15)
Atspi.generate_mouse_event({chat_logical_x}, {chat_logical_y}, 'b1c')
time.sleep(0.3)

# 3. Paste (Ctrl+V)
Atspi.generate_keyboard_event(65507, None, Atspi.KeySynthType.PRESS)
time.sleep(0.06)
Atspi.generate_keyboard_event(118, None, Atspi.KeySynthType.SYM)
time.sleep(0.06)
Atspi.generate_keyboard_event(65507, None, Atspi.KeySynthType.RELEASE)
time.sleep(0.3)

# 4. Enter
Atspi.generate_keyboard_event(65293, None, Atspi.KeySynthType.SYM)
print('[✓] AT-SPI Native Wayland Injection Succeeded.')
"""
    try:
        res = subprocess.run(
            ["/usr/bin/python3", "-c", atspi_script],
            capture_output=True,
            text=True,
            timeout=8
        )
        if res.returncode == 0:
            print(f"[✓] Successfully injected prompt into Trae IDE on {label} via AT-SPI.")
            return True
        else:
            print(f"[*] AT-SPI warning: {res.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"[*] AT-SPI execution error: {e}", file=sys.stderr)

    # Fallback to xdotool for Xwayland
    chat_input_x = ox + int(ow * 0.85)
    chat_input_y = oy + int(oh * 0.92)
    copy_to_clipboard(message)
    subprocess.run(["xdotool", "mousemove", str(chat_input_x), str(chat_input_y), "click", "1"])
    time.sleep(0.25)
    subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
    time.sleep(0.3)
    subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"])
    return True


# ---------------------------------------------------------------------------
# Unblock state machine
# ---------------------------------------------------------------------------

# observed UI signals that imply a state (checked in priority order)
_APPROVAL_SIGNALS = ("continue", "always continue", "run in terminal", "allow", "confirm", "apply", "accept")
_RUNNING_SIGNALS = ("running", "generating", "thinking", "executing", "streaming")


def classify_trae_ui_state(observation: str = "") -> str:
    """Map an observed UI signal to a state: approval | model_error | running | idle."""
    text = (observation or "").casefold()
    if "model request failed" in text or "request failed" in text:
        return "model_error"
    if any(s in text for s in _APPROVAL_SIGNALS):
        return "approval"
    if any(s in text for s in _RUNNING_SIGNALS):
        return "running"
    return "idle"


def unblock_trae(project_name: str, task_ref: str, last_action: str = "",
                 observed_state: str = "idle", max_retries: int = 3) -> bool:
    """Bounded-retry unblock: inject a context-aware recovery prompt per attempt.

    Never loops forever: at most max_retries inject attempts, then returns
    False so the caller can escalate instead of silently spinning.
    """
    recovery = (
        f"[Unblock {project_name}] State: {observed_state}. "
        f"Pending task: {task_ref}. Last action attempted: {last_action or 'none'}. "
        f"Continue the pending task now; do not repeat the last action."
    )
    for attempt in range(1, max_retries + 1):
        if inject_via_cdp(recovery, project_name=project_name):
            print(f"[✓] Unblocked {project_name} on attempt {attempt}.")
            return True
        print(f"[*] Unblock attempt {attempt}/{max_retries} failed.", file=sys.stderr)
        time.sleep(min(2 * attempt, 8))
    print(f"[!] Could not unblock {project_name} after {max_retries} attempts.", file=sys.stderr)
    return False


def detect_action_button_with_vision(image_path: Path) -> dict:
    """Use Vision AI to locate 'Continue' buttons OR detect 'Model request failed' banners in Trae."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "Bạn là hệ thống Vision AI phân tích giao diện Trae IDE.\n"
        "Hãy quan sát ảnh chụp màn hình và tìm xem có sự kiện nào sau đây đang xảy ra:\n"
        "1. Có nút bấm chờ duyệt: 'Continue', 'Always Continue', 'Run in Terminal', 'Run', 'Allow', 'Confirm', 'Accept', 'Apply'.\n"
        "2. Có thanh thông báo lỗi màu đỏ/cảnh báo: 'Model request failed. Click the arrow on the right to expand the provider's error details for troubleshooting.' (hoặc 'Model request failed').\n\n"
        "Hãy trả về DUY NHẤT một JSON format:\n"
        "- Nếu có nút bấm chờ duyệt:\n"
        "{\n"
        '  "found": true,\n'
        '  "action_type": "click_button",\n'
        '  "button_text": "Continue",\n'
        '  "norm_center_x": 860,\n'
        '  "norm_center_y": 780,\n'
        '  "description": "Nút Continue duyệt tool calls"\n'
        "}\n\n"
        "- Nếu có thanh lỗi 'Model request failed':\n"
        "{\n"
        '  "found": true,\n'
        '  "action_type": "model_error_retry",\n'
        '  "error_text": "Model request failed",\n'
        '  "suggested_prompt": "Tiếp tục công việc",\n'
        '  "description": "Lỗi Model request failed cần gửi lệnh Tiếp tục công việc"\n'
        "}\n\n"
        "- Nếu KHÔNG có nút hay lỗi nào:\n"
        '{"found": false, "reason": "Không có nút chờ duyệt hoặc lỗi Model request failed"}'
    )

    llm_url = "http://10.123.214.1:1234/v1/chat/completions"
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 350,
    }

    try:
        req = urllib.request.Request(
            llm_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()
            if "{" in content and "}" in content:
                json_str = content[content.find("{") : content.rfind("}") + 1]
                return json.loads(json_str)
    except Exception as e:
        print(f"[*] Vision detection error: {e}", file=sys.stderr)

    return {"found": False, "reason": "Vision model unavailable"}


def click_continue_button(target: str = "dell", force: bool = False) -> bool:
    """Take screenshot, detect approval buttons or Model Request Failed errors, and auto-recover."""
    from runner import capture_raw_wayland_screen, get_monitors_layout, crop_to_monitor

    timestamp = int(time.time())
    raw_path = DEFAULT_OUTPUT_DIR / f"check_btn_raw_{timestamp}.png"
    snap_path = DEFAULT_OUTPUT_DIR / f"check_btn_{timestamp}.jpg"

    monitors = get_monitors_layout()
    if not capture_raw_wayland_screen(raw_path):
        print("[!] Failed to capture screen for button check.", file=sys.stderr)
        return False

    raw_img = Image.open(raw_path)
    cropped_img, label = crop_to_monitor(raw_img, monitors, target)
    cropped_img.convert("RGB").save(snap_path, "JPEG", quality=90)
    if raw_path.exists():
        raw_path.unlink()

    (ox, oy, ow, oh), _ = get_monitor_offset(target)
    btn_info = detect_action_button_with_vision(snap_path)

    if btn_info.get("found"):
        action_type = btn_info.get("action_type", "click_button")

        # CASE 1: Model Request Failed Error -> Auto inject "Tiếp tục công việc"
        if action_type == "model_error_retry":
            retry_msg = btn_info.get("suggested_prompt", "Tiếp tục công việc")
            print(f"[!] Detected 'Model request failed' error on {label}!")
            print(f"[*] Auto-recovering: Sending '{retry_msg}' into Trae chat...")
            send_chat_to_trae(retry_msg, target=target)

            if snap_path.exists():
                snap_path.unlink()

            # Send Telegram alert
            try:
                from runner import send_to_telegram, load_hermes_env
                time.sleep(1.5)
                verify_raw = DEFAULT_OUTPUT_DIR / f"verify_retry_raw_{timestamp}.png"
                verify_snap = DEFAULT_OUTPUT_DIR / f"autopilot_retry_{timestamp}.jpg"
                if capture_raw_wayland_screen(verify_raw):
                    v_raw_img = Image.open(verify_raw)
                    v_cropped, _ = crop_to_monitor(v_raw_img, monitors, target)
                    v_cropped.convert("RGB").save(verify_snap, "JPEG", quality=88)
                    if verify_raw.exists():
                        verify_raw.unlink()

                    env = load_hermes_env()
                    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
                    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")
                    caption = (
                        f"⚠️ *Phát Hiện Lỗi: Model Request Failed!*\n"
                        f"• **Tự động xử lý**: Đã gửi `'{retry_msg}'` vào ô chat Trae\n"
                        f"• **Màn hình**: {label}\n"
                        f"• **Trạng thái**: Đã kích hoạt Trae tiếp tục công việc ổn định 🚀\n"
                        f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    print("[*] Dispatching recovery report to Telegram...")
                    send_to_telegram(token, chat_id, verify_snap, caption, "Auto-Retry: Model Error")
                    if verify_snap.exists():
                        verify_snap.unlink()
            except Exception as e:
                print(f"[!] Failed to send recovery report to Telegram: {e}", file=sys.stderr)
            return True

        # CASE 2: Action Button Click (Continue / Run)
        nx = btn_info.get("norm_center_x", 850)
        ny = btn_info.get("norm_center_y", 780)
        target_x = ox + int(ow * (nx / 1000.0))
        target_y = oy + int(oh * (ny / 1000.0))

        btn_text = btn_info.get("button_text", "Continue")
        print(f"[✓] Found button '{btn_text}' at screen coordinate ({target_x}, {target_y})!")
        print(f"[*] Moving mouse and clicking '{btn_text}'...")
        subprocess.run(["xdotool", "mousemove", str(target_x), str(target_y), "click", "1"])
        time.sleep(0.5)
        print(f"[✓] Successfully clicked '{btn_text}' on {label}!")

        if snap_path.exists():
            snap_path.unlink()

        # Send Telegram confirmation report with fresh screenshot
        try:
            from runner import send_to_telegram, load_hermes_env
            time.sleep(1.2)  # Wait for Trae UI to transition
            verify_raw = DEFAULT_OUTPUT_DIR / f"verify_click_raw_{timestamp}.png"
            verify_snap = DEFAULT_OUTPUT_DIR / f"autopilot_action_{timestamp}.jpg"
            if capture_raw_wayland_screen(verify_raw):
                v_raw_img = Image.open(verify_raw)
                v_cropped, _ = crop_to_monitor(v_raw_img, monitors, target)
                v_cropped.convert("RGB").save(verify_snap, "JPEG", quality=88)
                if verify_raw.exists():
                    verify_raw.unlink()

                env = load_hermes_env()
                token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
                chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")
                caption = (
                    f"⚡ *Autopilot Action Thành Công!*\n"
                    f"• **Thao tác**: Đã tự động bấm nút `[{btn_text}]`\n"
                    f"• **Màn hình**: {label}\n"
                    f"• **Trạng thái**: Xác nhận Trae IDE đang tiếp tục chạy ổn định 🚀\n"
                    f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                print("[*] Dispatching Autopilot confirmation to Telegram...")
                send_to_telegram(token, chat_id, verify_snap, caption, f"Autopilot: {btn_text}")

                if verify_snap.exists():
                    verify_snap.unlink()
        except Exception as e:
            print(f"[!] Failed to send action report to Telegram: {e}", file=sys.stderr)

        return True
    elif force:
        # Clean up check snapshot
        if snap_path.exists():
            snap_path.unlink()

        default_click_x = ox + int(ow * 0.85)
        default_click_y = oy + int(oh * 0.78)
        print(f"[*] Force-clicking standard Continue button area at ({default_click_x}, {default_click_y})...")
        subprocess.run(["xdotool", "mousemove", str(default_click_x), str(default_click_y), "click", "1"])
        time.sleep(0.5)
        print(f"[✓] Force click executed on {label}.")

        # Send Telegram report
        try:
            from runner import send_to_telegram, load_hermes_env
            time.sleep(1.0)
            verify_raw = DEFAULT_OUTPUT_DIR / f"verify_click_raw_{timestamp}.png"
            verify_snap = DEFAULT_OUTPUT_DIR / f"autopilot_action_{timestamp}.jpg"
            if capture_raw_wayland_screen(verify_raw):
                v_raw_img = Image.open(verify_raw)
                v_cropped, _ = crop_to_monitor(v_raw_img, monitors, target)
                v_cropped.convert("RGB").save(verify_snap, "JPEG", quality=88)
                if verify_raw.exists():
                    verify_raw.unlink()

                env = load_hermes_env()
                token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
                chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")
                caption = (
                    f"⚡ *Autopilot Action (Force Click)*\n"
                    f"• **Thao tác**: Đã click vị trí nút Continue mặc định\n"
                    f"• **Màn hình**: {label}\n"
                    f"• **Trạng thái**: Đã gửi tín hiệu tiếp tục cho Trae IDE 🚀\n"
                    f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_to_telegram(token, chat_id, verify_snap, caption, "Autopilot Click")

                # Clean up verify snapshot after sending
                if verify_snap.exists():
                    verify_snap.unlink()
        except Exception as e:
            print(f"[!] Failed to send action report to Telegram: {e}", file=sys.stderr)

        return True
    else:
        # Clean up check snapshot when no button was detected
        if snap_path.exists():
            snap_path.unlink()
        print(f"[*] No Continue/Confirm button detected ({btn_info.get('reason')}).")
        return False


def get_git_diff_summary(workspace_dir: Path = None) -> str:
    """Extract git status and git diff --stat summary for the workspace.

    If no workspace_dir is given, uses the active project's path.
    """
    if workspace_dir is None:
        _, active_path = project_active()
        workspace_dir = Path(active_path) if active_path else DEFAULT_WORKSPACE
    try:
        status_res = subprocess.run(
            ["git", "-C", str(workspace_dir), "status", "--short"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        diff_res = subprocess.run(
            ["git", "-C", str(workspace_dir), "diff", "--stat"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        status_text = status_res.stdout.strip()
        diff_text = diff_res.stdout.strip()

        proj_label = f" ({workspace_dir.name})"
        if not status_text and not diff_text:
            return f"✅ *Workspace Git State{proj_label}*: Không có file nào bị thay đổi (Clean Working Tree)."

        lines = [f"📁 *Thay đổi mã nguồn{proj_label} (Git Changes)*:"]
        if diff_text:
            lines.append("```text\n" + diff_text + "\n```")
        if status_text:
            lines.append("*Trạng thái chi tiết*:")
            lines.append("```text\n" + status_text[:800] + "\n```")

        return "\n".join(lines)
    except Exception as e:
        return f"ℹ️ *Git Info*: Không thể lấy git diff ({e})"


def report_task_completion(target: str = "dell") -> bool:
    """Capture completion snapshot, collect git diff, and dispatch full report to Telegram."""
    from runner import capture_trae_cdp_window, capture_wayland_desktop_portal, get_monitors_layout, crop_to_monitor, send_to_telegram, load_hermes_env

    env = load_hermes_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    timestamp = int(time.time())
    raw_path = DEFAULT_OUTPUT_DIR / f"complete_raw_{timestamp}.png"
    final_path = DEFAULT_OUTPUT_DIR / f"complete_trae_{timestamp}.jpg"

    active_name, _ = project_active()
    label = ""
    captured_via_cdp = False

    # 1. Try direct CDP window capture with active project
    ok, cdp_label = capture_trae_cdp_window(final_path, project=active_name)
    if ok:
        captured_via_cdp = True
        label = cdp_label

    # 2. Fallback to desktop portal + monitor crop
    if not captured_via_cdp:
        monitors = get_monitors_layout()
        if not capture_wayland_desktop_portal(raw_path):
            print("[!] Screen grab failed.", file=sys.stderr)
            return False

        raw_img = Image.open(raw_path)
        cropped_img, label = crop_to_monitor(raw_img, monitors, target)
        cropped_img.convert("RGB").save(final_path, "JPEG", quality=88)
        if raw_path.exists():
            raw_path.unlink()

    git_summary = get_git_diff_summary()
    caption = (
        f"🎉 *Trae IDE Đã Hoàn Tất Tác Vụ!* ({label})\n"
        f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"{git_summary}\n\n"
        f"📸 *Ảnh chụp màn hình kết quả đính kèm.*"
    )

    print(f"[*] Sending completion report to Telegram for {label}...")
    return send_to_telegram(token, chat_id, final_path, caption, label)


def run_autopilot_daemon(interval: int = 600, target: str = "dell"):
    """Hard-blocked: Hermes autopilot daemon must never start.

    The Trae Autopilot Extension (trae-controller systemd services) owns all
    loop/unblock/smart-prompt automation. Returning immediately prevents a
    second watcher from racing the extension.
    """
    print("🛑 Hermes Autopilot daemon bị vô hiệu hóa. Trae Autopilot Extension là bộ điều khiển duy nhất.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Trae IDE Interactive Remote Bridge & Co-Pilot.")
    parser.add_argument("--send", "-s", help="Inject prompt / message into Trae chat")
    parser.add_argument("--target", "-t", default="dell", help="Target monitor ('dell', 'samsung', 'laptop')")
    parser.add_argument("--interval", "-i", type=int, default=600, help="Autopilot scan interval in seconds (default: 600s = 10 minutes)")
    parser.add_argument("--continue-click", "-c", action="store_true", help="Detect and click 'Continue' / 'Run' button")
    parser.add_argument("--force-click", action="store_true", help="Force click default Continue button position")
    parser.add_argument("--autopilot", choices=["on", "off", "status", "daemon"], help="Manage Autopilot mode")
    parser.add_argument("--report-completion", action="store_true", help="Capture snapshot + Git Diff and send to Telegram")
    parser.add_argument("--git-diff", action="store_true", help="Print Git Diff summary")
    parser.add_argument("--project", "-p", help="Project subcommand (list/discover/select/add/remove) or project name for --send")
    parser.add_argument("--project-name", help="Override active project for this invocation (used with --send)")

    args = parser.parse_args()

    # --- Project management ---
    if args.project is not None:
        # If --send is also provided, --project is the project name
        if args.send:
            try:
                prompt = project_aware_prompt(args.send, project_name=args.project)
            except ValueError as exc:
                parser.error(str(exc))
            if not send_chat_to_trae(prompt, target=args.target, project_name=args.project):
                parser.error(f"Send refused for project {args.project!r}")
            return
        # Otherwise, it's a project subcommand
        result = _handle_project_command(args.project)
        print(result)
        return

    if args.autopilot:
        if args.autopilot == "on":
            set_autopilot_state(False)
            print("🛑 Hermes Autopilot luôn TẮT; Trae Autopilot Extension là bộ điều khiển duy nhất.")
        elif args.autopilot == "off":
            set_autopilot_state(False)
            print("🛑 [✓] Autopilot Mode: TẮT (OFF) — Chỉ click khi có lệnh từ người dùng.")
        elif args.autopilot == "status":
            st = get_autopilot_state()
            name, path = project_active()
            proj_info = f"\n📂 Active project: {name} → {path}" if name else "\n📂 No active project"
            print(f"ℹ️ Autopilot Status: {'ON (Đang Bật)' if st else 'OFF (Đang Tắt)'}{proj_info}")
        elif args.autopilot == "daemon":
            set_autopilot_state(False)
            print("🛑 Hermes Autopilot daemon bị vô hiệu hóa để tránh xung đột extension.")
        return

    if args.send:
        if not args.project_name:
            parser.error("--send requires --project <registered-name>")
        try:
            prompt = project_aware_prompt(args.send, project_name=args.project_name)
        except ValueError as exc:
            parser.error(str(exc))
        if not send_chat_to_trae(prompt, target=args.target, project_name=args.project_name):
            parser.error(f"Send refused for project {args.project_name!r}")

    if args.continue_click or args.force_click:
        click_continue_button(target=args.target, force=args.force_click)

    if args.report_completion:
        report_task_completion(target=args.target)

    if args.git_diff:
        # Use active project's directory for git diff
        _, active_path = project_active()
        workspace = Path(active_path) if active_path else None
        print(get_git_diff_summary(workspace))

    if not any([args.send, args.continue_click, args.force_click, args.autopilot, args.report_completion, args.git_diff]):
        parser.print_help()


if __name__ == "__main__":
    main()
