#!/usr/bin/env python3
"""
Agnes AI Video Free Quota Scheduler & Queue Manager.
Queues video prompts, monitors free quota replenishment, dispatches generation jobs,
downloads completed MP4 videos, and sends Telegram alerts.
"""

import os
import sys
import ssl
import json
import time
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import importlib.util

SKILL_DIR = Path(__file__).resolve().parent
_client_path = SKILL_DIR / "agnes_client.py"
_spec = importlib.util.spec_from_file_location("agnes_client", _client_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

AgnesAIClient = _mod.AgnesAIClient
resolve_agnes_api_key = _mod.resolve_agnes_api_key


HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))
DEFAULT_QUEUE_FILE = HERMES_HOME / "agnes_video_queue.json"
DEFAULT_OUTPUT_DIR = Path("/home/zen/hermes-agent/output_videos")
CRON_JOBS_FILE = HERMES_HOME / "cron" / "jobs.json"
DEFAULT_HERMES_ENV = HERMES_HOME / ".env"


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


def send_telegram_notification(text: str) -> bool:
    """Send Telegram status or delivery alert."""
    env = load_hermes_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "8809083341:AAHZw_PHdxmtZjns-8xfJahvYVz4AqTdclg")
    chat_id = env.get("TELEGRAM_ALLOWED_USERS", "1431349185")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
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
        print(f"[!] Failed to send Telegram video alert: {e}", file=sys.stderr)
        return False


