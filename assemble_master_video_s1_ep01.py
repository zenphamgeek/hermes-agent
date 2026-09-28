#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_master_video_s1_ep01.py
================================
Assembles 2K QHD (2560x1440 @ 60fps) master video for ZenPham Series 1 Episode 01:
"Bản chất của xác suất trong AI — Đồng xu của cỗ máy"
1. Synchronizes 8 rendered 2K Manim scene animations with TTS V0-Sense audio via tpad=clone.
2. Encodes intermediate clips with NVENC hardware acceleration.
3. Concatenates and multiplexes with 5-stage mastered audio.
4. Generates YouTube 2026 packaging metadata suite in staging directory.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path("/home/zen/hermes-agent")
SCRIPTS_VIDEO_DIR = REPO_ROOT / "assets" / "scripts_video"
AUDIO_DIR = SCRIPTS_VIDEO_DIR / "audio" / "series_01" / "tap_01"
MANIM_MEDIA_DIR = SCRIPTS_VIDEO_DIR / "output" / "manim_media" / "series_01" / "tap_01" / "videos" / "manim_s1_tap_01_probability" / "1440p60"
STAGING_DIR = SCRIPTS_VIDEO_DIR / "output" / "youtube_staging" / "series_01" / "tap_01"
CLIPS_DIR = STAGING_DIR / "scene_clips"

SCENE_MANIM_MAP = {
    1: "S1E1Scene01ColdOpen",
    2: "S1E1Scene02LaplaceDemon",
    3: "S1E1Scene03ShannonInformation",
    4: "S1E1Scene04BayesianBalance",
    5: "S1E1Scene05SoftmaxTemperature",
    6: "S1E1Scene06GaltonLawOfLargeNumbers",
    7: "S1E1Scene07ConfidenceTrapECE",
    8: "S1E1Scene08OceanOfUncertainty",
}

def get_duration(p: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(p)
    ]
    return float(subprocess.check_output(cmd, text=True).strip())

