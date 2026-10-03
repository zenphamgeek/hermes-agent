#!/usr/bin/env python3
"""
scripts/dispatch_live_avatar.py
================================
Unified CLI runner for generating Live Avatars using Wan 2.2 S2V on Modal Cloud & 9Router.
Uses presets from config/live_avatar_config.json.

Usage:
  python3 scripts/dispatch_live_avatar.py \
      --preset vietnam_culture_female_refined \
      --image output/qwen_asian_girl_aodai_master_1024x1536.png \
      --audio output/female_doan_trang_5s.wav \
      --output output/my_live_avatar.mp4
"""

import os
import sys
import json
import time
import base64
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "live_avatar_config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calibrate_audio(input_wav: str, output_wav: str, headroom_db: float = -1.5) -> str:
    """Standardizes input audio to 48kHz mono PCM with calibrated headroom to avoid mouth twitching."""
    os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", input_wav,
        "-filter:a", f"volume={headroom_db}dB",
        "-ar", "48000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_wav
    ]
    print(f"🎵 Calibrating audio: {input_wav} -> {output_wav} ({headroom_db}dB, 48kHz mono)...")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode != 0:
        print("⚠️ Warning: FFmpeg calibration had non-zero exit, falling back to original audio.")
        return input_wav
    return output_wav


def submit_job(api_base: str, payload: dict) -> dict:
    url = f"{api_base}/v1/jobs/generate"
    req_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "Hermes-LiveAvatar-Dispatcher/1.0"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_job_events(api_base: str, job_id: str, max_wait_seconds: int = 7200):
    status_url = f"{api_base}/v1/jobs/{job_id}"
    print(f"\n📡 [Hermes Cloud GPU Stream] Listening on: {status_url}")
    print("-------------------------------------------------------------------")

    last_step = -1
    last_status = None
    t0 = time.time()

    while time.time() - t0 < max_wait_seconds:
        try:
            req = urllib.request.Request(status_url, headers={"User-Agent": "Hermes-LiveAvatar-Dispatcher/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            status = data.get("status")
            step = data.get("step", 0)
            tot_step = data.get("total_steps", 35)
            progress = data.get("progress", 0.0)
            msg = data.get("message", "")
            speed = data.get("speed", "")
            rem = data.get("remaining", "")

            if step != last_step or status != last_status:
                last_step = step
                last_status = status
                timestamp = time.strftime("%H:%M:%S")
                if status == "running":
                    print(f"[{timestamp}] ⚡ [GPU EVENT] Step {step}/{tot_step} ({progress:.1f}%) | Speed: {speed} | ETA: {rem}")
                elif status == "completed":
                    print(f"[{timestamp}] 🎉 [GPU COMPLETED] Render finished in {data.get('duration_seconds', 0)}s!")
                    return data
                elif status == "failed":
                    print(f"[{timestamp}] ❌ [GPU FAILED] {data.get('error', 'Unknown error')}")
                    return data
                else:
                    print(f"[{timestamp}] ⏳ [GPU {status.upper()}] {msg}")

        except Exception as e:
            print(f"[Notice] Network blip ({e}), continuing heartbeat...")

        time.sleep(3.0)

    raise TimeoutError(f"Job {job_id} timed out after {max_wait_seconds}s")


def download_video(api_base: str, job_id: str, target_file: str):
    download_url = f"{api_base}/v1/jobs/{job_id}/download"
    print(f"\n📥 Downloading master video to {target_file}...")
    req = urllib.request.Request(download_url, headers={"User-Agent": "Hermes-LiveAvatar-Dispatcher/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        video_bytes = resp.read()

    os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
    with open(target_file, "wb") as f:
        f.write(video_bytes)

    mb = len(video_bytes) / (1024 * 1024)
    print(f" [✓] Delivered: {target_file} ({mb:.2f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Hermes Live Avatar Dispatcher")
    parser.add_argument("--preset", default="vietnam_culture_female_refined", help="Preset from config")
    parser.add_argument("--image", required=True, help="Input portrait image path")
    parser.add_argument("--audio", required=True, help="Input voice audio path (.wav)")
    parser.add_argument("--output", required=True, help="Output master video path (.mp4)")
    parser.add_argument("--prompt", default=None, help="Override prompt")
    parser.add_argument("--negative-prompt", default=None, help="Override negative prompt")
    parser.add_argument("--cfg", type=float, default=None, help="Override guide_scale (default 3.6)")
    parser.add_argument("--steps", type=int, default=None, help="Override sampling steps")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without sending")

    args = parser.parse_args()
    config = load_config()

    presets = config.get("presets", {})
    if args.preset not in presets:
        print(f"Error: Preset '{args.preset}' not found. Available presets: {list(presets.keys())}")
        sys.exit(1)

    p_conf = presets[args.preset]
    service_conf = config.get("routing", {}).get("services", {}).get("modal_s2v_api", {})
    api_base = service_conf.get("base_url", "https://zenonmind--hermes-wan-s2v-api.modal.run")

    if not os.path.exists(args.image):
        print(f"Error: Image '{args.image}' not found.")
        sys.exit(1)
    if not os.path.exists(args.audio):
        print(f"Error: Audio '{args.audio}' not found.")
        sys.exit(1)

    # 1. Calibrate audio with -1.5dB headroom
    calibrated_audio = f"/tmp/calibrated_{os.path.basename(args.audio)}"
    final_audio = calibrate_audio(args.audio, calibrated_audio, headroom_db=config.get("audio_calibration", {}).get("volume_adjustment_db", -1.5))

    # 2. Encode assets to base64
    with open(args.image, "rb") as f:
        img_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    with open(final_audio, "rb") as f:
        audio_b64 = "data:audio/wav;base64," + base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "image": img_b64,
        "audio": audio_b64,
        "template": p_conf.get("template", "shorts_vertical"),
        "size": p_conf.get("size", "704*1024"),
        "sample_steps": args.steps or p_conf.get("sample_steps", 35),
        "guide_scale": args.cfg or p_conf.get("guide_scale", 3.6),
        "seed": args.seed or p_conf.get("seed", 42),
        "prompt": args.prompt or p_conf.get("prompt", ""),
        "negative_prompt": args.negative_prompt or p_conf.get("negative_prompt", ""),
        "upscale_1080p": p_conf.get("upscale_1080p", True),
        "num_clip": 1,
    }

    if args.dry_run:
        print("\n[Dry Run] Prepared payload:")
        summary = {k: (v if k not in ("image", "audio") else f"Base64 ({len(v)} chars)") for k, v in payload.items()}
        print(json.dumps(summary, indent=2))
        return

    print("===================================================================")
    print(f" 🚀 DISPATCHING LIVE AVATAR: Preset '{args.preset}'")
    print(f" Target Engine: Modal Cloud A100-80GB (0% Local GPU)")
    print(f" CFG: {payload['guide_scale']} (Mouth dampening) | Steps: {payload['sample_steps']}")
    print("===================================================================")

    resp = submit_job(api_base, payload)
    job_id = resp["job_id"]
    print(f"[✓] Job Accepted: {job_id}")

    result = poll_job_events(api_base, job_id)
    if result.get("status") == "completed":
        download_video(api_base, job_id, args.output)
        print("\n===================================================================")
        print(f" 🎉 SUCCESS! Master video saved: {args.output}")
        print("===================================================================")
    else:
        print(f"❌ Failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
