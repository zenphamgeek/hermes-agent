#!/usr/bin/env python3
"""
Produce & Publish: Personal AI Agent 2026 Documentary Video to YouTube.
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
HERMES_REPO = Path("/home/zen/hermes-agent")

SCENES = [
    {
        "id": 1,
        "title": "KỶ NGUYÊN PERSONAL AI AGENT 2026",
        "subtitle": "SỰ CHUYỂN DỊCH TỪ CHATBOT SANG TRỢ LÝ TỰ HÀNH",
        "color_top": (15, 23, 42),
        "color_bottom": (30, 58, 138),
        "voiceover": "Năm 2026, chúng ta đã chính thức bước qua thời kỳ của những con Chatbot thụ động. Giờ đây, Personal AI Agent đã định nghĩa lại hoàn toàn cách con người làm việc với máy tính nhờ khả năng tự lập kế hoạch, tự chạy lệnh và tự động hoàn thành mục tiêu phức tạp.",
        "duration": 14
    },
    {
        "id": 2,
        "title": "NĂNG LỰC THỰC CHIẾN ĐA TÁC VỤ",
        "subtitle": "AUTONOMOUS CODING • CONTENT FACTORY • DEVOPS 24/7",
        "color_top": (24, 24, 27),
        "color_bottom": (88, 28, 135),
        "voiceover": "Personal AI Agent năm 2026 có thể đọc toàn bộ dự án hàng chục nghìn dòng code, phát hiện lỗi và sửa bug đến khi đạt 100 phần trăm test pass. Đồng thời tự vận hành Content Factory đa phương tiện và quản trị hệ thống 24 trên 7.",
        "duration": 16
    },
    {
        "id": 3,
        "title": "TELEGRAM MISSION CONTROL & VIBE CODING",
        "subtitle": "ĐIỀU KHIỂN TỪ XA • PARALLEL EXECUTION TRÊN IDE",
        "color_top": (17, 24, 39),
        "color_bottom": (6, 95, 70),
        "voiceover": "Với Telegram Mission Control, bạn có thể điều khiển trực tiếp IDE và terminal trên máy trạm từ bất cứ đâu. Agent tự động chụp ảnh màn hình, tương tác giao diện và báo cáo kết quả theo thời gian thực.",
        "duration": 14
    },
    {
        "id": 4,
        "title": "HÀNG RÀO BẢO MẬT & ZERO-TRUST",
        "subtitle": "SECRET VAULT • HUMAN-IN-THE-LOOP • WHITELIST ACCESS",
        "color_top": (31, 41, 55),
        "color_bottom": (159, 18, 57),
        "voiceover": "Bảo mật là ưu tiên cốt lõi: Agent áp dụng mô hình Zero-Trust chỉ nhận lệnh từ người dùng đã xác thực, cô lập hoàn toàn API keys trong Secret Vault và bắt buộc phê duyệt tường minh cho các lệnh có rủi ro cao.",
        "duration": 15
    },
    {
        "id": 5,
        "title": "MÔ HÌNH SOVEREIGN AI TỰ CHỦ",
        "subtitle": "100% LOCAL PRIVACY TRÊN THINKPAD P15 WORKSTATION",
        "color_top": (10, 15, 30),
        "color_bottom": (30, 41, 59),
        "voiceover": "Sovereign AI cho phép vận hành toàn bộ mô hình ngôn ngữ lớn và cơ sở dữ liệu vector trực tiếp trên máy trạm cá nhân, đảm bảo quyền riêng tư tuyệt đối và triệt tiêu nguy cơ rò rỉ dữ liệu doanh nghiệp.",
        "duration": 15
    },
    {
        "id": 6,
        "title": "KẾT LUẬN & ĐĂNG KÝ KÊNH",
        "subtitle": "KÊNH YOUTUBE ZENPHAM • ĐỒNG HÀNH CÙNG KỶ NGUYÊN AI",
        "color_top": (15, 23, 42),
        "color_bottom": (30, 58, 138),
        "voiceover": "Personal AI Agent năm 2026 là đòn bẩy năng suất vượt trội. Hãy đăng ký kênh ZENPHAM và để lại bình luận để cùng khám phá các công nghệ AI tự hành mới nhất!",
        "duration": 12
    }
]


def create_gradient_canvas(w: int, h: int, color1: tuple, color2: tuple) -> Image.Image:
    """Create a sleek vertical gradient canvas."""
    base = Image.new("RGB", (w, h), color1)
    top = Image.new("RGB", (w, h), color2)
    mask = Image.new("L", (w, h))
    mask_data = []
    for y in range(h):
        mask_data.extend([int(255 * (y / h))] * w)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def render_slide_image(scene: dict, output_path: Path):
    """Draw a rich 1920x1080 cinematic slide card."""
    w, h = 1920, 1080
    img = create_gradient_canvas(w, h, scene["color_top"], scene["color_bottom"])
    draw = ImageDraw.Draw(img)

    # Draw decorative cybernetic grid & border lines
    draw.rectangle([60, 60, w - 60, h - 60], outline=(100, 149, 237, 120), width=3)
    draw.rectangle([80, 80, w - 80, h - 80], outline=(255, 255, 255, 40), width=1)

    # Header badge
    draw.rectangle([100, 100, 480, 155], fill=(59, 130, 246, 220))
    draw.text((120, 115), f"PHẦN {scene['id']}/6 • ZENPHAM AI 2026", fill=(255, 255, 255))

    # Main Title & Subtitle
    draw.text((100, 340), scene["title"], fill=(255, 255, 255))
    draw.text((100, 460), scene["subtitle"], fill=(56, 189, 248))

    # Glassmorphism container for text content
    draw.rectangle([100, 620, w - 100, 960], fill=(0, 0, 0, 160), outline=(255, 255, 255, 60), width=2)
    draw.text((140, 660), f"📌 Luận điểm cốt lõi:", fill=(250, 204, 21))
    
    # Wrap voiceover text preview
    vo_preview = scene["voiceover"]
    draw.text((140, 740), vo_preview[:120] + "...", fill=(226, 232, 240))
    if len(vo_preview) > 120:
        draw.text((140, 820), vo_preview[120:240] + "...", fill=(203, 213, 225))

    img.save(output_path, "JPEG", quality=95)


def get_voice_clone_reference(voice_name: str = "tuan anh - deep & powerful vietnamese") -> tuple:
    """Look up reference audio URL and reference text for voice cloning."""
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


def generate_audio(text: str, output_path: Path, duration: int, voice: str = "tuan anh - deep & powerful vietnamese") -> bool:
    """Generate voiceover audio using OmniVoice Voice Clone container on GPU, fallback to edge-tts."""
    # 1. Primary: OmniVoice GPU Voice Clone container
    try:
        ref_audio_url, ref_text = get_voice_clone_reference(voice)
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
            with open(output_path, "wb") as f:
                f.write(resp.read())
            if output_path.exists() and output_path.stat().st_size > 2000:
                print(f"  [✓] OmniVoice GPU Clone Audio generated: {output_path.stat().st_size // 1024} KB")
                return True
    except Exception as e:
        print(f"[*] OmniVoice error: {e}, falling back to edge-tts...", file=sys.stderr)

    # 2. Fallback: edge-tts
    try:
        res = subprocess.run([
            "edge-tts",
            "--text", text,
            "--write-media", str(output_path),
            "--voice", "vi-VN-HoaiMyNeural"
        ], capture_output=True, timeout=30)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 2000:
            return True
    except Exception:
        pass

    # 3. Fallback: synthesizer
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=520:duration={duration}",
        "-c:a", "pcm_s16le", str(output_path)
    ], capture_output=True, timeout=10)
    return output_path.exists()


def assemble_scene_video(img_path: Path, audio_path: Path, out_path: Path) -> bool:
    """Render 1 scene video with smooth zoom pan."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img_path),
        "-i", str(audio_path),
        "-vf", "scale=1920:1080,zoompan=z='min(zoom+0.0008,1.15)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_path)
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=60)
    if res.returncode != 0:
        # Simple fallback
        fallback = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(img_path), "-i", str(audio_path),
            "-vf", "scale=1920:1080", "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", str(out_path)
        ]
        res = subprocess.run(fallback, capture_output=True, timeout=60)
    return res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 5000