class VideoQueueManager:
    """Manages persistent queue of video generation tasks."""

    def __init__(self, queue_file: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.queue_file = queue_file or DEFAULT_QUEUE_FILE
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_queue(self) -> Dict[str, Any]:
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[*] Warning loading queue: {e}", file=sys.stderr)
        return {"tasks": [], "updated_at": datetime.now(timezone.utc).isoformat()}

    def save_queue(self, data: Dict[str, Any]):
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def enqueue_prompt(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        seconds: str = "5",
        model: str = "agnes-video-2.5",
        mode: str = "text",
        size: str = "720P",
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new prompt to pending video queue."""
        data = self.load_queue()
        task_id = f"task_{int(time.time())}_{len(data['tasks'])+1}"
        item = {
            "id": task_id,
            "title": title or prompt[:50],
            "prompt": prompt,
            "model": model,
            "mode": mode,
            "seconds": str(seconds),
            "size": size,
            "aspect_ratio": aspect_ratio,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "agnes_task_id": None,
            "video_url": None,
            "local_path": None,
            "error": None
        }
        data["tasks"].append(item)
        self.save_queue(data)
        return item

    def process_pending_queue(self, notify: bool = True) -> Dict[str, Any]:
        """Attempt to dispatch pending tasks across all available API keys in round-robin."""
        keys = _mod.get_all_agnes_keys()
        if not keys:
            print("[*] No Agnes API keys found in pool.", file=sys.stderr)
            return {"processed": 0, "status": "no_keys"}

        data = self.load_queue()
        pending = [t for t in data["tasks"] if t["status"] == "pending"]

        if not pending:
            print("[*] No pending video tasks in queue.")
            return {"processed": 0, "status": "empty"}

        processed_count = 0
        quota_exceeded = False
        active_key_idx = 0

        for task in pending:
            task_dispatched = False

            # Try available keys
            for attempt in range(len(keys)):
                curr_key = keys[(active_key_idx + attempt) % len(keys)]
                client = AgnesAIClient(api_key=curr_key)

                print(f"[*] Submitting task '{task['title']}' using Key [{(active_key_idx + attempt) % len(keys) + 1}/{len(keys)}]...")
                res = client.create_video_task(
                    prompt=task["prompt"],
                    model=task.get("model", "agnes-video-2.5-flash"),
                    mode=task.get("mode", "text"),
                    seconds=task.get("seconds", "5"),
                    size=task.get("size", "720P"),
                    aspect_ratio=task.get("aspect_ratio", "16:9")
                )

                if res["success"]:
                    task["status"] = "in_progress"
                    task["agnes_task_id"] = res["task_id"]
                    task["dispatched_at"] = datetime.now(timezone.utc).isoformat()
                    self.save_queue(data)
                    processed_count += 1
                    active_key_idx = (active_key_idx + attempt + 1) % len(keys)
                    task_dispatched = True
                    print(f"  [✓] Dispatched to Agnes AI! Task ID: {res['task_id']}")

                    # Poll and download
                    out_filename = f"{task['id']}_{task.get('aspect_ratio', '16-9').replace(':', '-')}.mp4"
                    out_path = self.output_dir / out_filename
                    poll_res = client.poll_and_download(res["task_id"], out_path, timeout=300, interval=8)

                    if poll_res["success"]:
                        task["status"] = "completed"
                        task["local_path"] = poll_res["file_path"]
                        task["video_url"] = poll_res.get("video_url")
                        task["completed_at"] = datetime.now(timezone.utc).isoformat()
                        self.save_queue(data)

                        if notify:
                            tg_text = (
                                f"🎬 <b>VIDEO AI ĐÃ TẠO THÀNH CÔNG!</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"📌 <b>Tiêu đề:</b> {task['title']}\n"
                                f"🤖 <b>Model:</b> <code>{task.get('model', 'agnes-video-2.5-flash')}</code>\n"
                                f"📐 <b>Tỷ lệ:</b> {task.get('aspect_ratio')} | ⏱️ <b>Thời lượng:</b> {task.get('seconds')}s\n"
                                f"💾 <b>Lưu tại:</b> <code>{poll_res['file_path']}</code>\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"✨ <i>Agnes AI Video Free Quota Scheduler</i>"
                            )
                            send_telegram_notification(tg_text)
                    else:
                        task["status"] = "failed"
                        task["error"] = poll_res.get("error")
                        self.save_queue(data)
                    break
                else:
                    err_msg = res.get("error_message", "Unknown error")
                    err_code = str(res.get("error_code", "")).lower()
                    msg_lower = str(err_msg).lower()
                    print(f"  [!] Key failed with: {err_msg}. Switching to next key...")

            if not task_dispatched:
                quota_exceeded = True
                print("  [*] All keys in pool currently busy or rate-limited. Retaining task in queue.")
                break


        return {
            "processed": processed_count,
            "quota_exceeded": quota_exceeded,
            "remaining_pending": len([t for t in data["tasks"] if t["status"] == "pending"])
        }



def install_video_cron(schedule: str = "0 8,20 * * *") -> Dict[str, Any]:
    """Register cron job in Hermes Cron System to auto-check and process video queue."""
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

    job_id = "job_agnes_video_free_quota"
    cmd = f"python3 {Path(__file__).resolve()} --process-queue --notify"

    job_def = {
        "id": job_id,
        "name": "agnes-video-free-quota-scheduler",
        "prompt": f"Tự động kiểm tra hạn mức Free Quota và chạy tạo video trong hàng đợi bằng lệnh: {cmd}. Tải video MP4 về kho lưu trữ và gửi thông báo hoàn thành qua Telegram.",
        "skills": ["agnes-ai-video", "media-studio"],
        "skill": "agnes-ai-video",
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
            "display": f"{schedule} (Daily free quota video creator)"
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


def main():
    parser = argparse.ArgumentParser(description="Agnes AI Video Free Quota Scheduler & Queue Manager.")
    parser.add_argument("--enqueue", help="Prompt to add to pending video generation queue")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16", "1:1", "4:3", "21:9"], help="Video aspect ratio (default: 16:9)")
    parser.add_argument("--seconds", default="5", help="Video duration in seconds (default: 5)")
    parser.add_argument("--model", default="agnes-video-2.5", help="Model name (default: agnes-video-2.5)")
    parser.add_argument("--list-queue", action="store_true", help="List all video generation tasks in queue")
    parser.add_argument("--process-queue", action="store_true", help="Process pending tasks with available quota")
    parser.add_argument("--notify", action="store_true", help="Send Telegram notifications on completion")
    parser.add_argument("--install-cron", action="store_true", help="Register cron job in Hermes Cron Engine")
    parser.add_argument("--schedule", default="0 8,20 * * *", help="Cron schedule expression (default: 0 8,20 * * *)")
    parser.add_argument("--status", action="store_true", help="Show Agnes AI connection and quota status")
    args = parser.parse_args()

    qm = VideoQueueManager()

    if args.enqueue:
        task = qm.enqueue_prompt(
            prompt=args.enqueue,
            aspect_ratio=args.aspect_ratio,
            seconds=args.seconds,
            model=args.model
        )
        print(f"[✓] Successfully queued video task: {task['id']} ('{task['title']}')")

    elif args.process_queue:
        res = qm.process_pending_queue(notify=args.notify)
        print(f"=== Queue Processing Result: {res} ===")

    elif args.list_queue:
        data = qm.load_queue()
        print(f"=== Agnes AI Video Queue ({len(data['tasks'])} tasks) ===")
        for t in data["tasks"]:
            print(f" - [{t['status'].upper()}] {t['id']}: {t['prompt'][:60]} (Ratio: {t.get('aspect_ratio')}, Secs: {t.get('seconds')})")

    elif args.install_cron:
        res = install_video_cron(schedule=args.schedule)
        print(f"[✓] Installed Agnes AI video cron job: {res['job_id']} -> {res['schedule']}")

    elif args.status or not len(sys.argv) > 1:
        client = AgnesAIClient()
        q_info = client.check_quota()
        data = qm.load_queue()
        pending = len([t for t in data["tasks"] if t["status"] == "pending"])
        completed = len([t for t in data["tasks"] if t["status"] == "completed"])
        
        print("=== Agnes AI Video Generation & Quota Status ===")
        print(f"Authenticated: {q_info.get('authenticated')}")
        print(f"API Key: {q_info.get('api_key_masked')}")
        print(f"Video Models: {q_info.get('video_models')}")
        print(f"Queue Status: {pending} Pending | {completed} Completed | Total: {len(data['tasks'])}")


if __name__ == "__main__":
    main()
