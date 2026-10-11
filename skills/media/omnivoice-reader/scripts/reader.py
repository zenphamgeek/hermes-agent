#!/usr/bin/env python3
"""
OmniVoice Long Text Reader (Smart Chunking & Voice Cloning)
----------------------------------------------------------
Narrates and reads long text documents, transcripts, books, and articles using
the GPU-accelerated OmniVoice TTS engine running on the P15 LXC container.

Features:
- Smart semantic chunking on sentence & paragraph boundaries
- Vietnamese text normalization (cleaning sound tags [âm nhạc], punctuation, numbers)
- Voice cloning from reference audio (e.g. Moon Phan, Dũng, Tuấn Anh, Trang, etc.)
- Multi-threaded synthesis with progress bar
- Studio-grade audio concatenation with configurable natural pause intervals
- Optional synchronized SRT subtitle export for video dubbing / audiobooks
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
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import boto3
except ImportError:
    boto3 = None

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    console = Console()
except ImportError:
    console = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("omnivoice_reader")

# OmniVoice LXC Server Constants
DEFAULT_OMNIVOICE_URL = os.environ.get("OMNIVOICE_URL", "http://10.123.214.178:80/tts")
DEFAULT_VOICE = "moon phan - audiobooks & podcast"
DEFAULT_ENGINE = "omnivoice"

# MinIO S3 Voice Registry
S3_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://10.123.214.249:9000")
S3_BUCKET = "omnivoice-audio"
S3_ACCESS_KEY = "omnivoice-svc"
S3_SECRET_KEY = "omnivoice_svc_2026"


def sanitize_filename(name: str, max_len: int = 120) -> str:
    """Sanitize string for safe filesystem usage across OS platforms."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip()
    return cleaned or "untitled"


def format_timestamp(seconds: float) -> str:
    """Convert float seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def clean_transcript_text(raw_text: str) -> str:
    """
    Clean YouTube transcript artifacts:
    - Removes sound tags: [âm nhạc], [vỗ tay], [Music], [Applause], (nhạc), etc.
    - Joins line-broken sentences into continuous flow.
    - Standardizes quotes, dashes, and multiple spaces.
    """
    # Remove bracketed sound cues
    cleaned = re.sub(r"\[(?:âm nhạc|nhạc|vỗ tay|music|applause|cười|tiếng cười)\]", "", raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\((?:âm nhạc|nhạc|vỗ tay|music|applause)\)", "", cleaned, flags=re.IGNORECASE)
    
    # Remove sequence numbers or timestamps if present
    cleaned = re.sub(r"^\d+\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\d{2}:\d{2}(?::\d{2})?(?:[.,]\d+)?\s*-->\s*\d{2}:\d{2}(?::\d{2})?(?:[.,]\d+)?", "", cleaned)

    # Rejoin lines into smooth paragraphs
    paragraphs = []
    current_para = []
    
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
        else:
            current_para.append(line)
            
    if current_para:
        paragraphs.append(" ".join(current_para))

    result = "\n\n".join(paragraphs)
    # Normalize multiple whitespace
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result


def split_text_into_chunks(text: str, max_chars: int = 380, min_chars: int = 80) -> List[str]:
    """
    Split text into prosodically natural chunks for TTS synthesis.
    Splits on sentence delimiters (. ? ! ... \n), and if sentences are too long, on clauses (, ; : -).
    """
    paragraphs = text.split("\n\n")
    chunks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Split on sentence boundaries
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

                # If sentence itself is longer than max_chars, split on commas/clauses
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


def get_voice_clone_info(
    voice_name: Optional[str] = None,
    ref_audio_path: Optional[str] = None,
    ref_text_path: Optional[str] = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Resolves voice name, ref_audio URL, and ref_text.
    If local ref_audio/txt are provided, uploads or links them.
    """
    # 1. Local files provided explicitly
    if ref_audio_path:
        audio_p = Path(ref_audio_path)
        if not audio_p.exists():
            raise FileNotFoundError(f"Reference audio file not found: {ref_audio_path}")
            
        ref_text = ""
        if ref_text_path and Path(ref_text_path).exists():
            ref_text = Path(ref_text_path).read_text(encoding="utf-8").strip()
            
        # Check if file exists in S3 or use voice name
        stem_name = audio_p.stem
        return stem_name, None, ref_text

    # 2. Voice name lookup
    target_voice = voice_name or DEFAULT_VOICE
    return target_voice, None, None


