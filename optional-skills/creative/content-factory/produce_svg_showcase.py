#!/usr/bin/env python3
"""
Produce & Publish: High-Quality SVG Motion Animation Showcase Video for YouTube & Telegram.
Demonstrates 5 dynamic SVG vector animation scenes with OmniVoice Voice Clone.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path.home() / "workspace" / "output" / "factory"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STUDIO_DIR = Path(__file__).parent.parent / "video-motion-studio"
sys.path.insert(0, str(STUDIO_DIR))
from motion_studio import VideoMotionStudio

HERMES_ENV_PATH = Path.home() / ".hermes" / ".env"


def load_env():
    env = {}
    if HERMES_ENV_PATH.exists():
        with open(HERMES_ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


SHOWCASE_SCENES = [
    {
        "id": 1,
        "type": "architecture-flow",
        "title": "KIẾN TRÚC LUỒNG DỮ LIỆU ĐA TÁC VỤ",
        "voiceover": "Chào mừng bạn đến với Video Motion Studio. Đầu tiên là kiến trúc luồng dữ liệu tự hành kết nối giữa Telegram, Agent Core, Sandbox LXD và Trae IDE.",
        "duration": 12
    },
    {
        "id": 2,
        "type": "security-shield",
        "title": "HÀNG RÀO BẢO MẬT ZERO-TRUST",
        "voiceover": "Thứ hai, hệ thống lá chắn mật mã đa tầng bảo vệ an toàn tuyệt đối cho Secret Vault và các khóa API nhạy cảm của người dùng.",
        "duration": 11
    },
    {
        "id": 3,
        "type": "neural-network",
        "title": "MẠNG NƠ-RON SUY LUẬN TỰ CHỦ",
        "voiceover": "Thứ ba, mô hình mạng nơ-ron suy luận sâu, truyền xung tín hiệu liên tục để tự động giải quyết các bài toán kỹ thuật phức tạp.",
        "duration": 12
    },
    {
        "id": 4,
        "type": "vibe-coding",
        "title": "VIBE CODING & MISSION CONTROL REALTIME",
        "voiceover": "Thứ tư, giao diện lập trình Vibe Coding tự động mở terminal, gõ code, chạy bài kiểm thử và tạo bản git commit chỉ qua một tin nhắn.",
        "duration": 13
    },
    {
        "id": 5,
        "type": "cyber-hud",
        "title": "HỆ THỐNG ĐIỀU KHIỂN TELEMETRY HUD",
        "voiceover": "Và cuối cùng, bảng điều khiển Telemetry đo lường hiệu năng thời gian thực, đảm bảo hệ thống vận hành với độ trễ dưới một mili-giây.",
        "duration": 12
    }
]


def get_voice_clone_reference(voice_name: str = "tuan anh - deep & powerful vietnamese") -> tuple:
    ref_audio_url = ""
    ref_text = ""
    try:
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url="http://10.123.214.249:9000",
            aws_access_key_id="omnivoice-svc",
            aws_secret_access_key="omnivoice_svc_2026"
        )
        res = s3.list_objects_v2(Bucket="omnivoice-audio", Prefix="voices/")
        contents = res.get("Contents", [])
        target_key = None
        target_txt_key = None

        for item in contents:
            key = item["Key"]
            if voice_name.lower() in key.lower():
                if key.endswith((".mp3", ".wav", ".m4a", ".ogg")):
                    target_key = key
                elif key.endswith(".txt"):
                    target_txt_key = key

        if target_key:
            ref_audio_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": "omnivoice-audio", "Key": target_key},
                ExpiresIn=3600
            )
        if target_txt_key:
            ref_text = s3.get_object(Bucket="omnivoice-audio", Key=target_txt_key)["Body"].read().decode("utf-8").strip()
    except Exception as e:
        print(f"[*] S3 voice ref lookup warning: {e}", file=sys.stderr)

    return ref_audio_url, ref_text


def synthesize_audio(text: str, out_p: Path, dur: int) -> bool:
    try:
        ref_audio_url, ref_text = get_voice_clone_reference()
        payload = {
            "text": text,
            "lang": "vi",
            "normalize_vi": True,
            "ref_audio": ref_audio_url,
            "ref_text": ref_text,
            "speed": 1.0
        }
        req = urllib.request.Request(
            "http://10.123.214.178/tts/omnivoice",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            with open(out_p, "wb") as f:
                f.write(resp.read())
            if out_p.exists() and out_p.stat().st_size > 2000:
                return True
    except Exception as e:
        print(f"[*] OmniVoice error: {e}, falling back to edge-tts...", file=sys.stderr)

    try:
        res = subprocess.run([
            "edge-tts",
            "--text", text,
            "--write-media", str(out_p),
            "--voice", "vi-VN-HoaiMyNeural"
        ], capture_output=True, timeout=30)
        return res.returncode == 0 and out_p.exists()
    except Exception:
        return False


def main():
    studio = VideoMotionStudio()
    scene_video_files = []

    print("[*] Starting SVG Animation Showcase Production...")

    for sc in SHOWCASE_SCENES:
        s_id = sc["id"]
        print(f"\n[*] Rendering SVG Scene {s_id}/5: {sc['title']} ({sc['type']})...")
        
        audio_file = OUTPUT_DIR / f"svg_showcase_audio_{s_id}.wav"
        scene_mp4 = OUTPUT_DIR / f"svg_showcase_scene_{s_id}.mp4"

        # 1. Synthesize Voiceover
        print("  • Synthesizing Voice Clone audio...")
        synthesize_audio(sc["voiceover"], audio_file, sc["duration"])

        # 2. Render SVG Animation Scene with Audio
        print(f"  • Generating SVG Vector Motion ({sc['type']})...")
        ok = studio.render_svg_scene_with_audio(
            animation_type=sc["type"],
            audio_path=audio_file,
            output_path=scene_mp4,
            title=f"⚡ {sc['title']}"
        )
        if ok and scene_mp4.exists():
            print(f"  [✓] Scene {s_id} rendered: {scene_mp4} ({scene_mp4.stat().st_size // 1024} KB)")
            scene_video_files.append(scene_mp4)

    # Concatenate all 5 scenes
    print("\n[*] Concatenating Full SVG Showcase Video...")
    concat_list_file = OUTPUT_DIR / "svg_concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for vf in scene_video_files:
            f.write(f"file '{vf}'\n")

    final_video = OUTPUT_DIR / "svg_motion_showcase_final.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(final_video)
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)
    print(f"[✓] Full Showcase Video Created: {final_video} ({final_video.stat().st_size // 1024} KB)")

    # Produce Thumbnail
    thumb_path = OUTPUT_DIR / "svg_motion_showcase_thumb.jpg"
    studio.generate_tech_infographic(
        title="SVG VECTOR MOTION ENGINE 2026",
        subtitle="5 Đột Phá Animation Đồ Họa Vector Cho AI Agent",
        nodes=[
            {"title": "Flow Pipeline", "desc": "Data packet flow", "badge": "SCENE 1"},
            {"title": "Zero-Trust", "desc": "Cryptographic shield", "badge": "SCENE 2"},
            {"title": "Neural Graph", "desc": "Synapse pulse firing", "badge": "SCENE 3"},
            {"title": "Vibe Coding", "desc": "Live IDE simulation", "badge": "SCENE 4"}
        ],
        output_path=thumb_path
    )
    print(f"[✓] Custom Thumbnail Created: {thumb_path}")


if __name__ == "__main__":
    main()
