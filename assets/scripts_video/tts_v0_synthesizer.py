#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_v0_synthesizer.py
=====================
TTS V0 Engine: Direct raw script synthesis with Local VieNeu-TTS (v3 Turbo on CUDA)
without any intermediate V8 phonetic modifications, dictionaries, or compound locks.

Standard:
- Input: 100% Raw Script (natural Vietnamese text directly from author script/cue sheet)
- Synthesizer: Local VieNeu-TTS v3 Turbo running on NVIDIA Quadro RTX 5000 (CUDA)
- Voice Clone: zenpham-zen-meditation-mientay.wav
- Mastering Chain: Highpass 75Hz + EBU R128 (-14.5 LUFS, TP <= -1.5 dBFS, 48000 Hz Stereo)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Union, List

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REF_WAV = REPO_ROOT / "assets" / "voices" / "Zen Mien Tay" / "zenpham-zen-meditation-mientay.wav"

try:
    from tts_input_sanitizer import sanitize_tts_input
except ImportError:
    from assets.scripts_video.tts_input_sanitizer import sanitize_tts_input

# Ensure vieneu package can be imported from vieneu_tts_test
VIENEU_SRC = REPO_ROOT / "vieneu_tts_test" / "src"
if str(VIENEU_SRC) not in sys.path:
    sys.path.insert(0, str(VIENEU_SRC))

try:
    from vieneu import Vieneu
except ImportError:
    Vieneu = None

class TtsV0Engine:
    def __init__(self, ref_wav: Optional[Path] = None, device: str = "cuda"):
        if Vieneu is None:
            raise ImportError(
                "Vieneu package not found. Run with: "
                f"{REPO_ROOT}/vieneu_tts_test/.venv/bin/python"
            )
        self.ref_wav = Path(ref_wav) if ref_wav else DEFAULT_REF_WAV
        if not self.ref_wav.exists():
            raise FileNotFoundError(f"Reference audio not found: {self.ref_wav}")

        print(f"[*] Initializing Local VieNeu-TTS v3 Turbo Engine on {device.upper()}...")
        t0 = time.time()
        self.engine = Vieneu()
        print(f"✓ Local VieNeu-TTS v3 Turbo Engine ready in {time.time() - t0:.2f}s")
        print(f"  Voice Reference: {self.ref_wav.name}")

    def synthesize(
        self,
        raw_text: str,
        output_wav: Union[str, Path],
        target_lufs: float = -14.5,
        target_tp: float = -1.5
    ) -> dict:
        """
        Synthesizes raw text directly without V8 preprocessing.
        Applies clean studio broadcast mastering (EBU R128).
        """
        # Security Control: Sanitize input against control chars, ANSI escapes, Trojan Source
        raw_text = sanitize_tts_input(raw_text)

        output_wav = Path(output_wav)
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        raw_wav = output_wav.with_suffix(".raw.wav")

        print(f"\n[TTS V0] Synthesizing ({len(raw_text.split())} words)...")
        t0 = time.time()
        # Golden Parameters tuned to eliminate tremor and produce round, resonant vowels:
        # - temperature: 0.65 (prevents micro-pitch jitter on sustained vowels)
        # - repetition_penalty: 1.12 (prevents vowel clipping/thinning while avoiding repeats)
        # - top_k: 20, top_p: 0.92 (prunes noisy acoustic tail tokens)
        # - max_chars: 180 (natural biological respiratory pacing)
        audio = self.engine.infer(
            raw_text,
            ref_audio=str(self.ref_wav),
            denoise=True,
            temperature=0.65,
            repetition_penalty=1.12,
            top_k=20,
            top_p=0.92,
            max_chars=180
        )
        t_infer = time.time() - t0
        self.engine.save(audio, str(raw_wav))

        # 5-Stage Studio Vocal Mastering Chain:
        # 1. Highpass 80Hz: Triệt tiêu rumble hạ âm dưới 80Hz
        # 2. De-mud EQ 300Hz: Hạ -2.0dB loại bỏ ồm rung lồng ngực
        # 3. Presence EQ 3800Hz: Nâng +3.0dB giúp phụ âm sắc nét, tròn vành rõ chữ
        # 4. Air Treble 9000Hz: Nâng +3.5dB cho dải cao mượt mà, sang trọng
        # 5. EBU R128 Loudnorm: Chuẩn phát thanh -14.5 LUFS, TP -1.5 dBFS, LRA 7.0
        af_chain = (
            "highpass=f=80, "
            "equalizer=f=300:t=q:w=1.5:g=-2.0, "
            "equalizer=f=3800:t=q:w=1.2:g=3.0, "
            "treble=g=3.5:f=9000:t=s, "
            f"loudnorm=I={target_lufs}:TP={target_tp}:LRA=7.0"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_wav),
            "-af", af_chain,
            "-ar", "48000",
            "-ac", "2",
            str(output_wav)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if raw_wav.exists():
            raw_wav.unlink()

        # Audit with ffprobe (safe array-based call, zero shell=True)
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output_wav)
        ]
        dur = float(subprocess.check_output(probe_cmd).decode().strip())

        rtf = t_infer / max(dur, 0.01)
        print(f"✓ Mastered WAV created: {output_wav.name} | Duration: {dur:.2f}s | RTF: {rtf:.2f}")

        return {
            "output_wav": str(output_wav),
            "duration": dur,
            "inference_time": t_infer,
            "rtf": rtf,
            "word_count": len(raw_text.split())
        }

def main():
    parser = argparse.ArgumentParser(description="TTS V0 Synthesizer with Local VieNeu-TTS")
    parser.add_argument("--text", type=str, help="Raw script text to synthesize")
    parser.add_argument("--text-file", type=Path, help="File containing raw text")
    parser.add_argument("--output", type=Path, required=True, help="Target output wav path")
    parser.add_argument("--ref-wav", type=Path, default=DEFAULT_REF_WAV, help="Reference audio path")
    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.text_file and args.text_file.exists():
        with open(args.text_file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError("Must provide either --text or valid --text-file")

    engine = TtsV0Engine(ref_wav=args.ref_wav)
    engine.synthesize(text, args.output)

if __name__ == "__main__":
    main()
