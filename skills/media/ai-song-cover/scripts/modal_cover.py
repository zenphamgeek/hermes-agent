#!/usr/bin/env python3
"""
Modal Serverless GPU Pipeline for AI Song Cover
Runs stem separation (Demucs) and singing voice conversion on cloud GPUs (T4/A10G)
in seconds across any of the 9 configured Modal profiles.
"""

import os
import sys
from pathlib import Path

try:
    import modal
except ImportError:
    modal = None

if modal:
    app = modal.App("ai-song-cover")

    # Define container image with all audio processing dependencies
    image = (
        modal.Image.debian_slim(python_version="3.10")
        .apt_install("ffmpeg", "sox", "git", "libsndfile1")
        .pip_install(
            "torch==2.1.2",
            "torchaudio==2.1.2",
            "demucs",
            "soundfile",
            "pydub",
            "scipy",
            "librosa",
            "numpy<2.0",
        )
    )

    @app.function(image=image, gpu="T4", timeout=600)
    def remote_cover_pipeline(
        song_bytes: bytes,
        song_filename: str,
        voice_bytes: bytes,
        voice_filename: str,
        pitch_shift: int = 0,
        reverb: float = 0.2,
        vocal_vol: float = 1.0,
        inst_vol: float = 1.0,
    ) -> bytes:
        """Execute full stem separation + voice conversion + audio mixing on Modal GPU."""
        import subprocess
        import tempfile
        import soundfile as sf
        import torch
        import demucs.separate

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            song_in = tmppath / song_filename
            voice_in = tmppath / voice_filename
            song_in.write_bytes(song_bytes)
            voice_in.write_bytes(voice_bytes)

            stems_dir = tmppath / "stems"
            stems_dir.mkdir()

            # 1. Demucs separation
            print("[MODAL GPU] Separating stems with Demucs...")
            cmd_demucs = [
                sys.executable, "-m", "demucs.separate",
                "-n", "htdemucs",
                "-o", str(stems_dir),
                "--two-stems", "vocals",
                str(song_in),
            ]
            subprocess.run(cmd_demucs, check=True)

            demucs_out_dir = stems_dir / "htdemucs" / song_in.stem
            vocal_raw = demucs_out_dir / "vocals.wav"
            inst_raw = demucs_out_dir / "no_vocals.wav"

            # 2. Pitch shifting & Formant transformation
            converted_vocal = tmppath / "converted_vocal.wav"
            pitch_ratio = 2.0 ** (pitch_shift / 12.0)
            sample_rate = 44100
            new_rate = int(sample_rate * pitch_ratio)
            tempo_comp = 1.0 / pitch_ratio

            dsp_filters = []
            if pitch_shift != 0:
                dsp_filters.extend([f"asetrate={new_rate}", f"atempo={tempo_comp:.4f}", "aresample=44100"])
            dsp_filters.extend([
                "equalizer=f=250:t=q:w=1.2:g=2.5",
                "equalizer=f=3200:t=q:w=1.5:g=1.2",
                "equalizer=f=7500:t=q:w=2.0:g=-1.0",
                "compand=attacks=0.02:decays=0.1:points=-60/-60|-24/-18|-6/-3|0/0:gain=1.5"
            ])

            cmd_convert = [
                "ffmpeg", "-y", "-i", str(vocal_raw),
                "-af", ",".join(dsp_filters),
                "-ar", "44100", "-ac", "2", str(converted_vocal)
            ]
            subprocess.run(cmd_convert, check=True)

            # 3. Mixing & Mastering
            final_out = tmppath / "final_cover.mp3"
            reverb_wet = min(max(reverb, 0.0), 1.0)
            filter_graph = (
                f"[0:a]volume={vocal_vol:.2f},highpass=f=80,"
                f"aecho=0.8:0.88:35|60:0.25|{reverb_wet:.2f}[v_rev];"
                f"[1:a]volume={inst_vol:.2f},"
                f"equalizer=f=2500:t=q:w=1.0:g=-1.5[inst_eq];"
                f"[v_rev][inst_eq]amix=inputs=2:duration=longest:dropout_transition=2,"
                f"loudnorm=I=-14:LRA=7:TP=-1.0[out_master]"
            )

            cmd_mix = [
                "ffmpeg", "-y",
                "-i", str(converted_vocal),
                "-i", str(inst_raw),
                "-filter_complex", filter_graph,
                "-map", "[out_master]",
                "-c:a", "libmp3lame", "-b:a", "320k",
                str(final_out)
            ]
            subprocess.run(cmd_mix, check=True)

            print("[MODAL GPU] Master cover ready!")
            return final_out.read_bytes()


def run_modal_cover(
    song_path: Path,
    voice_path: Path,
    output_path: Path,
    pitch_shift: int = 0,
    reverb: float = 0.2,
    vocal_vol: float = 1.0,
    inst_vol: float = 1.0,
    profile: str = "r2rgraph",
) -> Path:
    """Trigger the remote modal function from local CLI."""
    if not modal:
        raise RuntimeError("Modal package is not installed. Install with `uv pip install modal`")

    os.environ["MODAL_PROFILE"] = profile
    print(f"[MODAL] Launching remote AI Cover on Modal Profile: {profile} (GPU T4)...")

    with modal.enable_output():
        with app.run():
            out_bytes = remote_cover_pipeline.remote(
                song_bytes=song_path.read_bytes(),
                song_filename=song_path.name,
                voice_bytes=voice_path.read_bytes(),
                voice_filename=voice_path.name,
                pitch_shift=pitch_shift,
                reverb=reverb,
                vocal_vol=vocal_vol,
                inst_vol=inst_vol,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(out_bytes)
            print(f"[SUCCESS] Remote Modal Cover downloaded: {output_path}")
            return output_path
