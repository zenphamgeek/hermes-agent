#!/usr/bin/env python3
"""Generate simple SRT subtitles from text content.

For Edge-TTS output that doesn't support stream-mode subtitles,
this generates evenly-timed subtitle blocks.

Usage:
    python gen_subtitles.py --text "Content here" --duration 30 --output subs.srt
    python gen_subtitles.py --file script.txt --duration 30 --output subs.srt
"""

import argparse
import re
import sys
from pathlib import Path


def text_to_srt(text: str, total_duration: float, output_path: str):
    """Generate SRT subtitles from text with even timing."""
    # Split text into subtitle chunks (max ~10 words each)
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        # Break on sentence-ending punctuation or after 8-10 words
        if (len(current_chunk) >= 8 or
                word.endswith('.') or word.endswith('!') or
                word.endswith('?') or word.endswith(',')):
            chunks.append(' '.join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    if not chunks:
        print("No text to subtitle")
        sys.exit(1)

    # Calculate timing
    time_per_chunk = total_duration / len(chunks)

    srt_lines = []
    for i, chunk in enumerate(chunks):
        start_time = i * time_per_chunk
        end_time = min((i + 1) * time_per_chunk, total_duration)

        start_str = _format_srt_time(start_time)
        end_str = _format_srt_time(end_time)

        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(chunk)
        srt_lines.append("")

    srt_content = '\n'.join(srt_lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)

    print(f"Generated {len(chunks)} subtitle blocks ({total_duration:.1f}s) → {output_path}")


def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main():
    parser = argparse.ArgumentParser(description="Generate SRT subtitles from text")
    parser.add_argument("--text", help="Text content to subtitle")
    parser.add_argument("--file", help="File containing text to subtitle")
    parser.add_argument("--duration", type=float, required=True, help="Total audio duration in seconds")
    parser.add_argument("--output", required=True, help="Output SRT file path")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding='utf-8')
    elif args.text:
        text = args.text
    else:
        print("Provide --text or --file")
        sys.exit(1)

    # Clean up script markers
    text = re.sub(r'\[HOOK\]|\[NỘI DUNG\]|\[CTA\]', '', text)
    text = text.strip()

    text_to_srt(text, args.duration, args.output)


if __name__ == "__main__":
    main()
