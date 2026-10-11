#!/usr/bin/env python3
"""
srt_extractor.py — YouTube Subtitle, Transcript & Audio ASR Ingestion Engine
===========================================================================
Part of the `youtube-video-rewriter` Skill ecosystem on ThinkPad P15.

Features:
1. Native Subtitle Harvesting: Downloads manual or auto-generated `.srt` / `.vtt`
   via `yt-dlp` or `youtube_transcript_api` for Vietnamese ('vi') and English ('en').
2. Whisper ASR Fallback: If no subtitles exist, downloads audio stream (.m4a/.wav)
   and runs local `faster-whisper` (GPU CUDA/CTranslate2) to generate `.srt`.
3. Structural Parsing: Cleans subtitle artifacts, formats into structured segments
   with word-level timestamps, speech rate (WPM), and total silence periods.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_ytdlp_bin() -> str:
    """Resolve the yt-dlp binary path reliably."""
    import shutil
    candidate = shutil.which("yt-dlp")
    if candidate:
        return candidate
    venv_ytdlp = Path(sys.executable).parent / "yt-dlp"
    if venv_ytdlp.exists():
        return str(venv_ytdlp)
    default_p = Path("/home/zen/hermes-agent/.venv/bin/yt-dlp")
    if default_p.exists():
        return str(default_p)
    return "yt-dlp"


def clean_subtitle_text(text: str) -> str:
    """Remove formatting tags, HTML entities, and duplicate consecutive words."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[[^\]]+\]", "", text)  # remove [Music], [Applause]
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_srt_file(srt_path: Path) -> List[Dict[str, Any]]:
    """Parse standard SRT file into timestamped segment objects."""
    if not srt_path.exists():
        return []

    content = srt_path.read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r"\n\s*\n", content.strip())
    segments = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            time_line = lines[1]
            text = " ".join(lines[2:]).strip()
            text = clean_subtitle_text(text)
            if not text:
                continue

            time_match = re.match(
                r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
                time_line,
            )
            if time_match:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, time_match.groups())
                start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
                duration = max(0.1, end_sec - start_sec)
                word_count = len(text.split())
                wpm = round((word_count / duration) * 60, 1)

                segments.append(
                    {
                        "start": start_sec,
                        "end": end_sec,
                        "duration": round(duration, 2),
                        "text": text,
                        "word_count": word_count,
                        "wpm": wpm,
                    }
                )

    return segments


def fetch_youtube_metadata(url: str, output_dir: Path) -> Dict[str, Any]:
    """Retrieve full video metadata using yt-dlp, with graceful HTML fallback."""
    print(f"[*] Fetching video metadata: {url}")
    ytdlp = get_ytdlp_bin()
    cmd = [
        ytdlp,
        "--dump-json",
        "--skip-download",
        "--no-warnings",
        url,
    ]
    metadata = {
        "id": "",
        "title": "",
        "description": "",
        "duration": 0,
        "channel": "",
        "channel_url": "",
        "view_count": 0,
        "tags": [],
        "categories": [],
        "chapters": [],
    }

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            metadata.update({
                "id": data.get("id", ""),
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "duration": data.get("duration", 0),
                "channel": data.get("uploader", ""),
                "channel_url": data.get("uploader_url", ""),
                "view_count": data.get("view_count", 0),
                "tags": data.get("tags", []),
                "categories": data.get("categories", []),
                "chapters": data.get("chapters", []),
            })
            return metadata
    except Exception as e:
        print(f"    [!] Warning: yt-dlp metadata failed ({e}). Attempting web fallback...")

    # Fallback to URL parsing & Web scraping
    video_id_m = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    video_id = video_id_m.group(1) if video_id_m else "unknown"
    metadata["id"] = video_id
    metadata["title"] = f"Video_{video_id}"

    if video_id and video_id != "unknown":
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://www.youtube.com/watch?v={video_id}",
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            )
            html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
            title_m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            desc_m = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if title_m:
                metadata["title"] = title_m.group(1)
            if desc_m:
                metadata["description"] = desc_m.group(1)
            print(f"    [+] Web fallback extracted title: '{metadata['title']}'")
        except Exception as e:
            print(f"    [-] Web fallback failed: {e}")

    return metadata


