#!/usr/bin/env python3
"""
OmniVoice Moon Phan TTS Synthesis Pipeline
-------------------------------------------
Reads formalized Vietnamese text, performs prosodic chunking, synthesizes
via LXC OmniVoice GPU container with Moon Phan voice cloning, and stitches
into studio-quality master audio (.mp3) + synced SRT subtitles.
"""

import argparse
import concurrent.futures
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("omnivoice_tts")

OMNIVOICE_BASE = os.environ.get("OMNIVOICE_URL", "http://10.123.214.178:80").rstrip("/")
VOICE_NAME = "moon phan - audiobooks & podcast"
VOICE_PROMPT_DEFAULT = "Chúc bạn một ngày mới tràn đầy năng lượng và đủ dũng cảm để bắt đầu một điều gì đó dù là rất nhỏ"

def get_moon_phan_voice_info() -> Tuple[str, str]:
    """Fetch current pre-signed S3 ref_audio URL and ref_text for Moon Phan voice."""
    try:
        req = urllib.request.Request(f"{OMNIVOICE_BASE}/voices")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for eng in ["omnivoice", "fishspeech"]:
                if eng in data and "voices" in data[eng]:
                    for v in data[eng]["voices"]:
                        if "moon phan" in v.get("name", "").lower():
                            ref_audio = v.get("ref_audio", "")
                            ref_text = v.get("ref_text", VOICE_PROMPT_DEFAULT)
                            if ref_audio:
                                return ref_audio, ref_text
    except Exception as e:
        logger.warning(f"Could not query /voices endpoint: {e}")
    return "", VOICE_PROMPT_DEFAULT


