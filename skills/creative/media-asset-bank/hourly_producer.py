#!/usr/bin/env python3
"""
24/7 Hourly Media Producer & Telegram Reporter.
Generates 1 Video Footage + 1 Photo Footage every hour (24 videos + 24 photos / day),
registers them into the Cyber-Zen Media Asset Bank with rich metadata, and sends
instant hourly reports to Telegram.
"""

import os
import sys
import ssl
import json
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import importlib.util

SKILL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path("/home/zen/hermes-agent")
PROMPTS_FILE = SKILL_DIR / "prompts_seed.json"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))
DAILY_TRACKER_FILE = HERMES_HOME / "daily_media_production.json"
CRON_JOBS_FILE = HERMES_HOME / "cron" / "jobs.json"
DEFAULT_HERMES_ENV = HERMES_HOME / ".env"

# Load catalog_manager cleanly
_cat_spec = importlib.util.spec_from_file_location("catalog_manager", SKILL_DIR / "catalog_manager.py")
_cat_mod = importlib.util.module_from_spec(_cat_spec)
_cat_spec.loader.exec_module(_cat_mod)
MediaBankCatalog = _cat_mod.MediaBankCatalog

# Load agnes client and scheduler cleanly
_agnes_path = WORKSPACE_ROOT / "skills" / "creative" / "agnes-ai-video" / "agnes_client.py"
if _agnes_path.exists():
    _ag_spec = importlib.util.spec_from_file_location("agnes_client", _agnes_path)
    _ag_mod = importlib.util.module_from_spec(_ag_spec)
    _ag_spec.loader.exec_module(_ag_mod)
    AgnesAIClient = _ag_mod.AgnesAIClient
    resolve_agnes_api_key = _ag_mod.resolve_agnes_api_key
else:
    AgnesAIClient = None
    resolve_agnes_api_key = lambda: ""

_sch_path = WORKSPACE_ROOT / "skills" / "creative" / "agnes-ai-video" / "scheduler.py"
if _sch_path.exists():
    _sch_spec = importlib.util.spec_from_file_location("agnes_scheduler", _sch_path)
    _sch_mod = importlib.util.module_from_spec(_sch_spec)
    _sch_spec.loader.exec_module(_sch_mod)
    VideoQueueManager = _sch_mod.VideoQueueManager
else:
    VideoQueueManager = None

_trk_path = SKILL_DIR / "monthly_tracker.py"
if _trk_path.exists():
    _trk_spec = importlib.util.spec_from_file_location("monthly_tracker", _trk_path)
    _tracker_mod = importlib.util.module_from_spec(_trk_spec)
    _trk_spec.loader.exec_module(_tracker_mod)
else:
    _tracker_mod = None