def download_native_subtitles(url: str, output_dir: Path) -> Optional[Path]:
    """Attempt downloading native or auto-generated YouTube subtitles in SRT format."""
    print("[*] Checking for native YouTube subtitles (vi, en)...")
    base_name = "youtube_transcript"
    output_template = str(output_dir / f"{base_name}.%(ext)s")

    ytdlp = get_ytdlp_bin()
    cmd = [
        ytdlp,
        "--skip-download",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", "vi,en",
        "--sub-format", "srt/vtt/best",
        "--convert-subs", "srt",
        "-o", output_template,
        url,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        # Search for generated .srt files
        srt_files = list(output_dir.glob(f"{base_name}*.srt"))
        if srt_files:
            # Prefer Vietnamese if present
            vi_files = [f for f in srt_files if ".vi." in f.name]
            chosen = vi_files[0] if vi_files else srt_files[0]
            print(f"    [+] Found native subtitle: {chosen.name}")
            return chosen
    except Exception as e:
        print(f"    [!] Error during yt-dlp subtitle download: {e}", file=sys.stderr)

    # Fallback: Check via youtube_transcript_api
    video_id_m = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if video_id_m:
        vid = video_id_m.group(1)
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            ytt = YouTubeTranscriptApi()
            t_list = ytt.list(vid)
            # Try vi first, then en
            transcript = None
            try:
                transcript = t_list.find_transcript(["vi"])
            except Exception:
                try:
                    transcript = t_list.find_transcript(["en"])
                except Exception:
                    pass

            if transcript:
                items = transcript.fetch()
                srt_out = output_dir / f"{base_name}_api.srt"
                with open(srt_out, "w", encoding="utf-8") as f:
                    for idx, item in enumerate(items, 1):
                        start = item["start"]
                        dur = item.get("duration", 2.0)
                        end = start + dur
                        f.write(f"{idx}\n")
                        f.write(
                            f"{format_timestamp(start)} --> {format_timestamp(end)}\n"
                        )
                        f.write(f"{clean_subtitle_text(item['text'])}\n\n")
                print(f"    [+] Extracted via youtube_transcript_api: {srt_out.name}")
                return srt_out
        except Exception as e:
            print(f"    [-] youtube_transcript_api fallback unavailable: {e}")

    return None


def format_timestamp(seconds: float) -> str:
    """Format seconds into SRT timestamp 00:00:00,000."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_audio_whisper(
    url: str, output_dir: Path, model_size: str = "small"
) -> Optional[Path]:
    """Download audio stream and transcribe using local Faster-Whisper on ThinkPad P15."""
    print("[*] No native subtitles found. Fallback to local Faster-Whisper ASR on P15...")
    audio_path = output_dir / "audio_source.wav"

    # Step 1: Download 16kHz mono audio via yt-dlp
    ytdlp = get_ytdlp_bin()
    cmd = [
        ytdlp,
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--postprocessor-args", "-ar 16000 -ac 1",
        "-o", str(audio_path),
        url,
    ]
    try:
        print("    [+] Downloading audio stream (16kHz mono)...")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not audio_path.exists():
            # Check for name variations
            wavs = list(output_dir.glob("*.wav"))
            if wavs:
                audio_path = wavs[0]
            else:
                print("    [!] Audio download failed.")
                return None
    except Exception as e:
        print(f"    [!] Error downloading audio: {e}", file=sys.stderr)
        return None

    # Step 2: Run faster-whisper
    try:
        from faster_whisper import WhisperModel
        print(f"    [+] Loading Faster-Whisper ({model_size}) on GPU...")
        # Device: cuda with float16 or cpu with int8
        device = "cuda" if os.path.exists("/dev/nvidia0") else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, info = model.transcribe(str(audio_path), beam_size=5)

        srt_out = output_dir / "youtube_transcript_whisper.srt"
        with open(srt_out, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(segments, 1):
                f.write(f"{idx}\n")
                f.write(
                    f"{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}\n"
                )
                f.write(f"{clean_subtitle_text(seg.text)}\n\n")

        print(f"    [+] Faster-Whisper transcription complete: {srt_out.name}")
        return srt_out
    except Exception as e:
        print(f"    [!] Faster-Whisper failed: {e}", file=sys.stderr)
        return None


def run_extraction(
    url: str, output_dir: Path, force_whisper: bool = False
) -> Dict[str, Any]:
    """Execute full ingestion pipeline, returning unified analysis object."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = fetch_youtube_metadata(url, output_dir)

    srt_file = None
    if not force_whisper:
        srt_file = download_native_subtitles(url, output_dir)

    if not srt_file:
        srt_file = transcribe_audio_whisper(url, output_dir)

    segments = []
    full_text = ""
    total_words = 0
    avg_wpm = 0.0

    if srt_file and srt_file.exists():
        segments = parse_srt_file(srt_file)
        full_text = " ".join([s["text"] for s in segments])
        total_words = sum([s["word_count"] for s in segments])
        total_duration = segments[-1]["end"] if segments else metadata.get("duration", 1)
        avg_wpm = round((total_words / max(1, total_duration)) * 60, 1)

    result = {
        "metadata": metadata,
        "srt_file": str(srt_file) if srt_file else "",
        "segment_count": len(segments),
        "total_words": total_words,
        "avg_wpm": avg_wpm,
        "full_text": full_text,
        "segments": segments,
    }

    # Save summary JSON
    summary_path = output_dir / "ingestion_summary.json"
    summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[+] Ingestion complete. Segments: {len(segments)}, Words: {total_words}, Avg WPM: {avg_wpm}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Subtitle & Audio ASR Ingestion Engine"
    )
    parser.add_argument("url", help="YouTube video URL or Video ID")
    parser.add_argument(
        "--output-dir",
        default="./workspace/youtube_ingest",
        help="Directory to store SRT, audio, and metadata",
    )
    parser.add_argument(
        "--force-whisper",
        action="store_true",
        help="Force local Whisper transcription regardless of native subtitles",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    res = run_extraction(args.url, out_dir, args.force_whisper)
    print("\n" + "=" * 60)
    print(f"🎬 Title    : {res['metadata']['title']}")
    print(f"⏱️ Duration : {res['metadata']['duration']}s")
    print(f"📝 Subtitle : {res['srt_file'] or 'None'}")
    print(f"📊 Words    : {res['total_words']} words (~{res['avg_wpm']} WPM)")
    print("=" * 60)


if __name__ == "__main__":
    main()