def main():
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    master_audio = AUDIO_DIR / "master_audio_series_01_tap_01.wav"
    if not master_audio.exists():
        print(f"❌ Master audio missing: {master_audio}")
        sys.exit(1)

    audio_total_dur = get_duration(master_audio)
    print(f"[*] Master Audio Duration: {audio_total_dur:.2f}s ({audio_total_dur/60:.2f} min)")

    scene_audio_durs = {}
    for idx in range(1, 9):
        w = AUDIO_DIR / f"scene_{idx:02d}.wav"
        if not w.exists():
            print(f"❌ Missing scene audio: {w}")
            sys.exit(1)
        dur = get_duration(w)
        scene_audio_durs[idx] = dur
        print(f"   Scene {idx:02d} Audio: {dur:.2f}s")

    # Encode each scene clip with tpad
    print(f"\n[*] Assembling 8 Scene Video Clips with tpad Synchronization...")
    clip_paths = []

    for idx in range(1, 9):
        scene_name = SCENE_MANIM_MAP[idx]
        manim_mp4 = MANIM_MEDIA_DIR / f"{scene_name}.mp4"
        if not manim_mp4.exists():
            print(f"❌ Missing rendered scene mp4: {manim_mp4}")
            sys.exit(1)

        manim_dur = get_duration(manim_mp4)
        target_dur = scene_audio_durs[idx]
        pad_dur = max(0.0, target_dur - manim_dur)

        out_clip = CLIPS_DIR / f"clip_{idx:02d}_{scene_name}.mp4"
        clip_paths.append(out_clip)

        print(f"   [+] Encoding Clip {idx:02d} ({scene_name}): Manim {manim_dur:.2f}s -> Target {target_dur:.2f}s (pad +{pad_dur:.2f}s)...")

        cmd = [
            "ffmpeg", "-y", "-v", "warning",
            "-i", str(manim_mp4),
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad_dur:.3f}",
            "-t", f"{target_dur:.3f}",
            "-c:v", "h264_nvenc",
            "-preset", "p6",
            "-cq", "19",
            "-pix_fmt", "yuv420p",
            "-r", "60",
            str(out_clip)
        ]
        subprocess.run(cmd, check=True)

    # Concat file list
    concat_list_file = STAGING_DIR / "concat_clips.txt"
    with open(concat_list_file, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.resolve()}'\n")

    # Final Master Assembly
    final_output = STAGING_DIR / "master_2k.mp4"
    print(f"\n[*] Concatenating clips and multiplexing audio -> {final_output}...")

    cmd_mux = [
        "ffmpeg", "-y", "-v", "warning",
        "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        str(final_output)
    ]
    subprocess.run(cmd_mux, check=True)

    final_dur = get_duration(final_output)
    final_size = final_output.stat().st_size / (1024 * 1024)
    print(f"\n[✓] MASTER 2K QHD VIDEO ASSEMBLED SUCCESSFULLY!")
    print(f"   Path: {final_output}")
    print(f"   Duration: {final_dur:.2f}s ({final_dur/60:.2f} min)")
    print(f"   Size: {final_size:.2f} MB")

    # Generate YouTube 2026 Staging Metadata
    print("\n[*] Generating YouTube 2026 Staging Metadata...")
    meta = {
        "series": "Tôi Làm Việc — ZenPham Educational Cinema",
        "season": 1,
        "episode": 1,
        "title": "Bản chất của Xác Suất trong AI: Có Phép Màu Nào Đằng Sau Đồng Xu?",
        "subtitle": "Từ Cú Búng Tay Của Quỷ Laplace Đến Đại Dương Bất Định Của Claude Shannon",
        "duration_seconds": round(final_dur, 2),
        "resolution": "2560x1440 @ 60fps",
        "audio_standard": "EBU R128 (-14.5 LUFS Stereo)",
        "published_at": None,
        "tags": [
            "AI", "Xác suất", "Định lý Bayes", "Claude Shannon",
            "Entropy", "Softmax", "Temperature", "Galton Board",
            "Định luật số lớn", "ECE", "Hallucination", "Manim", "ZenPham"
        ]
    }
    with open(STAGING_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    desc_content = """Bản chất của Xác Suất trong AI: Có Phép Màu Nào Đằng Sau Đồng Xu?

Khi tung một đồng xu lên không trung, kết quả là ngẫu nhiên hay chỉ là sự thiếu hụt thông tin của con người?
Và tại sao một cỗ máy vi mạch hiện đại — thứ được xây dựng từ hàng tỷ bóng bán dẫn tất định bậc nhất — lại phải liên tục tung những đồng xu xác suất để trò chuyện cùng chúng ta?

Trong tập mở màn của Series "Tôi Làm Việc", chúng ta cùng đi sâu vào giải phẫu toán học và triết học của xác suất trong Trí Tuệ Nhân Tạo: từ cú búng tay cơ học cổ điển của Newton, Quỷ Laplace, thước đo thông tin 1 bit của Claude Shannon, cán cân niềm tin Thomas Bayes, bàn xoay Softmax Temperature, đến phép màu hội tụ của Định luật số lớn.

TIMESTAMPS:
00:00 - Cú búng tay trong bóng tối & Nghịch lý tất định
01:02 - Quỷ Laplace & Hai tầng ngẫu nhiên: Bản thể vs Nhận thức
02:07 - Claude Shannon & Thước đo độ bất ngờ (1 Bit thông tin)
03:22 - Cán cân cơ học Bayes: Cập nhật niềm tin bằng bằng chứng
04:31 - Ma trận trọng số, đa tạp Softmax & Bàn xoay Nhiệt độ (Temperature)
06:01 - Phép màu Định luật Số lớn & Bàn chốt cản Galton
07:10 - Chiếc bẫy tự tin (Overconfidence Gap) & Hiệu chuẩn sai số ECE
08:19 - Đại dương bất định & Hẹn gặp lại ở Tập 02 (Gradient Descent)

---
Toàn bộ đồ họa toán học được lập trình động lực học trực quan bằng Manim Community (2K QHD 60fps).
Âm thanh chuẩn phát thanh quốc tế EBU R128 (-14.5 LUFS).

#ZenPham #ToiLamViec #ArtificialIntelligence #Manim #Probability #DataScience
"""
    with open(STAGING_DIR / "description.txt", "w", encoding="utf-8") as f:
        f.write(desc_content)

    pinned_comment = """Bạn tin rằng trí tuệ nhân tạo sau cùng chỉ là một cỗ máy tính toán xác suất tinh xảo, hay khi số lượng tham số đủ lớn, một dạng ý thức thực sự sẽ trỗi dậy?

Hãy để lại góc nhìn của bạn bên dưới, và hẹn gặp lại bạn ở Tập 02: Giải tích & Chiếc la bàn Gradient Descent!"""
    with open(STAGING_DIR / "pinned_comment.txt", "w", encoding="utf-8") as f:
        f.write(pinned_comment)

    print("✓ Staging metadata generated (metadata.json, description.txt, pinned_comment.txt)")

if __name__ == "__main__":
    main()
