#!/usr/bin/env python3
"""
Vocal & Instrumental Stem Separator
Separates an input audio track into pure `vocals.wav` and `instrumental.wav`
using Demucs AI (htdemucs) with GPU acceleration.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def separate_stems(
    input_audio: str | Path,
    output_dir: str | Path,
    model_name: str = "htdemucs",
    device: str = "auto",
    overlap: float = 0.25,
) -> tuple[Path, Path]:
    """
    Separate input audio into (vocals_path, instrumental_path) using Demucs AI.
    """
    input_path = Path(input_audio).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input audio not found: {input_path}")

    stem_vocal = out_dir / "vocals.wav"
    stem_inst = out_dir / "instrumental.wav"

    # Check if already separated and cached
    if stem_vocal.exists() and stem_inst.exists() and stem_vocal.stat().st_size > 1000:
        print(f"[CACHE] Found existing clean stems in {out_dir}")
        return stem_vocal, stem_inst

    print(f"[SEPARATE] Demucs AI Isolating Vocals for: {input_path.name}...")

    # Execute Demucs via uv run or direct module
    demucs_out = out_dir / "demucs_temp"
    cmd = [
        "uv", "run", "--with", "demucs", "--with", "torch", "--with", "torchaudio",
        "python3", "-m", "demucs.separate",
        "-n", model_name,
        "-o", str(demucs_out),
        "--two-stems", "vocals",
        "--overlap", str(overlap),
    ]
    if device != "auto":
        cmd.extend(["-d", device])
    cmd.append(str(input_path))

    print(f"[DEMUCS] Running AI separation: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if res.returncode == 0:
        demucs_track_dir = demucs_out / model_name / input_path.stem
        vocal_src = demucs_track_dir / "vocals.wav"
        inst_src = demucs_track_dir / "no_vocals.wav"
        if vocal_src.exists() and inst_src.exists():
            shutil.move(str(vocal_src), str(stem_vocal))
            shutil.move(str(inst_src), str(stem_inst))
            shutil.rmtree(str(demucs_out), ignore_errors=True)
            print(f"[SUCCESS] Demucs AI stems isolated cleanly: {stem_vocal.name}, {stem_inst.name}")
            return stem_vocal, stem_inst
        else:
            print(f"[WARN] Demucs output files not located, falling back to phase filter...")
    else:
        print(f"[WARN] Demucs failed (rc={res.returncode}): {res.stderr[-300:]}")

    # Fallback to FFmpeg Center-Channel Vocal Extraction (Phase Cancellation)
    print("[FALLBACK] Using FFmpeg phase extraction filter...")
    
    ffmpeg_inst = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", "stereotools=mlev=0.016:slev=1.4,volume=1.1",
        "-ac", "2", "-ar", "44100", str(stem_inst)
    ]
    subprocess.run(ffmpeg_inst, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    ffmpeg_vocal = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", "stereotools=mlev=1.4:slev=0.016,highpass=f=120,lowpass=f=9500,volume=1.2",
        "-ac", "2", "-ar", "44100", str(stem_vocal)
    ]
    subprocess.run(ffmpeg_vocal, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"[SUCCESS] Stems exported: {stem_vocal}, {stem_inst}")
    return stem_vocal, stem_inst


def main():
    parser = argparse.ArgumentParser(description="Stem Separator for AI Covers")
    parser.add_argument("-i", "--input", required=True, help="Input audio file")
    parser.add_argument("-o", "--outdir", default="./stems", help="Output directory")
    parser.add_argument("-m", "--model", default="htdemucs", help="Demucs model name")
    parser.add_argument("--device", default="auto", help="Device: cuda, cpu, auto")
    args = parser.parse_args()

    vocal, inst = separate_stems(args.input, args.outdir, model_name=args.model, device=args.device)
    print(f"Vocals: {vocal}")
    print(f"Instrumental: {inst}")


if __name__ == "__main__":
    main()