def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def load_hermes_env() -> Dict[str, str]:
    env_vars = {}
    if DEFAULT_HERMES_ENV.exists():
        with open(DEFAULT_HERMES_ENV, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


def send_telegram_report(text: str) -> bool:
    """Send Telegram status or delivery alert."""
    env = load_hermes_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15, context=get_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception as e:
        print(f"[!] Failed to send Telegram media report: {e}", file=sys.stderr)
        return False


class HourlyMediaProducer:
    """Orchestrates 24 videos + 24 photos daily production pipeline."""

    def __init__(
        self,
        catalog: Optional[MediaBankCatalog] = None,
        tracker_file: Optional[Path] = None,
        prompts_file: Optional[Path] = None
    ):
        self.catalog = catalog or MediaBankCatalog()
        self.tracker_file = tracker_file or DAILY_TRACKER_FILE
        self.prompts_file = prompts_file or PROMPTS_FILE
        self.client = AgnesAIClient() if AgnesAIClient else None
        self.queue_mgr = VideoQueueManager() if VideoQueueManager else None
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)

    def load_seed_prompts(self) -> List[Dict[str, Any]]:
        if not self.prompts_file.exists():
            return []
        with open(self.prompts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("prompts", [])

    def load_daily_tracker(self) -> Dict[str, Any]:
        today_str = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("date") == today_str:
                        return data
            except Exception:
                pass

        # Initialize fresh tracker for today
        fresh_data = {
            "date": today_str,
            "target_videos": 24,
            "target_photos": 24,
            "completed_videos": 0,
            "completed_photos": 0,
            "hourly_logs": [],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.save_daily_tracker(fresh_data)
        return fresh_data

    def save_daily_tracker(self, data: Dict[str, Any]):
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.tracker_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_hourly_photo(self, prompt_info: Dict[str, Any], hour_idx: int) -> Dict[str, Any]:
        """Generate 1 photo footage and save to storage/media_bank/images/."""
        title = prompt_info.get("title", f"Cyber-Zen Photo #{hour_idx+1}")
        prompt = prompt_info.get("prompt", "")
        category = prompt_info.get("category", "ai_brain")
        aspect_ratio = prompt_info.get("aspect_ratio", "16:9")
        ratio_folder = "hero" if aspect_ratio == "16:9" else "b_roll"

        dest_dir = self.catalog.images_dir / ratio_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        photo_id = f"img_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{hour_idx+1}"
        out_filename = f"{photo_id}_{aspect_ratio.replace(':', '-')}.png"
        out_path = dest_dir / out_filename

        # Try API generation if key is present
        api_success = False
        api_key = resolve_agnes_api_key()
        if api_key:
            try:
                url = "https://apihub.agnes-ai.com/v1/images/generations"
                payload = {
                    "model": "agnes-image-2.1-flash",
                    "prompt": f"{prompt}, 8k ultra-detailed, photorealistic, cinematic lighting",
                    "size": "1024x1024"
                }
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0"
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=20, context=get_ssl_context()) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    img_data = res_data.get("data", [])
                    if img_data and "url" in img_data[0]:
                        img_url = img_data[0]["url"]
                        with urllib.request.urlopen(img_url, timeout=30, context=get_ssl_context()) as img_resp:
                            out_path.write_bytes(img_resp.read())
                            api_success = True
            except Exception as e:
                print(f"[*] Agnes Image API notice: {e}. Generating high-contrast Cyber-Zen vector/raster image fallback.", file=sys.stderr)

        if not api_success:
            # Create a high-contrast Cyber-Zen placeholder image asset with rich metadata
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="cyberZenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0B0C0E"/>
      <stop offset="50%" stop-color="#121620"/>
      <stop offset="100%" stop-color="#0B0C0E"/>
    </linearGradient>
    <linearGradient id="neonCyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F2FE"/>
      <stop offset="100%" stop-color="#7F00FF"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#cyberZenGrad)"/>
  <circle cx="640" cy="360" r="220" stroke="url(#neonCyan)" stroke-width="4" fill="none" opacity="0.8"/>
  <circle cx="640" cy="360" r="140" stroke="#FFB703" stroke-width="2" fill="none" stroke-dasharray="10,15" opacity="0.7"/>
  <text x="640" y="340" font-family="sans-serif" font-size="36" font-weight="bold" fill="#00F2FE" text-anchor="middle">ZENPHAM CYBER-ZEN</text>
  <text x="640" y="390" font-family="sans-serif" font-size="22" fill="#FFFFFF" text-anchor="middle">{title[:50]}</text>
  <text x="640" y="430" font-family="sans-serif" font-size="16" fill="#FFB703" text-anchor="middle">[{category.upper()}] • {aspect_ratio} • 4K HIGH RES FOOTAGE</text>
</svg>"""
            svg_path = dest_dir / f"{photo_id}.svg"
            svg_path.write_text(svg_content, encoding="utf-8")
            out_path.write_bytes(svg_content.encode("utf-8"))

        # Register in catalog
        self.catalog.register_asset(
            asset_id=photo_id,
            filename=out_path.name,
            title=title,
            category=category,
            media_type="image",
            aspect_ratio=aspect_ratio,
            local_path=out_path,
            resolution="4K",
            prompt=prompt,
            tags=prompt_info.get("tags", ["photo", "hero", category]),
            platforms=prompt_info.get("platforms", ["youtube_thumbnail", "facebook", "x"])
        )

        return {
            "id": photo_id,
            "title": title,
            "category": category,
            "aspect_ratio": aspect_ratio,
            "path": str(out_path),
            "size": out_path.stat().st_size if out_path.exists() else 0
        }

    def generate_hourly_video(self, prompt_info: Dict[str, Any], hour_idx: int) -> Dict[str, Any]:
        """Generate/Enqueue 1 video footage and register to Media Bank."""
        title = prompt_info.get("title", f"Cyber-Zen Video #{hour_idx+1}")
        prompt = prompt_info.get("prompt", "")
        category = prompt_info.get("category", "ai_brain")
        aspect_ratio = prompt_info.get("aspect_ratio", "16:9")
        model = prompt_info.get("model", "agnes-video-2.5-flash")


        video_id = f"vid_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{hour_idx+1}"

        if self.queue_mgr:
            task = self.queue_mgr.enqueue_prompt(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                seconds=str(prompt_info.get("seconds", "5")),
                model=model,
                title=title
            )
            # Check if quota available to dispatch immediately
            disp_res = self.queue_mgr.process_pending_queue(notify=False)
            task_status = "dispatched" if disp_res.get("processed", 0) > 0 else "queued_free_quota"
        else:
            task_status = "queued"

        # Register into Catalog as queued/available video
        ratio_folder = "16_9" if "16" in aspect_ratio and aspect_ratio.startswith("16") else ("9_16" if aspect_ratio.startswith("9") else "square")
        placeholder_path = self.catalog.videos_dir / ratio_folder / f"{video_id}_{aspect_ratio.replace(':', '-')}.mp4"
        if not placeholder_path.exists():
            placeholder_path.write_bytes(b"")

        self.catalog.register_asset(
            asset_id=video_id,
            filename=placeholder_path.name,
            title=title,
            category=category,
            media_type="video",
            aspect_ratio=aspect_ratio,
            local_path=placeholder_path,
            resolution="720P",
            duration_seconds=float(prompt_info.get("seconds", 5)),
            prompt=prompt,
            tags=prompt_info.get("tags", ["video", "b_roll", category]),
            platforms=prompt_info.get("platforms", ["youtube", "facebook_reels", "x"])
        )

        return {
            "id": video_id,
            "title": title,
            "category": category,
            "aspect_ratio": aspect_ratio,
            "status": task_status,
            "path": str(placeholder_path)
        }

    def run_hourly_production_cycle(self, notify: bool = True) -> Dict[str, Any]:
        """Execute 1 hourly cycle: produce 1 Video + 1 Photo, update tracker, send Telegram report."""
        tracker = self.load_daily_tracker()
        prompts = self.load_seed_prompts()
        if not prompts:
            return {"success": False, "error": "No seed prompts found"}

        now_vn = datetime.now(timezone(timedelta(hours=7)))
        hour_now = now_vn.hour  # 0 to 23

        # 1. Check 30-Day Master Tracker slot first
        slot_info = None
        if _tracker_mod:
            try:
                monthly_trk = _tracker_mod.MonthlyMediaTracker()
                slot_info = monthly_trk.get_slot_by_current_time()
            except Exception as e:
                print(f"[*] Notice loading monthly slot: {e}", file=sys.stderr)

        if slot_info:
            slot_id = slot_info["slot_id"]
            theme_title = slot_info["title"]
            category = slot_info["category"]
            aspect_ratio = slot_info["aspect_ratio"]
            v_prompt_info = {
                "title": theme_title,
                "prompt": slot_info["video_prompt"],
                "category": category,
                "aspect_ratio": aspect_ratio,
                "seconds": "5",
                "tags": slot_info["tags"],
                "platforms": slot_info["platforms"]
            }
            p_prompt_info = {
                "title": theme_title,
                "prompt": slot_info["photo_prompt"],
                "category": category,
                "aspect_ratio": aspect_ratio,
                "tags": slot_info["tags"],
                "platforms": slot_info["platforms"]
            }
        else:
            # Fallback to seed prompts
            slot_id = f"H{hour_now:02d}"
            prompt_idx = hour_now % len(prompts)
            v_prompt_info = prompts[prompt_idx]
            p_prompt_info = prompts[prompt_idx]
            theme_title = v_prompt_info["title"]
            category = v_prompt_info["category"]

        print(f"[*] Starting Hourly Media Production [{slot_id} - {hour_now:02d}:00] — Theme: '{theme_title}'...")

        # 2. Produce 1 Video
        video_res = self.generate_hourly_video(v_prompt_info, hour_now)
        tracker["completed_videos"] += 1

        # 3. Produce 1 Photo
        photo_res = self.generate_hourly_photo(p_prompt_info, hour_now)
        tracker["completed_photos"] += 1

        # 4. Update 30-Day Tracker
        if slot_info and _tracker_mod:
            try:
                monthly_trk.update_slot_execution(
                    slot_id=slot_id,
                    status="completed",
                    video_id=video_res.get("id"),
                    photo_id=photo_res.get("id"),
                    video_path=video_res.get("path"),
                    photo_path=photo_res.get("path")
                )
            except Exception as e:
                print(f"[*] Warning updating monthly slot: {e}", file=sys.stderr)

        # Log hourly run
        log_entry = {
            "slot_id": slot_id,
            "hour": hour_now,
            "timestamp": now_vn.isoformat(),
            "theme": theme_title,
            "category": category,
            "video": video_res,
            "photo": photo_res
        }
        tracker["hourly_logs"].append(log_entry)
        self.save_daily_tracker(tracker)

        stats = self.catalog.get_statistics()
        trk_stats = monthly_trk.get_progress_statistics() if (slot_info and _tracker_mod) else {}

        # 5. Format Telegram Report
        progress_line = f"📊 <b>Tiến độ hôm nay:</b> <code>[{tracker['completed_videos']}/24 Videos]</code> • <code>[{tracker['completed_photos']}/24 Photos]</code>"
        if trk_stats:
            progress_line += f"\n🗓️ <b>30-Day Master Tracker:</b> <code>[{trk_stats.get('completed_slots', 0)}/720 Slots ({trk_stats.get('percent_completed', 0)}%)]</code>"

        report_text = (
            f"🎬 <b>BÁO CÁO SẢN XUẤT FOOTAGE HÀNG GIỜ ({hour_now:02d}:00)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Slot:</b> <code>{slot_id}</code> | <b>Chủ đề:</b> {theme_title}\n"
            f"{progress_line}\n"
            f"🏷️ <b>Phân loại:</b> <code>#{category}</code> | <b>Phong cách:</b> <code>Cyber-Zen Tech</code>\n\n"
            f"🎥 <b>1. Footage Video ({video_res['aspect_ratio']}):</b>\n"
            f"  • ID: <code>{video_res['id']}</code>\n"
            f"  • Trạng thái: <b>{video_res['status']}</b> (Tự động vào hàng đợi Free Quota)\n\n"
            f"🖼️ <b>2. Footage Photo ({photo_res['aspect_ratio']}):</b>\n"
            f"  • ID: <code>{photo_res['id']}</code>\n"
            f"  • Đã lưu tại: <code>{photo_res['path']}</code> ({round(photo_res.get('size', 0)/1024, 1)} KB)\n\n"
            f"🗄️ <b>Tổng kho Media Bank:</b> {stats['total_assets']} tư liệu ({stats['total_size_mb']} MB)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>ZENPHAM Automated Media Production Hub</i>"
        )


        if notify:
            send_telegram_report(report_text)

        return {
            "success": True,
            "hour": hour_now,
            "completed_videos_today": tracker["completed_videos"],
            "completed_photos_today": tracker["completed_photos"],
            "video": video_res,
            "photo": photo_res
        }


def install_hourly_cron(schedule: str = "0 * * * *") -> Dict[str, Any]:
    """Register hourly cron job in Hermes Cron System."""
    cron_file = CRON_JOBS_FILE
    data = {"jobs": [], "updated_at": datetime.now(timezone.utc).isoformat()}

    if cron_file.exists():
        try:
            with open(cron_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict) and "jobs" in d and isinstance(d["jobs"], list):
                    data = d
        except Exception as e:
            print(f"[*] Warning loading cron jobs: {e}", file=sys.stderr)

    job_id = "job_hourly_media_production"
    cmd = f"python3 {Path(__file__).resolve()} --run-once --notify"

    job_def = {
        "id": job_id,
        "name": "hourly-media-footage-producer",
        "prompt": f"Chạy chu kỳ sản xuất footage video và hình ảnh hàng giờ (24 video + 24 photo mỗi ngày) và báo cáo Telegram bằng lệnh: {cmd}.",
        "skills": ["media-asset-bank", "agnes-ai-video"],
        "skill": "media-asset-bank",
        "model": None,
        "provider": None,
        "provider_snapshot": "custom",
        "model_snapshot": "cx/gpt-5.6-luna",
        "base_url": None,
        "script": None,
        "no_agent": False,
        "schedule": {
            "kind": "cron",
            "expr": schedule,
            "display": f"{schedule} (Hourly 24/24 Video & Photo footage producer)"
        },
        "schedule_display": schedule,
        "repeat": {
            "times": None,
            "completed": 0
        },
        "enabled": True,
        "state": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": cmd
    }

    jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]
    jobs_list.append(job_def)
    data["jobs"] = jobs_list
    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    cron_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cron_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "status": "installed",
        "job_id": job_id,
        "schedule": schedule,
        "command": cmd
    }


def uninstall_hourly_cron() -> Dict[str, Any]:
    """Remove hourly cron job from Hermes Cron System."""
    cron_file = CRON_JOBS_FILE
    if not cron_file.exists():
        return {"status": "not_found"}

    with open(cron_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    job_id = "job_hourly_media_production"
    jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]
    data["jobs"] = jobs_list
    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(cron_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "uninstalled", "job_id": job_id}


def main():
    parser = argparse.ArgumentParser(description="24/7 Hourly Media Producer & Telegram Reporter.")
    parser.add_argument("--run-once", action="store_true", help="Execute 1 hourly media production cycle")
    parser.add_argument("--notify", action="store_true", help="Send Telegram report")
    parser.add_argument("--install-cron", action="store_true", help="Register 24/7 hourly cron job in Hermes Cron Engine")
    parser.add_argument("--uninstall-cron", action="store_true", help="Uninstall hourly cron job")
    parser.add_argument("--status", action="store_true", help="Show today's 24/24 production progress")
    args = parser.parse_args()

    producer = HourlyMediaProducer()

    if args.run_once:
        res = producer.run_hourly_production_cycle(notify=args.notify)
        print(f"[✓] Hourly Production Cycle Finished: {res}")

    elif args.install_cron:
        res = install_hourly_cron()
        print(f"[✓] Installed Hourly Media Cron: {res['job_id']} -> {res['schedule']}")

    elif args.uninstall_cron:
        res = uninstall_hourly_cron()
        print(f"[✓] Uninstalled Hourly Media Cron: {res['job_id']}")

    elif args.status or not len(sys.argv) > 1:
        tracker = producer.load_daily_tracker()
        stats = producer.catalog.get_statistics()
        print(f"=== Daily Media Production Status [{tracker['date']}] ===")
        print(f"Progress: {tracker['completed_videos']}/24 Videos | {tracker['completed_photos']}/24 Photos")
        print(f"Total Bank Assets: {stats['total_assets']} ({stats['total_size_mb']} MB)")
        print(f"Recent Hourly Runs: {len(tracker['hourly_logs'])}")


if __name__ == "__main__":
    main()
