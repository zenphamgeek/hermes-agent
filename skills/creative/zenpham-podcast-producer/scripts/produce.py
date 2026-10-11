#!/usr/bin/env python3
"""Produce a ZENPHAM podcast; optionally upload it privately and report Telegram."""
import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request
from pathlib import Path

REPO = Path("/home/zen/hermes-agent")
VIDEO_ROOT = REPO / "assets/scripts_video"
VALIDATOR = REPO / "skills/creative/zenpham-script-writer/scripts/zenpham_script.py"
PUBLISHER = REPO / "skills/media/youtube-publisher/scripts/yt_publish.py"


def run(command: list[str], timeout: int) -> str:
    result = subprocess.run(command, cwd=VIDEO_ROOT, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:] or result.stdout[-2000:])
    return result.stdout


def title_for(script: Path) -> str:
    text = script.read_text(encoding="utf-8")
    match = re.search(r'END_TITLE:\s*"(.+?)"', text)
    if match:
        return re.sub(r"^ZENPHAM\s*(?:—|-|:)\s*", "", match.group(1), flags=re.I).strip()
    match = re.search(r'Kịch bản video ZENPHAM\s*—\s*"(.+?)"', text)
    return match.group(1).strip() if match else script.stem.replace("_", " ").title()


def slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value.replace("Đ", "D").replace("đ", "d")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


def telegram(message: str) -> None:
    env_path = Path.home() / ".hermes/.env"
    env = dict(os.environ)
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = (env.get("TELEGRAM_ALLOWED_USERS") or "").split(",", 1)[0].strip()
    if not token or not chat_id:
        raise RuntimeError("Telegram credentials unavailable")
    data = json.dumps({"chat_id": chat_id, "text": message, "disable_web_page_preview": True}).encode()
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Telegram HTTP {response.status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path, help="Script relative to assets/scripts_video or absolute")
    parser.add_argument("--publish", action="store_true", help="Upload privately to ZENPHAM then notify Telegram")
    parser.add_argument("--description", default="Một suy ngẫm đời thường từ ZENPHAM.")
    args = parser.parse_args()
    script = args.script if args.script.is_absolute() else VIDEO_ROOT / args.script
    if not script.is_file():
        parser.error(f"Script not found: {script}")
    title = title_for(script)
    final = VIDEO_ROOT / "output" / f"{slug(title)}_final.mp4"
    try:
        run([sys.executable, str(VALIDATOR), str(script)], 60)
        for command, timeout in (
            ([sys.executable, "fetch_stock.py", "--md", str(script), "--force"], 900),
            ([sys.executable, "post_stock.py", "--md", str(script)], 1200),
            ([sys.executable, "tts_sangtruong.py", "--md", str(script), "--force"], 1200),
            ([sys.executable, "assemble_podcast.py", "--md", str(script)], 2100),
        ):
            run(command, timeout)
        probe = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "json", str(final)], 30)
        streams = json.loads(probe).get("streams", [])
        if not final.is_file() or final.stat().st_size < 10_000_000 or not any(s.get("width") == 1080 and s.get("height") == 1920 for s in streams):
            raise RuntimeError("Final media validation failed")
        result = {"status": "rendered", "video": str(final), "title": title}
        if args.publish:
            check = json.loads(run([sys.executable, str(PUBLISHER), "--check"], 120))
            if check.get("channel") != "ZENPHAM":
                raise RuntimeError("Refusing upload: YouTube channel is not ZENPHAM")
            upload = run([sys.executable, str(PUBLISHER), "upload", "--video", str(final), "--title", f"{title} #Shorts", "--description", args.description, "--tags", "ZENPHAM,triết học,podcast,shorts", "--category", "22", "--privacy", "private", "--shorts"], 1200)
            result = json.loads(upload.splitlines()[-1])
            if result.get("status") != "ok":
                raise RuntimeError("YouTube upload failed")
            telegram(f"ZENPHAM: Đã publish riêng tư thành công.\n{title}\n{result['url']}")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
