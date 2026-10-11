#!/usr/bin/env python3
"""
AI Song Cover Orchestrator
Transforms any input song into a full AI Song Cover using a custom voice sample.

Usage:
  uv run python skills/media/ai-song-cover/scripts/cover.py \
    --song "path/to/song.mp3" \
    --voice "assets/voices/zenpham-mien tay-trung nien.mp3" \
    --pitch -12 \
    --output "output/zenpham_cover.mp3"
"""

import argparse
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from separator import separate_stems
from converter import convert_voice, resolve_voice_sample
from mixer import mix_cover


def build_cover(
    song_path: str | Path,
    voice_target: str | Path = "zenpham-mien tay-trung nien",
    output_path: str | Path | None = None,
    pitch_shift: int = 0,
    reverb: float = 0.20,
    vocal_vol: float = 1.0,
    inst_vol: float = 1.0,
    f0_method: str = "rmvpe",
    engine: str = "local",
    modal_profile: str = "r2rgraph",
    keep_stems: bool = False,
) -> Path:
    """
    End-to-end AI Song Cover generation pipeline.

    Args:
        song_path: Input song file (.mp3, .wav, .m4a, .mp4).
        voice_target: Target voice path or name in assets/voices.
        output_path: Final output file path.
        pitch_shift: Semitones transposition (-12 to +12).
        reverb: Reverb wet amount (0.0 to 1.0).
        vocal_vol: Vocal gain multiplier.
        inst_vol: Instrumental gain multiplier.
        f0_method: Pitch detection algorithm.
        engine: 'local' (local GPU) or 'modal' (Modal GPU cloud).
        modal_profile: Modal profile workspace.
        keep_stems: Whether to retain intermediate stem files.

    Returns:
        Path to the finished cover file.
    """
    song_file = Path(song_path).resolve()
    if not song_file.exists():
        raise FileNotFoundError(f"Song file not found: {song_file}")

    voice_file = resolve_voice_sample(voice_target)

    # Determine output path if not specified
    if not output_path:
        out_dir = Path("/home/zen/workspace/output/covers")
        out_dir.mkdir(parents=True, exist_ok=True)
        sanitized_song = song_file.stem.replace(" ", "_")
        sanitized_voice = voice_file.stem.replace(" ", "_")
        final_out = out_dir / f"{sanitized_song}_{sanitized_voice}_pitch{pitch_shift:+d}.mp3"
    else:
        final_out = Path(output_path).resolve()
        final_out.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎵 AI SONG COVER GENERATOR")
    print(f"▶ Input Song:    {song_file.name}")
    print(f"▶ Voice Timbre:  {voice_file.name}")
    print(f"▶ Pitch Shift:   {pitch_shift:+d} semitones")
    print(f"▶ Reverb Wet:    {reverb:.2f}")
    print(f"▶ Engine:        {engine.upper()} {'(' + modal_profile + ')' if engine == 'modal' else ''}")
    print(f"▶ Output File:   {final_out}")
    print("=" * 60)

    start_time = time.time()

    # Route to Modal if requested
    if engine.lower() == "modal":
        try:
            from modal_cover import run_modal_cover
            res = run_modal_cover(
                song_path=song_file,
                voice_path=voice_file,
                output_path=final_out,
                pitch_shift=pitch_shift,
                reverb=reverb,
                vocal_vol=vocal_vol,
                inst_vol=inst_vol,
                profile=modal_profile,
            )
            elapsed = time.time() - start_time
            print(f"✨ Cover completed successfully in {elapsed:.1f}s via Modal GPU!")
            return res
        except Exception as e:
            print(f"[WARN] Modal run failed: {e}. Falling back to Local engine...")

    # Local Pipeline Execution
    work_dir = Path(tempfile.mkdtemp(prefix="aicover_"))
    try:
        # Step 1: Stem Separation
        print("\n[Step 1/3] 🎼 Isolating Vocals & Instrumental Beat...")
        stems_dir = final_out.parent / "stems" if keep_stems else work_dir / "stems"
        stems_dir.mkdir(parents=True, exist_ok=True)
        vocal_raw, inst_raw = separate_stems(song_file, stems_dir)

        # Step 2: Voice Timbre & Pitch Conversion
        print("\n[Step 2/3] 🎤 Transforming Singing Voice Timbre...")
        converted_vocal = work_dir / "converted_vocal.wav"
        convert_voice(
            vocal_path=vocal_raw,
            voice_reference=voice_file,
            output_path=converted_vocal,
            pitch_shift=pitch_shift,
            f0_method=f0_method,
        )

        # Step 3: Mixing & Mastering
        print("\n[Step 3/3] 🎚️ Mixing, Reverb Ambience & LuFS Mastering...")
        mix_cover(
            vocal_path=converted_vocal,
            instrumental_path=inst_raw,
            output_path=final_out,
            vocal_volume=vocal_vol,
            instrumental_volume=inst_vol,
            reverb_amount=reverb,
            format="mp3",
            bitrate="320k",
        )

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"🎉 SUCCESS: AI Song Cover created in {elapsed:.1f}s!")
        print(f"📁 Output: {final_out} ({final_out.stat().st_size // 1024} KB)")
        print("=" * 60)
        return final_out

    finally:
        if not keep_stems:
            shutil.rmtree(str(work_dir), ignore_errors=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Song Cover Generator - Transform any song with your voice."
    )
    parser.add_argument(
        "-s", "--song",
        required=True,
        help="Path to the input song file (MP3, WAV, MP4, M4A)",
    )
    parser.add_argument(
        "-v", "--voice",
        default="zenpham-mien tay-trung nien",
        help="Voice sample path or name from assets/voices/ (default: zenpham-mien tay-trung nien)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Destination path for output cover file",
    )
    parser.add_argument(
        "-p", "--pitch",
        type=int,
        default=0,
        help="Key transposition in semitones: -12 (female to male), +12 (male to female), 0 (no change)",
    )
    parser.add_argument(
        "--reverb",
        type=float,
        default=0.20,
        help="Reverb wet ratio (0.0 = dry, 0.2 = ballad, 0.35 = bolero hall)",
    )
    parser.add_argument(
        "--vocal-vol",
        type=float,
        default=1.0,
        help="Vocal volume multiplier (e.g. 1.1 = +1dB boost)",
    )
    parser.add_argument(
        "--inst-vol",
        type=float,
        default=1.0,
        help="Instrumental volume multiplier (e.g. 0.9 = slight cut)",
    )
    parser.add_argument(
        "--pitch-algo",
        default="rmvpe",
        choices=["rmvpe", "harvest", "crepe", "pm"],
        help="F0 pitch detection algorithm (default: rmvpe)",
    )
    parser.add_argument(
        "--engine",
        default="local",
        choices=["local", "modal"],
        help="Processing engine: local GPU or cloud Modal GPU",
    )
    parser.add_argument(
        "--modal-profile",
        default="r2rgraph",
        help="Modal profile workspace to run on (r2rgraph, diatts, mojopham, etc.)",
    )
    parser.add_argument(
        "--keep-stems",
        action="store_true",
        help="Retain isolated vocal and instrumental stem files",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        build_cover(
            song_path=args.song,
            voice_target=args.voice,
            output_path=args.output,
            pitch_shift=args.pitch,
            reverb=args.reverb,
            vocal_vol=args.vocal_vol,
            inst_vol=args.inst_vol,
            f0_method=args.pitch_algo,
            engine=args.engine,
            modal_profile=args.modal_profile,
            keep_stems=args.keep_stems,
        )
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
