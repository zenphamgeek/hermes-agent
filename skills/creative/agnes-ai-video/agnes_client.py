#!/usr/bin/env python3
"""
Agnes AI Video & Image Generation API Client.
Connects to https://apihub.agnes-ai.com/v1 with support for text-to-video,
image-to-video, task polling, and automatic video downloading.
"""

import os
import sys
import ssl
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))
ENV_FILE = HERMES_HOME / ".env"
WORKSPACE_ENV = Path("/home/zen/hermes-agent/.env")


def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_all_agnes_keys() -> List[str]:
    """Retrieve all available Agnes AI API keys from env and .env files."""
    keys = []
    for env_k in ["AGNES_AI_API_KEY", "AGNES_AI_API_KEY_2", "AGNES_AI_API_KEY_1", "AGNES_API_KEY"]:
        v = os.environ.get(env_k)
        if v and v not in keys:
            keys.append(v)

    for env_path in [ENV_FILE, WORKSPACE_ENV]:
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k_clean = k.strip()
                        if k_clean.startswith("AGNES_AI_API_KEY") or k_clean == "AGNES_API_KEY":
                            val = v.strip()
                            if val and val not in keys:
                                keys.append(val)
    return keys


def resolve_agnes_api_key(prefer_key2: bool = False) -> str:
    """Resolve AGNES_AI_API_KEY from environment or .env files."""
    all_keys = get_all_agnes_keys()
    if not all_keys:
        return ""
    if prefer_key2 and len(all_keys) > 1:
        return all_keys[1]
    return all_keys[0]



class AgnesAIClient:
    """Official API Client for Agnes AI (apihub.agnes-ai.com)."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key or resolve_agnes_api_key()
        self.base_url = base_url.rstrip("/")

        if not self.api_key:
            print("[*] Warning: AGNES_AI_API_KEY not found in environment or ~/.hermes/.env", file=sys.stderr)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "HermesAgent/1.0",
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """List all supported models from Agnes AI."""
        url = f"{self.base_url}/models"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=12, context=get_ssl_context()) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("data", [])
        except Exception as e:
            print(f"[!] Error listing Agnes models: {e}", file=sys.stderr)
            return []

    def check_quota(self) -> Dict[str, Any]:
        """Check user quota and account status by probing models and endpoints."""
        models = self.list_models()
        if not models:
            return {
                "authenticated": False,
                "error": "Authentication failed or network error"
            }

        video_models = [m["id"] for m in models if "video" in m["id"]]
        image_models = [m["id"] for m in models if "image" in m["id"]]

        return {
            "authenticated": True,
            "api_key_masked": f"{self.api_key[:6]}...{self.api_key[-4:]}" if len(self.api_key) > 10 else "N/A",
            "total_models": len(models),
            "video_models": video_models,
            "image_models": image_models,
            "supported_ratios": ["16:9", "9:16", "1:1", "4:3", "21:9"],
            "default_model": "agnes-video-2.5"
        }

    def create_video_task(
        self,
        prompt: str,
        model: str = "agnes-video-2.5-flash",
        mode: str = "text",
        seconds: str = "5",
        size: str = "720P",
        aspect_ratio: str = "16:9",
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new video generation task.
        Returns response containing task ID / video_id.
        """
        url = f"{self.base_url}/videos"
        payload = {
            "model": model,
            "prompt": prompt,
            "mode": mode,
            "seconds": str(seconds),
            "size": size,
            "aspect_ratio": aspect_ratio
        }
        if image_url and mode == "image":
            payload["image_url"] = image_url

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30, context=get_ssl_context()) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {
                    "success": True,
                    "task_id": result.get("id") or result.get("video_id") or result.get("task_id"),
                    "raw_response": result
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(body)
                msg = err_json.get("message") or err_json.get("error", {}).get("message") or body
                code = err_json.get("code") or err_json.get("error", {}).get("code") or "HTTP_ERROR"
            except Exception:
                msg = body
                code = f"HTTP_{e.code}"
            return {
                "success": False,
                "error_code": code,
                "error_message": msg,
                "status_code": e.code
            }
        except Exception as e:
            return {
                "success": False,
                "error_code": "EXCEPTION",
                "error_message": str(e)
            }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Poll task status using /v1/videos/{task_id} or /v1/agnesapi."""
        urls_to_try = [
            f"{self.base_url}/videos/{urllib.parse.quote(task_id)}",
            f"{self.base_url}/agnesapi?video_id={urllib.parse.quote(task_id)}"
        ]

        last_error = None
        for url in urls_to_try:
            req = urllib.request.Request(url, headers=self._headers(), method="GET")
            try:
                with urllib.request.urlopen(req, timeout=15, context=get_ssl_context()) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    status = result.get("status") or result.get("state") or "unknown"
                    raw_meta = result.get("metadata") or {}
                    video_url = (
                        result.get("video_url")
                        or result.get("url")
                        or result.get("download_url")
                        or raw_meta.get("url")
                        or (result.get("data") or {}).get("url")
                    )
                    return {
                        "task_id": task_id,
                        "status": status,
                        "progress": result.get("progress", 0),
                        "video_url": video_url,
                        "raw_response": result
                    }

            except Exception as e:
                last_error = e
                continue

        return {
            "task_id": task_id,
            "status": "error",
            "error": str(last_error) if last_error else "Unknown polling error"
        }


    def poll_and_download(
        self,
        task_id: str,
        output_file: Path,
        timeout: int = 600,
        interval: int = 10
    ) -> Dict[str, Any]:
        """Poll task status until completion and download final MP4 video."""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        print(f"[*] Polling Agnes AI video task {task_id} (timeout={timeout}s)...")
        while time.time() - start_time < timeout:
            status_info = self.get_task_status(task_id)
            state = status_info.get("status", "").lower()
            print(f"  [Task {task_id}] Status: {state} (Progress: {status_info.get('progress', 'N/A')}%)")

            if state in ("success", "completed", "done"):
                video_url = status_info.get("video_url")
                if video_url:
                    print(f"[*] Downloading generated video from {video_url}...")
                    req = urllib.request.Request(video_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=60, context=get_ssl_context()) as resp:
                        content = resp.read()
                        with open(output_file, "wb") as f:
                            f.write(content)
                    return {
                        "success": True,
                        "file_path": str(output_file),
                        "file_size": len(content),
                        "video_url": video_url
                    }
                else:
                    return {"success": False, "error": "Task marked success but no video_url returned"}

            elif state in ("failed", "error", "cancelled"):
                return {
                    "success": False,
                    "error": f"Task failed with state: {state}",
                    "details": status_info
                }

            time.sleep(interval)

        return {"success": False, "error": f"Polling timed out after {timeout} seconds"}