def format_srt_timestamp(seconds: float) -> str:
    """Format float seconds to SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_into_prosodic_chunks(text: str, max_chars: int = 320, min_chars: int = 60) -> List[str]:
    """
    Split formalized text into natural sentence and clause chunks.
    Ensures optimal pacing and prosody for Dharma audiobook narration.
    """
    paragraphs = text.split("\n\n")
    chunks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Split on sentence end delimiters: . ! ? …
        sentences = re.split(r"(?<=[.?!…])\s+", para)
        cur_chunk = ""

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            if len(cur_chunk) + len(sent) + 1 <= max_chars:
                cur_chunk = f"{cur_chunk} {sent}".strip()
            else:
                if cur_chunk:
                    chunks.append(cur_chunk)
                    cur_chunk = ""

                # If sentence itself exceeds max_chars, split on clauses
                if len(sent) > max_chars:
                    clauses = re.split(r"(?<=[,;:\-–—])\s+", sent)
                    sub_chunk = ""
                    for cl in clauses:
                        cl = cl.strip()
                        if not cl:
                            continue
                        if len(sub_chunk) + len(cl) + 1 <= max_chars:
                            sub_chunk = f"{sub_chunk} {cl}".strip()
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk)
                            sub_chunk = cl
                    if sub_chunk:
                        cur_chunk = sub_chunk
                else:
                    cur_chunk = sent

        if cur_chunk:
            chunks.append(cur_chunk)

    return chunks if chunks else [text]


def synthesize_chunk_request(
    chunk_text: str,
    output_wav: Path,
    ref_audio_url: str,
    ref_text: str,
    speed: float = 1.0,
    retry_count: int = 3
) -> bool:
    """Call OmniVoice TTS API on LXC container for a single chunk."""
    if output_wav.exists() and output_wav.stat().st_size > 2000:
        return True

    payload = {
        "text": chunk_text,
        "voice": VOICE_NAME,
        "engine": "omnivoice",
        "lang": "vi",
        "speed": speed,
    }
    if ref_audio_url:
        payload["ref_audio"] = ref_audio_url
        payload["ref_text"] = ref_text

    data_bytes = json.dumps(payload).encode("utf-8")
    url = f"{OMNIVOICE_BASE}/tts/omnivoice"

    for attempt in range(retry_count + 1):
        try:
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                if resp.status == 200:
                    raw_data = resp.read()
                    audio_data = None

                    # Check if response is JSON with download_url (S3 cache)
                    if raw_data.startswith(b"{"):
                        try:
                            res_json = json.loads(raw_data.decode("utf-8"))
                            dl_url = res_json.get("download_url") or res_json.get("audio_url")
                            if dl_url:
                                with urllib.request.urlopen(dl_url, timeout=60) as dl_resp:
                                    audio_data = dl_resp.read()
                        except Exception:
                            pass
                    elif len(raw_data) > 2000:
                        audio_data = raw_data

                    if audio_data and len(audio_data) > 2000:
                        with open(output_wav, "wb") as f:
                            f.write(audio_data)
                        return True
        except Exception as e:
            if attempt == retry_count:
                logger.error(f"TTS Chunk synthesis failed: '{chunk_text[:50]}...' -> {e}")
                return False
            time.sleep(1.5 * (attempt + 1))
    return False


def get_audio_duration_ffprobe(audio_path: Path) -> float:
    """Get exact duration in seconds using ffprobe."""
    try:
        res = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ], capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        # Fallback estimation for 24kHz 16-bit mono WAV (~48kB/s)
        size = audio_path.stat().st_size
        return max(size / 48000.0, 0.5)


def stitch_audio_and_srt(
    chunk_files: List[Path],
    chunks: List[str],
    output_mp3: Path,
    output_srt: Path,
    pause_ms: int = 350,
    bitrate: str = "192k"
):
    """Concatenate WAV chunks with silence padding using ffmpeg and export synced SRT."""
    tmp_dir = chunk_files[0].parent
    silence_wav = tmp_dir / "silence_gap.wav"
    silence_sec = max(pause_ms / 1000.0, 0.05)

    # 1. Create silence WAV
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(silence_sec),
        str(silence_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 2. Build concat list and SRT timestamps
    concat_list = tmp_dir / "concat_list.txt"
    srt_entries = []
    current_time = 0.0

    with open(concat_list, "w", encoding="utf-8") as f:
        for i, (c_file, chunk_text) in enumerate(zip(chunk_files, chunks)):
            f.write(f"file '{c_file.resolve()}'\n")
            dur = get_audio_duration_ffprobe(c_file)
            start_ts = format_srt_timestamp(current_time)
            end_ts = format_srt_timestamp(current_time + dur)

            srt_entries.append(f"{i+1}\n{start_ts} --> {end_ts}\n{chunk_text}\n")
            current_time += dur

            if i < len(chunk_files) - 1:
                f.write(f"file '{silence_wav.resolve()}'\n")
                current_time += silence_sec

    # 3. Render Master MP3
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c:a", "libmp3lame",
        "-b:a", bitrate,
        str(output_mp3)
    ]
    logger.info(f"Rendering master MP3 ({bitrate}) via FFmpeg...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 4. Save synced SRT
    with open(output_srt, "w", encoding="utf-8") as sf:
        sf.write("\n".join(srt_entries))
    logger.info(f" [✓] Synced SRT Subtitle saved: {output_srt}")


def process_tts_pipeline(
    formalized_text_file: Path,
    output_audio_path: Optional[Path] = None,
    max_workers: int = 3,
    max_chunk_chars: int = 320,
    pause_ms: int = 350,
    speed: float = 1.0
):
    start_time = time.time()
    text = formalized_text_file.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"File {formalized_text_file} is empty!")

    chunks = split_into_prosodic_chunks(text, max_chars=max_chunk_chars)
    logger.info(f"Loaded formalized text: {len(text):,} chars | {len(chunks)} chunks")
    logger.info(f"Target Voice: Moon Phan ('{VOICE_NAME}') on LXC OmniVoice GPU container.")

    ref_audio_url, ref_text = get_moon_phan_voice_info()
    logger.info(f"Reference Audio URL: {'Available' if ref_audio_url else 'Using server voice'}")
    logger.info(f"Reference Text: '{ref_text}'")

    if not output_audio_path:
        out_dir = Path("/home/zen/hermes-agent/output_audio")
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_stem = re.sub(r'[\\/*?:"<>|]', "", formalized_text_file.stem).strip()
        output_audio_path = out_dir / f"{safe_stem}_moon_phan.mp3"

    output_srt_path = output_audio_path.with_suffix(".srt")

    cache_dir = output_audio_path.parent / ".chunk_cache" / output_audio_path.stem
    cache_dir.mkdir(parents=True, exist_ok=True)
    chunk_files = [cache_dir / f"chunk_{i:04d}.wav" for i in range(len(chunks))]

    cached_count = sum(1 for f in chunk_files if f.exists() and f.stat().st_size > 2000)
    logger.info(f"Found {cached_count}/{len(chunks)} chunks already synthesized in cache.")

    pending_indices = [i for i, f in enumerate(chunk_files) if not (f.exists() and f.stat().st_size > 2000)]
    logger.info(f"Synthesizing {len(pending_indices)} pending chunks with {max_workers} worker threads...")

    completed_count = cached_count
    if pending_indices:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(
                    synthesize_chunk_request,
                    chunks[i],
                    chunk_files[i],
                    ref_audio_url,
                    ref_text,
                    speed
                ): i for i in pending_indices
            }

            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                success = future.result()
                if not success:
                    raise RuntimeError(f"Chunk {idx+1} synthesis failed on OmniVoice!")
                completed_count += 1
                if completed_count % 10 == 0 or completed_count == len(chunks):
                    pct = (completed_count / len(chunks)) * 100
                    logger.info(f"TTS Progress: [{completed_count}/{len(chunks)}] chunks ({pct:.1f}%)...")

    # Stitch into master MP3 + SRT
    stitch_audio_and_srt(
        chunk_files=chunk_files,
        chunks=chunks,
        output_mp3=output_audio_path,
        output_srt=output_srt_path,
        pause_ms=pause_ms
    )

    elapsed = time.time() - start_time
    size_mb = output_audio_path.stat().st_size / (1024 * 1024)
    duration_sec = get_audio_duration_ffprobe(output_audio_path)
    logger.info("=" * 60)
    logger.info(f" [✓] TTS MASTER AUDIO GENERATED SUCCESSFULLY!")
    logger.info(f"File: {output_audio_path}")
    logger.info(f"Duration: {duration_sec/60:.2f} minutes ({duration_sec:.1f}s)")
    logger.info(f"Size: {size_mb:.2f} MB")
    logger.info(f"Subtitle: {output_srt_path}")
    logger.info(f"Elapsed time: {elapsed:.1f}s ({elapsed/60:.2f} minutes)")
    logger.info("=" * 60)
    return output_audio_path, output_srt_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OmniVoice Moon Phan TTS runner.")
    parser.add_argument("file", help="Formalized text file path")
    parser.add_argument("-o", "--output", help="Output MP3 file path")
    parser.add_argument("-w", "--workers", type=int, default=3, help="Concurrent workers (default: 3)")
    parser.add_argument("--max-chars", type=int, default=320, help="Max characters per chunk (default: 320)")
    parser.add_argument("--pause-ms", type=int, default=350, help="Inter-chunk pause ms (default: 350)")
    parser.add_argument("--speed", type=float, default=1.0, help="Reading speed (default: 1.0)")
    args = parser.parse_args()

    inp = Path(args.file)
    if not inp.exists():
        logger.error(f"Input file not found: {args.file}")
        sys.exit(1)

    out = Path(args.output) if args.output else None
    process_tts_pipeline(
        formalized_text_file=inp,
        output_audio_path=out,
        max_workers=args.workers,
        max_chunk_chars=args.max_chars,
        pause_ms=args.pause_ms,
        speed=args.speed
    )