class OmniVoiceReader:
    """Master controller for long text chunking, TTS synthesis, and audio stitching."""

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        ref_audio: Optional[str] = None,
        ref_text: Optional[str] = None,
        engine: str = DEFAULT_ENGINE,
        server_url: str = DEFAULT_OMNIVOICE_URL,
        max_chunk_chars: int = 380,
        pause_ms: int = 350,
        max_workers: int = 3,
        output_format: str = "mp3",
        bitrate: str = "192k",
    ):
        self.voice_name, self.custom_ref_audio_url, self.custom_ref_text = get_voice_clone_info(
            voice_name=voice,
            ref_audio_path=ref_audio,
            ref_text_path=ref_text
        )
        self.engine = engine
        self.server_url = server_url.rstrip("/")
        self.max_chunk_chars = max_chunk_chars
        self.pause_ms = pause_ms
        self.max_workers = max_workers
        self.output_format = output_format.lower()
        self.bitrate = bitrate
        self._find_ffmpeg()

    def _find_ffmpeg(self):
        """Locate ffmpeg binary on the system."""
        for p in [os.environ.get("FFMPEG", ""), os.path.expanduser("~/.local/bin/ffmpeg"), "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg", "ffmpeg"]:
            if p and (shutil.which(p) or (os.path.isfile(p) and os.access(p, os.X_OK))):
                self.ffmpeg = p
                return
        self.ffmpeg = "ffmpeg"

    def synthesize_single_chunk(
        self,
        chunk_text: str,
        output_wav: Path,
        retry_count: int = 2
    ) -> bool:
        """Call OmniVoice TTS API for a single chunk."""
        if output_wav.exists() and output_wav.stat().st_size > 1000:
            return True

        payload = {
            "text": chunk_text,
            "voice": self.voice_name,
            "engine": self.engine,
        }
        if self.custom_ref_text:
            payload["ref_text"] = self.custom_ref_text

        data_bytes = json.dumps(payload).encode("utf-8")
        
        for attempt in range(retry_count + 1):
            try:
                req = urllib.request.Request(
                    self.server_url,
                    data=data_bytes,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    if resp.status == 200:
                        raw_data = resp.read()
                        audio_data = None
                        
                        # Check if response is JSON metadata with download_url
                        if raw_data.startswith(b"{") or raw_data.startswith(b"["):
                            try:
                                res_json = json.loads(raw_data.decode("utf-8"))
                                dl_url = res_json.get("download_url") or res_json.get("audio_url")
                                if dl_url:
                                    with urllib.request.urlopen(dl_url, timeout=60) as dl_resp:
                                        audio_data = dl_resp.read()
                            except Exception as json_err:
                                logger.warning(f"Failed to parse JSON download_url: {json_err}")
                        elif len(raw_data) > 1000:
                            audio_data = raw_data

                        if audio_data and len(audio_data) > 1000:
                            with open(output_wav, "wb") as f:
                                f.write(audio_data)
                            return True
            except Exception as e:
                logger.error(f"TTS attempt {attempt+1} failed: {e}")
                if attempt == retry_count:
                    logger.error(f"TTS synthesis failed for chunk: '{chunk_text[:50]}...' -> {e}")
                    return False
                time.sleep(1.0 * (attempt + 1))
        return False

    def process_file(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        export_srt: bool = True
    ) -> Path:
        """Read long text file, synthesize all chunks in parallel, and stitch into master audio."""
        start_time = time.time()
        raw_text = input_file.read_text(encoding="utf-8")
        clean_text = clean_transcript_text(raw_text)
        
        if not clean_text:
            raise ValueError(f"Input file {input_file} has no readable text content.")

        chunks = split_text_into_chunks(clean_text, max_chars=self.max_chunk_chars)
        logger.info(
            f"Input file: '{input_file.name}' | Total Characters: {len(clean_text):,} | Total Chunks: {len(chunks)}"
        )
        logger.info(f"Using Voice: '{self.voice_name}' on OmniVoice GPU container.")

        if not output_file:
            safe_stem = sanitize_filename(input_file.stem)
            output_dir = input_file.parent / "audiobooks"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{safe_stem}_{sanitize_filename(self.voice_name)}.{self.output_format}"

        output_file.parent.mkdir(parents=True, exist_ok=True)
        cache_dir = output_file.parent / ".chunk_cache" / sanitize_filename(output_file.stem)
        cache_dir.mkdir(parents=True, exist_ok=True)
        chunk_files = [cache_dir / f"chunk_{i:04d}.wav" for i in range(len(chunks))]
        
        # Check how many are already in cache
        cached_count = sum(1 for f in chunk_files if f.exists() and f.stat().st_size > 1000)
        if cached_count > 0:
            logger.info(f"Found {cached_count}/{len(chunks)} pre-synthesized chunks in cache.")

        # Progress Tracking
        logger.info(f"Synthesizing {len(chunks) - cached_count} pending chunks with {self.max_workers} worker threads...")
        failed_indices = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {}
            for i in range(len(chunks)):
                if chunk_files[i].exists() and chunk_files[i].stat().st_size > 1000:
                    continue
                future_to_idx[executor.submit(self.synthesize_single_chunk, chunks[i], chunk_files[i])] = i
            
            completed_count = cached_count
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                success = future.result()
                if success:
                    completed_count += 1
                    if completed_count % 10 == 0 or completed_count == len(chunks):
                        pct = (completed_count / len(chunks)) * 100
                        logger.info(f"Progress: [{completed_count}/{len(chunks)}] chunks synthesized ({pct:.1f}%)...")
                else:
                    failed_indices.append(idx)

        if failed_indices:
            logger.warning(f"{len(failed_indices)} chunks failed. Retrying failed chunks sequentially...")
            for idx in failed_indices:
                ok = self.synthesize_single_chunk(chunks[idx], chunk_files[idx], retry_count=3)
                if not ok:
                    raise RuntimeError(f"Could not synthesize chunk {idx}: '{chunks[idx][:40]}...'")

        # Stitch chunks with natural silence pause
        logger.info("Stitching all synthesized chunks into master audio...")
        self._stitch_audio_chunks(chunk_files, chunks, output_file, export_srt)

        elapsed = time.time() - start_time
        size_mb = output_file.stat().st_size / (1024 * 1024)
        logger.info(
            f" [✓] Audio successfully created: {output_file} ({size_mb:.2f} MB) in {elapsed:.1f}s"
        )
        return output_file

    def _stitch_audio_chunks(
        self,
        chunk_files: List[Path],
        chunks: List[str],
        output_file: Path,
        export_srt: bool
    ):
        """Concatenate WAV chunks with silence padding using ffmpeg and generate synced SRT."""
        tmp_dir = chunk_files[0].parent
        
        # 1. Generate silence WAV
        silence_wav = tmp_dir / "silence.wav"
        silence_sec = max(self.pause_ms / 1000.0, 0.05)
        subprocess.run([
            self.ffmpeg, "-y", "-f", "lavfi",
            "-i", f"anullsrc=r=24000:cl=mono",
            "-t", str(silence_sec),
            str(silence_wav)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 2. Write concat list and compute timing for SRT
        concat_list = tmp_dir / "concat.txt"
        srt_entries = []
        cur_time_sec = 0.0

        with open(concat_list, "w", encoding="utf-8") as f:
            for i, c_file in enumerate(chunk_files):
                f.write(f"file '{c_file.resolve()}'\n")
                
                # Get chunk duration using ffprobe
                dur = self._get_audio_duration(c_file)
                start_ts = format_timestamp(cur_time_sec)
                end_ts = format_timestamp(cur_time_sec + dur)
                
                srt_entries.append(f"{i+1}\n{start_ts} --> {end_ts}\n{chunks[i]}\n")
                cur_time_sec += dur

                # Add silence between chunks (except after the last chunk)
                if i < len(chunk_files) - 1:
                    f.write(f"file '{silence_wav.resolve()}'\n")
                    cur_time_sec += silence_sec

        # 3. Render Final Master Audio
        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
        ]
        
        if self.output_format == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", self.bitrate])
        elif self.output_format == "m4a":
            cmd.extend(["-c:a", "aac", "-b:a", self.bitrate])
        elif self.output_format == "wav":
            cmd.extend(["-c:a", "pcm_s16le"])
            
        cmd.append(str(output_file))
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 4. Save synced SRT subtitle if requested
        if export_srt:
            srt_path = output_file.with_suffix(".srt")
            with open(srt_path, "w", encoding="utf-8") as sf:
                sf.write("\n".join(srt_entries))
            logger.info(f" [✓] Synced SRT subtitle saved: {srt_path}")

    def _get_audio_duration(self, audio_path: Path) -> float:
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
            # Fallback estimation based on size for 24kHz 16-bit mono WAV (~48kB/s)
            size = audio_path.stat().st_size
            return max(size / 48000.0, 1.0)


def parse_args():
    parser = argparse.ArgumentParser(
        description="OmniVoice Long Text Reader — Convert long text/transcripts to high-quality cloned voiceover audio."
    )
    parser.add_argument(
        "file",
        help="Input text file path (e.g. transcript.txt or book.txt)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output audio file path (.mp3, .wav, .m4a)"
    )
    parser.add_argument(
        "-v", "--voice",
        default=DEFAULT_VOICE,
        help=f"Voice name (default: '{DEFAULT_VOICE}')"
    )
    parser.add_argument(
        "--ref-audio",
        help="Path to local reference audio sample (.mp3 / .wav) for custom voice cloning"
    )
    parser.add_argument(
        "--ref-text",
        help="Path to local reference text matching the ref-audio"
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=380,
        help="Maximum characters per chunk (default: 380)"
    )
    parser.add_argument(
        "--pause-ms",
        type=int,
        default=350,
        help="Silence pause between chunks in milliseconds (default: 350ms)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Parallel worker threads for synthesis (default: 3)"
    )
    parser.add_argument(
        "--format",
        choices=["mp3", "wav", "m4a"],
        default="mp3",
        help="Output audio container format (default: mp3)"
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="Audio encoding bitrate (default: 192k)"
    )
    parser.add_argument(
        "--no-srt",
        action="store_true",
        help="Do not export matching synced .srt subtitle file"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_p = Path(args.file)
    if not input_p.exists():
        logger.error(f"Input file not found: {args.file}")
        sys.exit(1)

    out_p = Path(args.output) if args.output else None

    reader = OmniVoiceReader(
        voice=args.voice,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        max_chunk_chars=args.max_chars,
        pause_ms=args.pause_ms,
        max_workers=args.workers,
        output_format=args.format,
        bitrate=args.bitrate,
    )
    reader.process_file(
        input_file=input_p,
        output_file=out_p,
        export_srt=not args.no_srt
    )


if __name__ == "__main__":
    main()
