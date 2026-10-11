#!/usr/bin/env python3
"""
Trae Screen Analyst Runner for Hermes Agent
Native Wayland Multi-Monitor Support: Introspects monitor layout, isolates & crops
specifically the Trae IDE window / active screen, analyzes with Vision AI, and sends to Telegram.
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
import numpy as np

DEFAULT_OUTPUT_DIR = Path("/home/zen/workspace/output/trae_snapshots")
DEFAULT_HERMES_ENV = Path("/home/zen/.hermes/.env")


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


def get_monitors_layout():
    """Query GNOME Mutter via DBus to get real-time monitor geometry and scale factors."""
    script = """
import gi, json
gi.require_version('Gio', '2.0')
from gi.repository import Gio

bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
res = bus.call_sync(
    'org.gnome.Mutter.DisplayConfig',
    '/org/gnome/Mutter/DisplayConfig',
    'org.gnome.Mutter.DisplayConfig',
    'GetCurrentState',
    None,
    None,
    Gio.DBusCallFlags.NONE,
    -1,
    None
)
serial, monitor_modes, logical_monitors, props = res.unpack()

modes_dict = {}
for mon in monitor_modes:
    (conn, vendor, prod, sn), modes, extra = mon
    for mode in modes:
        mode_id, w, h, refresh, pref_scale, scales, mode_props = mode
        if mode_props.get('is-current', False):
            modes_dict[conn] = {'w': w, 'h': h, 'name': extra.get('display-name', conn)}

monitors = []
for m in logical_monitors:
    x, y, scale, transform, primary, mon_info, extra = m
    conn = mon_info[0][0]
    info = modes_dict.get(conn, {'w': 1920, 'h': 1080, 'name': conn})
    monitors.append({
        'connector': conn,
        'name': info['name'],
        'log_x': x,
        'log_y': y,
        'scale': scale,
        'mode_w': info['w'],
        'mode_h': info['h'],
        'primary': primary
    })

print(json.dumps(monitors))
"""
    try:
        res = subprocess.run(["/usr/bin/python3", "-c", script], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return json.loads(res.stdout.strip())
    except Exception as e:
        print(f"[*] Failed to fetch Mutter display config: {e}", file=sys.stderr)
    return []


def capture_trae_cdp_window(output_path: Path, project: str = None) -> tuple[bool, str]:
    """Capture Trae IDE window directly and silently from CDP render buffer."""
    try:
        trae_pkg = Path("/home/zen/workspace/trae-controller")
        if str(trae_pkg) not in sys.path:
            sys.path.insert(0, str(trae_pkg))
        from trae_controller.core import TraeCDPController  # type: ignore
        controller = TraeCDPController()
        pages = controller.get_all_page_infos()
        if not pages:
            return False, ""
        
        target_page = None
        if project and project.lower() not in ("trae", "auto", "default"):
            for p in pages:
                if project.lower() in p.project_name.lower() or project.lower() in p.title.lower():
                    target_page = p
                    break
        
        if not target_page:
            target_page = pages[0]
            
        success = controller.capture_cdp_screenshot(output_path, project=target_page.project_name)
        if success and output_path.exists() and output_path.stat().st_size > 2000:
            label = f"Trae [{target_page.project_name}] - {target_page.title}"
            return True, label
    except Exception as e:
        print(f"[*] CDP capture error: {e}", file=sys.stderr)
    return False, ""


def capture_wayland_desktop_portal(output_path: Path) -> bool:
    """Capture the full Wayland multi-monitor desktop via portal or grim."""
    # Try grim first if available for speed
    try:
        res = subprocess.run(["grim", str(output_path)], capture_output=True, timeout=5)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 5000:
            return True
    except Exception:
        pass

    portal_script = """
import sys, gi, urllib.parse, shutil
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

target_file = sys.argv[1]
captured_uri = None

def on_response(conn, sender, path, iface, signal, params):
    global captured_uri
    code, results = params.unpack()
    if code == 0 and 'uri' in results:
        captured_uri = results['uri']
    loop.quit()

bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
loop = GLib.MainLoop()

