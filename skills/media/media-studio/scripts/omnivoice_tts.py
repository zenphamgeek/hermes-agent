#!/usr/bin/env python3
"""OmniVoice TTS client — Generate voiceover using local voice cloning.

Uses the OmniVoice Unified TTS Portal running on the P15 LXC container
(10.123.214.178:80) with voice cloning from reference audio samples.

Usage:
    python omnivoice_tts.py --text "Nội dung cần đọc" --voice "dũng" --output voiceover.wav
    python omnivoice_tts.py --file script.txt --voice "dũng" --output voiceover.wav
    python omnivoice_tts.py --list-voices
    python omnivoice_tts.py --health
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None
    import urllib.request
    import urllib.error


# OmniVoice server on P15 LXC
OMNIVOICE_HOST = os.environ.get("OMNIVOICE_HOST", "10.123.214.178")
OMNIVOICE_PORT = os.environ.get("OMNIVOICE_PORT", "80")
OMNIVOICE_BASE = os.environ.get("OMNIVOICE_BASE_URL", f"http://{OMNIVOICE_HOST}:{OMNIVOICE_PORT}").rstrip("/")

# Default voice for ZENPHAM brand
DEFAULT_VOICE = "dũng - poetic, deep and resonant"
DEFAULT_ENGINE = "omnivoice"  # local GPU engine

# Max text length per request (split longer texts)
MAX_CHUNK_CHARS = 500


def _request(method, path, json_data=None, output_file=None, timeout=120):
    """Make HTTP request to OmniVoice server."""
    url = f"{OMNIVOICE_BASE}{path}"

    if requests:
        if method == "GET":
            resp = requests.get(url, timeout=timeout)
        elif method == "POST":
            resp = requests.post(url, json=json_data, timeout=timeout, stream=bool(output_file))
        else:
            raise ValueError(f"Unsupported method: {method}")

        if output_file and resp.status_code == 200:
            with open(output_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            # If server returned JSON with download_url (cache hit)
            if os.path.exists(output_file) and os.path.getsize(output_file) < 4096:
                try:
                    with open(output_file, "r", encoding="utf-8") as jf:
                        jdata = json.load(jf)
                    if isinstance(jdata, dict) and "download_url" in jdata:
                        dl = requests.get(jdata["download_url"], timeout=60)
                        if dl.status_code == 200 and len(dl.content) > 1000:
                            with open(output_file, "wb") as f:
                                f.write(dl.content)
                except Exception:
                    pass
            return {"status": "ok", "file": output_file, "size": os.path.getsize(output_file)}

        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code, "raw": resp.text[:500]}
    else:
        # urllib fallback
        if method == "GET":
            req = urllib.request.Request(url)
        elif method == "POST":
            body = json.dumps(json_data).encode() if json_data else None
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if output_file and resp.status == 200:
                    with open(output_file, "wb") as f:
                        while True:
                            chunk = resp.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                    return {"status": "ok", "file": output_file, "size": os.path.getsize(output_file)}
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return {"status": "error", "code": e.code, "error": e.read().decode()[:500]}
        except Exception as e:
            return {"status": "error", "error": str(e)}


def cmd_health(args):
    """Check OmniVoice server health."""
    result = _request("GET", "/health")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if isinstance(result, dict):
        engines = result.get("engines", {})
        omni = engines.get("omnivoice", {})
        if omni.get("status") == "ok":
            sys.exit(0)
    sys.exit(1)


def cmd_list_voices(args):
    """List available voices."""
    result = _request("GET", "/voices")
    if isinstance(result, dict):
        for engine_name, engine_data in result.items():
            voices = engine_data.get("voices", [])
            engine_type = engine_data.get("type", "unknown")
            engine_label = engine_data.get("engine", engine_name)
            print(f"\n{'='*60}")
            print(f"Engine: {engine_label} ({engine_type})")
            print(f"{'='*60}")
            for v in voices:
                if isinstance(v, dict):
                    name = v.get("name", "unknown")
                    ref_text = v.get("ref_text", "")[:60]
                else:
                    name = str(v)
                    ref_text = ""
                print(f"  🎤 {name}")
                if ref_text:
                    print(f"     ref: \"{ref_text}...\"")
    else:
        print(json.dumps(result, indent=2))


def _split_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list:
    """Split text into chunks at sentence boundaries."""
    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk = f"{current_chunk} {sentence}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If single sentence is too long, split by comma
            if len(sentence) > max_chars:
                sub_parts = sentence.split(", ")
                sub_chunk = ""
                for part in sub_parts:
                    if len(sub_chunk) + len(part) + 2 <= max_chars:
                        sub_chunk = f"{sub_chunk}, {part}".strip(", ")
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = part
                if sub_chunk:
                    chunks.append(sub_chunk)
                current_chunk = ""
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [text]


def cmd_tts(args):
    """Generate TTS audio using OmniVoice with voice cloning."""
    # Load text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text.strip()
    else:
        print(json.dumps({"status": "error", "error": "Provide --text or --file"}))
        sys.exit(1)

    # Clean up script markers
    text = re.sub(r'\[HOOK\]|\[NỘI DUNG\]|\[CTA\]', '', text)
    text = text.strip()

    voice = args.voice or DEFAULT_VOICE
    engine = args.engine or DEFAULT_ENGINE
    output = args.output

    # Determine output format
    output_path = Path(output)
    output_format = output_path.suffix.lstrip(".")
    if output_format not in ("wav", "mp3", "ogg"):
        output_format = "wav"

    # Split long text into chunks
    chunks = _split_text(text)

    if len(chunks) == 1:
        # Single request
        print(f"Generating TTS ({len(text)} chars, voice: {voice})...", file=sys.stderr)
        payload = {
            "text": text,
            "voice": voice,
            "engine": engine,
        }

        result = _request("POST", "/tts", json_data=payload, output_file=output, timeout=180)

        if result.get("status") == "ok":
            size = result.get("size", 0)
            print(json.dumps({
                "status": "ok",
                "output": output,
                "size_bytes": size,
                "voice": voice,
                "engine": engine,
                "chunks": 1,
            }))
        else:
            print(json.dumps({"status": "error", "error": str(result)}))
            sys.exit(1)
    else:
        # Multi-chunk: generate each chunk, then concatenate
        import tempfile
        import subprocess

        tmp_dir = tempfile.mkdtemp(prefix="omnivoice-")
        chunk_files = []

        for i, chunk_text in enumerate(chunks):
            chunk_file = os.path.join(tmp_dir, f"chunk_{i:03d}.wav")
            print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk_text)} chars)...", file=sys.stderr)

            payload = {
                "text": chunk_text,
                "voice": voice,
                "engine": engine,
            }

            result = _request("POST", "/tts", json_data=payload, output_file=chunk_file, timeout=180)

            if result.get("status") == "ok":
                chunk_files.append(chunk_file)
            else:
                print(f"  ⚠ Chunk {i+1} failed: {result}", file=sys.stderr)

        if not chunk_files:
            print(json.dumps({"status": "error", "error": "All chunks failed"}))
            sys.exit(1)

        # Concatenate with FFmpeg
        ffmpeg = os.environ.get("FFMPEG", "ffmpeg")
        for loc in [os.path.expanduser("~/.local/bin/ffmpeg"), "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
            if os.path.isfile(loc) and os.access(loc, os.X_OK):
                ffmpeg = loc
                break

        concat_list = os.path.join(tmp_dir, "concat.txt")
        with open(concat_list, "w") as f:
            for cf in chunk_files:
                f.write(f"file '{cf}'\n")

        concat_cmd = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c:a", "pcm_s16le" if output_format == "wav" else "libmp3lame",
            output,
        ]

        subprocess.run(concat_cmd, capture_output=True, check=True)

        # Cleanup
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

        size = os.path.getsize(output)
        print(json.dumps({
            "status": "ok",
            "output": output,
            "size_bytes": size,
            "voice": voice,
            "engine": engine,
            "chunks": len(chunks),
        }))


def main():
    parser = argparse.ArgumentParser(description="OmniVoice TTS Client")
    parser.add_argument("--health", action="store_true", help="Check server health")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--text", help="Text to synthesize")
    parser.add_argument("--file", help="File containing text to synthesize")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"Voice name (default: {DEFAULT_VOICE})")
    parser.add_argument("--engine", default=DEFAULT_ENGINE, help=f"TTS engine (default: {DEFAULT_ENGINE})")
    parser.add_argument("--output", default="voiceover.wav", help="Output file path")
    args = parser.parse_args()

    if args.health:
        cmd_health(args)
    elif args.list_voices:
        cmd_list_voices(args)
    elif args.text or args.file:
        cmd_tts(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