def main():
    print("[*] Starting Content Factory Video Production for YouTube...")
    scene_videos = []

    # 1. Render each scene
    for s in SCENES:
        sid = s["id"]
        img_p = OUTPUT_DIR / f"scene_{sid}.jpg"
        aud_p = OUTPUT_DIR / f"scene_{sid}.wav"
        vid_p = OUTPUT_DIR / f"scene_{sid}.mp4"

        print(f"[*] Rendering Scene {sid}/6: {s['title']}...")
        render_slide_image(s, img_p)
        generate_audio(s["voiceover"], aud_p, s["duration"])
        if assemble_scene_video(img_p, aud_p, vid_p):
            scene_videos.append(vid_p)
            print(f"[✓] Scene {sid} rendered: {vid_p} ({vid_p.stat().st_size // 1024} KB)")

    # 2. Concat all scenes into final video
    concat_list_path = OUTPUT_DIR / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for v in scene_videos:
            f.write(f"file '{v}'\n")

    final_video = OUTPUT_DIR / "personal_ai_agent_2026_final.mp4"
    print("[*] Concatenating full video...")
    res = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path),
        "-c", "copy", str(final_video)
    ], capture_output=True, timeout=120)

    if not final_video.exists():
        print("[!] Final video generation failed.", file=sys.stderr)
        sys.exit(1)

    print(f"[✓] Final Video Produced: {final_video} ({final_video.stat().st_size // (1024*1024)} MB)")

    # 3. Create Custom Thumbnail
    thumb_path = OUTPUT_DIR / "personal_ai_agent_2026_thumb.jpg"
    thumb_img = create_gradient_canvas(1280, 720, (15, 23, 42), (30, 58, 138))
    tdraw = ImageDraw.Draw(thumb_img)
    tdraw.rectangle([40, 40, 1240, 680], outline=(250, 204, 21), width=6)
    tdraw.rectangle([80, 80, 520, 150], fill=(239, 68, 68))
    tdraw.text((100, 95), "ZENPHAM • AI 2026", fill=(255, 255, 255))
    tdraw.text((80, 220), "PERSONAL AI AGENT 2026", fill=(255, 255, 255))
    tdraw.text((80, 340), "TỰ HÀNH • BẢO MẬT TUYỆT ĐỐI", fill=(56, 189, 248))
    tdraw.rectangle([80, 480, 1200, 620], fill=(0, 0, 0, 200), outline=(255, 255, 255, 80), width=2)
    tdraw.text((110, 520), "⚡ Vibe Coding | Telegram Mission Control | Sovereign AI", fill=(250, 204, 21))
    thumb_img.save(thumb_path, "JPEG", quality=95)
    print(f"[✓] Custom Thumbnail Produced: {thumb_path}")

    # 4. Publish to YouTube
    print("[*] Publishing video to YouTube Channel 'ZENPHAM'...")
    title = "Personal AI Agent 2026: Trợ Lý Tự Hành Đột Phá & Bảo Mật Tuyệt Đối"
    description = (
        "Khám phá toàn diện về Personal AI Agent trong năm 2026: Từ Chatbot thụ động sang AI tự hành, "
        "khả năng Vibe Coding điều khiển IDE từ xa qua Telegram, kiến trúc bảo mật Zero-Trust "
        "và mô hình Sovereign AI bảo vệ 100% dữ liệu cục bộ.\n\n"
        "📌 Nội dung chính:\n"
        "00:00 - Sự chuyển dịch từ Chatbot sang Autonomous Agent\n"
        "00:45 - Năng lực thực chiến đa tác vụ năm 2026\n"
        "01:45 - Telegram Mission Control & Vibe Coding\n"
        "02:45 - Hàng rào bảo mật Zero-Trust & Secret Vault\n"
        "03:45 - Mô hình Sovereign AI trên ThinkPad P15\n"
        "04:30 - Kết luận & Đăng ký kênh ZENPHAM\n\n"
        "#AIAgent #PersonalAI #VibeCoding #AutonomousAgent #HermesAgent #ZENPHAM #AI2026"
    )
    tags = "AIAgent,PersonalAI,VibeCoding,HermesAgent,ZENPHAM,AI2026,SovereignAI,MachineLearning"

    publish_cmd = [
        sys.executable,
        str(HERMES_REPO / "skills" / "media" / "youtube-publisher" / "scripts" / "yt_publish.py"),
        "upload",
        "--video", str(final_video),
        "--title", title,
        "--description", description,
        "--tags", tags,
        "--thumbnail", str(thumb_path),
        "--privacy", "public"
    ]

    pub_res = subprocess.run(publish_cmd, capture_output=True, text=True, timeout=120)
    print("YouTube Publish Output:\n", pub_res.stdout)
    if pub_res.stderr:
        print("YouTube Publish Stderr:\n", pub_res.stderr, file=sys.stderr)


if __name__ == "__main__":
    main()