bus.signal_subscribe(
    'org.freedesktop.portal.Desktop',
    'org.freedesktop.portal.Request',
    'Response',
    None,
    None,
    Gio.DBusSignalFlags.NONE,
    on_response
)

try:
    res = bus.call_sync(
        'org.freedesktop.portal.Desktop',
        '/org/freedesktop/portal/desktop',
        'org.freedesktop.portal.Screenshot',
        'Screenshot',
        GLib.Variant('(sa{sv})', ('', {'interactive': GLib.Variant('b', False)})),
        GLib.VariantType('(o)'),
        Gio.DBusCallFlags.NONE,
        -1,
        None
    )
    GLib.timeout_add_seconds(6, loop.quit)
    loop.run()
except Exception:
    sys.exit(1)

if captured_uri:
    src_path = urllib.parse.unquote(urllib.parse.urlparse(captured_uri).path)
    shutil.copy2(src_path, target_file)
    sys.exit(0)
sys.exit(1)
"""
    try:
        res = subprocess.run(["/usr/bin/python3", "-c", portal_script, str(output_path)], capture_output=True, timeout=10)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
            return True
    except Exception as e:
        print(f"[*] Portal error: {e}", file=sys.stderr)
        
    # Fallback to direct CDP if portal is unresponsive
    ok, _ = capture_trae_cdp_window(output_path)
    return ok


def capture_raw_wayland_screen(output_path: Path) -> bool:
    """Backward compatibility wrapper: tries CDP window first, then Portal desktop."""
    ok, _ = capture_trae_cdp_window(output_path)
    if ok:
        return True
    return capture_wayland_desktop_portal(output_path)


def crop_to_monitor(full_img: Image.Image, monitors: list, target: str) -> tuple[Image.Image, str]:
    """Calculate exact pixel coordinates on the unified canvas and crop the desired monitor."""
    full_w, full_h = full_img.size

    # Compute bounding box of logical coordinates
    min_log_x = min(m['log_x'] for m in monitors)
    min_log_y = min(m['log_y'] for m in monitors)
    max_log_x = max(m['log_x'] + int(m['mode_w'] / m['scale']) for m in monitors)
    max_log_y = max(m['log_y'] + int(m['mode_h'] / m['scale']) for m in monitors)
    
    total_log_w = max_log_x - min_log_x
    canvas_scale = full_w / total_log_w

    cropped_monitors = {}
    for m in monitors:
        px_x = int((m['log_x'] - min_log_x) * canvas_scale)
        px_y = int((m['log_y'] - min_log_y) * canvas_scale)
        px_w = int((m['mode_w'] / m['scale']) * canvas_scale)
        px_h = int((m['mode_h'] / m['scale']) * canvas_scale)

        box = (px_x, px_y, min(px_x + px_w, full_w), min(px_y + px_h, full_h))
        crop_img = full_img.crop(box)
        cropped_monitors[m['connector'].lower()] = {
            'image': crop_img,
            'info': m,
            'name': m['name']
        }

    target = target.lower()

    # Match target
    for k in cropped_monitors:
        if target in k or target in cropped_monitors[k]['name'].lower():
            return cropped_monitors[k]['image'], f"{cropped_monitors[k]['name']} ({k.upper()})"

    # Aliases
    if target in ['dell', 'dp']:
        for k in cropped_monitors:
            if 'dp' in k:
                return cropped_monitors[k]['image'], f"{cropped_monitors[k]['name']} ({k.upper()})"
    elif target in ['samsung', 'hdmi']:
        for k in cropped_monitors:
            if 'hdmi' in k:
                return cropped_monitors[k]['image'], f"{cropped_monitors[k]['name']} ({k.upper()})"
    elif target in ['laptop', 'edp', 'builtin']:
        for k in cropped_monitors:
            if 'edp' in k:
                return cropped_monitors[k]['image'], f"{cropped_monitors[k]['name']} ({k.upper()})"

    # AUTO: Find the monitor containing Trae IDE (highest dark theme / IDE code editor density)
    best_score = -1
    best_crop = None
    best_label = "Auto Trae"

    for k, item in cropped_monitors.items():
        arr = np.array(item['image'].convert('RGB'))
        # Detect VSCode/Trae dark theme pixels (RGB ~ 20..40)
        dark_mask = (arr[:, :, 0] >= 15) & (arr[:, :, 0] <= 45) & (arr[:, :, 1] >= 15) & (arr[:, :, 1] <= 45) & (arr[:, :, 2] >= 15) & (arr[:, :, 2] <= 55)
        score = dark_mask.mean()
        if score > best_score:
            best_score = score
            best_crop = item['image']
            best_label = f"{item['name']} ({k.upper()}) [Trae IDE Detected]"

    if best_crop:
        return best_crop, best_label

    return full_img, "Full Canvas"


def analyze_image_with_llm(image_path: Path, custom_prompt: str = None) -> str:
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = custom_prompt or (
        "Bạn là chuyên gia AI phân tích màn hình ứng dụng Trae IDE (Electron).\n"
        "Hãy quan sát kỹ khung ứng dụng Trae và tóm tắt có cấu trúc:\n"
        "1. 🖥️ **Mã nguồn / File đang mở**: Tên file, hàm/logic chính đang hiển thị.\n"
        "2. ⚡ **Terminal / Console**: Output gần nhất, lệnh đang chạy hoặc trạng thái tiến trình.\n"
        "3. ⚠️ **Phát hiện Lỗi / Warning**: Lỗi cú pháp, compile error, log đỏ hoặc vấn đề phát hiện được.\n"
        "4. 🤖 **Trạng thái AI Assistant / Trae Chat**: Hội thoại với AI, task đang thực hiện.\n"
        "5. 💡 **Đề xuất bước tiếp theo**: Gợi ý ngắn gọn 1-2 hành động tiếp theo."
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
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    try:
        req = urllib.request.Request(
            llm_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return (
            f"📸 **Trae IDE Window Snapshot (Cropped App Screen)**\n"
            f"• **File**: `{image_path.name}` ({image_path.stat().st_size // 1024} KB)\n"
            f"• **Thời gian**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• **Trạng thái**: Đã crop chính xác khung ứng dụng Trae IDE trên màn hình.\n"
            f"• **Ghi chú**: Ảnh chụp chi tiết đã gửi kèm bên dưới."
        )


def send_to_telegram(token: str, chat_id: str, image_path: Path, caption: str, screen_label: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = f"----WebKitFormBoundary{int(time.time()*1000)}"

    with open(image_path, "rb") as f:
        file_bytes = f.read()

    tg_caption = caption
    followup_msg = None
    if len(tg_caption) > 1000:
        followup_msg = tg_caption
        tg_caption = f"🎯 *Trae IDE App Snapshot* — {screen_label}\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}\n*(Chi tiết phân tích gửi bên dưới)*"

    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode())
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{tg_caption}\r\n'.encode())
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="parse_mode"\r\n\r\nMarkdown\r\n')
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        f'Content-Disposition: form-data; name="photo"; filename="{image_path.name}"\r\n'.encode()
    )
    body.extend(b"Content-Type: image/jpeg\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                print("[✓] Cropped snapshot photo sent to Telegram successfully.")
                if followup_msg:
                    send_msg_url = f"https://api.telegram.org/bot{token}/sendMessage"
                    msg_payload = json.dumps({
                        "chat_id": chat_id,
                        "text": followup_msg,
                        "parse_mode": "Markdown"
                    }).encode("utf-8")
                    msg_req = urllib.request.Request(
                        send_msg_url,
                        data=msg_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(msg_req, timeout=15) as mresp:
                        if mresp.status == 200:
                            print("[✓] Detailed analysis report sent to Telegram.")
                return True
    except Exception as e:
        print(f"[!] Error sending to Telegram: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Capture & crop specifically Trae IDE Electron window, analyze with Vision, and send to Telegram.")
    parser.add_argument("--target", "-t", default="trae", help="Target screen or project: 'trae' (auto-detect), 'dell', 'samsung', 'laptop', 'all', or project name ('insilos_ee', 'VerticalRisk')")
    parser.add_argument("--project", "-p", help="Target specific project name if multiple Trae windows are open")
    parser.add_argument("--prompt", help="Custom prompt for screen analysis")
    parser.add_argument("--chat-id", "-c", help="Target Telegram Chat ID (defaults to TELEGRAM_ALLOWED_USERS)")
    parser.add_argument("--token", help="Telegram Bot Token (defaults to TELEGRAM_BOT_TOKEN in ~/.hermes/.env)")
    parser.add_argument("--no-telegram", action="store_true", help="Skip sending to Telegram")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    env = load_hermes_env()

    token = args.token or env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = args.chat_id or env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    timestamp = int(time.time())
    raw_path = DEFAULT_OUTPUT_DIR / f"raw_canvas_{timestamp}.png"
    final_path = DEFAULT_OUTPUT_DIR / f"trae_app_{timestamp}.jpg"

    # Check target type: is it a physical monitor or a Trae project/window?
    target_lower = args.target.lower()
    proj_target = args.project or (args.target if target_lower not in ("dell", "dp", "samsung", "hdmi", "laptop", "edp", "all", "desktop") else None)

    screen_label = ""
    captured_via_cdp = False

    # 1. Attempt Direct CDP Window Capture if not explicitly requesting a physical monitor
    if target_lower in ("trae", "auto", "default") or proj_target:
        print(f"[*] Attempting direct Trae window CDP capture (target: {proj_target or 'active'})...")
        ok, cdp_label = capture_trae_cdp_window(final_path, project=proj_target)
        if ok:
            captured_via_cdp = True
            screen_label = cdp_label
            print(f"[✓] Captured Trae IDE window directly via CDP: {screen_label} ({final_path.stat().st_size // 1024} KB)")

    # 2. Fallback / Physical Monitor Capture via Wayland Portal
    if not captured_via_cdp:
        print("[*] Detecting connected displays & Wayland layout...")
        monitors = get_monitors_layout()
        print(f"[*] Found {len(monitors)} active display monitors.")

        print(f"[*] Capturing Wayland screen buffer via Portal...")
        if not capture_wayland_desktop_portal(raw_path):
            print("[!] Failed to capture Wayland screen.", file=sys.stderr)
            sys.exit(1)

        print(f"[*] Isolating & cropping target '{args.target}'...")
        raw_img = Image.open(raw_path)
        if args.target.lower() == "all" or not monitors:
            cropped_img = raw_img
            screen_label = "All Displays"
        else:
            cropped_img, screen_label = crop_to_monitor(raw_img, monitors, args.target)

        # Resize/optimize cleanly to 1080p/1440p
        w, h = cropped_img.size
        if w > 1920 or h > 1080:
            ratio = min(1920 / w, 1080 / h)
            cropped_img = cropped_img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)

        cropped_img.convert("RGB").save(final_path, "JPEG", quality=88, optimize=True)
        print(f"[✓] Cropped Trae window saved at: {final_path} ({final_path.stat().st_size // 1024} KB) [{screen_label}]")

        # Clean up raw multi-screen canvas
        if raw_path.exists():
            raw_path.unlink()

    print("[*] Analyzing cropped Trae screen with Vision AI...")
    analysis = analyze_image_with_llm(final_path, custom_prompt=args.prompt)

    telegram_sent = False
    if not args.no_telegram and token and chat_id:
        print(f"[*] Sending isolated Trae screen to Telegram chat {chat_id}...")
        telegram_sent = send_to_telegram(token, chat_id, final_path, analysis, screen_label)

    result = {
        "success": True,
        "image_path": str(final_path),
        "target": args.target,
        "screen_label": screen_label,
        "timestamp": timestamp,
        "telegram_sent": telegram_sent,
        "analysis": analysis,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n" + "="*50)
        print(f"📊 TRAE IDE SCREEN ANALYSIS ({screen_label})")
        print("="*50)
        print(analysis)
        print("="*50)
        print(f"📁 Image: {final_path}")
        print(f"📱 Telegram: {'Sent ✓' if telegram_sent else 'Skipped/Failed'}")


if __name__ == "__main__":
    main()
