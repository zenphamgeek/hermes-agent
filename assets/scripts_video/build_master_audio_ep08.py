#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_master_audio_ep08.py
Concatenate scene_01.wav through scene_06.wav for Episode 08 using filter_complex concat
and apply 5-Stage Studio Vocal Chain:
1. Highpass 80Hz
2. De-mud EQ 300Hz
3. Presence EQ 3.8kHz
4. Air Treble 9kHz
5. EBU R128 Loudnorm (I=-14.5, TP=-1.5, LRA=7.0)
Sampling: 48kHz Stereo
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/home/zen/hermes-agent")
AUDIO_DIR = REPO_ROOT / "assets" / "scripts_video" / "audio" / "series_02" / "tap_08"
OUT_WAV = AUDIO_DIR / "master_audio_series_02_tap_08.wav"

def main():
    scenes = [AUDIO_DIR / f"scene_{i:02d}.wav" for i in range(1, 7)]
    for s in scenes:
        if not s.exists():
            print(f"❌ Missing scene wav: {s}")
            sys.exit(1)

    cmd = ["ffmpeg", "-y", "-v", "warning"]
    for s in scenes:
        cmd.extend(["-i", str(s)])

    concat_inputs = "".join(f"[{i}:a]" for i in range(len(scenes)))
    af_chain = (
        "highpass=f=80, "
        "equalizer=f=300:t=q:w=1.2:g=-1.5, "
        "equalizer=f=3800:t=q:w=1.0:g=1.8, "
        "treble=g=2.0:f=9000:t=s, "
        "loudnorm=I=-14.5:TP=-1.5:LRA=7.0"
    )

    filter_complex = f"{concat_inputs}concat=n={len(scenes)}:v=0:a=1,{af_chain}[aout]"
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-ar", "48000", "-ac", "2",
        str(OUT_WAV)
    ])

    print(f"[*] Concatenating and mastering audio cleanly via filter_complex to {OUT_WAV}...")
    subprocess.run(cmd, check=True)

    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(OUT_WAV)]
    dur = float(subprocess.check_output(dur_cmd, text=True).strip())
    print(f"[✓] Master audio created: {dur:.2f}s ({dur/60:.2f} min)")

    ebur_cmd = ["ffmpeg", "-i", str(OUT_WAV), "-af", "ebur128=framelog=verbose", "-f", "null", "-"]
    res = subprocess.run(ebur_cmd, capture_output=True, text=True)
    for line in res.stderr.splitlines():
        if "Integrated loudness" in line or "Loudness range" in line or "True peak" in line:
            print(f"   {line.strip()}")

if __name__ == "__main__":
    main()
