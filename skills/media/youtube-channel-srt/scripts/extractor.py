#!/usr/bin/env python3
"""
YouTube Channel SRT Extractor (Anti-Bot Resilient & Scheduled)
-------------------------------------------------------------
Downloads all subtitles/transcripts (.srt) from a YouTube channel, playlist, or video list.
If a video lacks YouTube subtitles (manual or auto-captions), automatically extracts audio
and runs WhisperX (with GPU CUDA acceleration, VAD batching, and word-level alignment) to generate SRT.

Anti-Bot & Scheduling Features:
- Mobile player client spoofing (android, ios, mweb) to bypass web bot checks
- Smart rate-limiting & randomized jitter delays (avoids 429 / Sign-in bot triggers)
- Cookies support (--cookies or --cookies-from-browser)
- Batch chunking with rest intervals
- Scheduled continuous monitoring (--loop --interval)
- Exponential backoff retry on temporary blocks
- Resumable SQLite & JSON manifest state store
"""

import argparse
import concurrent.futures
import json
import logging
import os
import random
import re
import shutil
import signal
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Third-party imports
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    import torch
except ImportError:
    torch = None

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
except ImportError:
    console = None

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("yt_channel_srt")


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


def parse_vtt_to_srt(vtt_content: str) -> str:
    """
    Convert WebVTT content to standard SRT format.
    Strips VTT headers, cue settings, HTML styling tags, and deduplicates rolling captions.
    """
    lines = vtt_content.splitlines()
    srt_entries = []
    
    ts_pattern = re.compile(
        r"^(?:(\d{1,2}):)?(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})\.(\d{3})"
    )
    
    idx = 0
    i = 0
    last_text = ""
    
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE") or line.startswith("STYLE") or line.startswith("REGION"):
            continue
            
        ts_match = ts_pattern.match(line)
        if ts_match:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = ts_match.groups()
            h1 = int(h1) if h1 else 0
            h2 = int(h2) if h2 else 0
            
            start_ts = f"{h1:02d}:{int(m1):02d}:{int(s1):02d},{ms1}"
            end_ts = f"{h2:02d}:{int(m2):02d}:{int(s2):02d},{ms2}"
            
            text_lines = []
            while i < len(lines):
                cur = lines[i].strip()
                if not cur:
                    i += 1
                    break
                if ts_pattern.match(cur):
                    break
                cleaned_cur = re.sub(r"<[^>]+>", "", cur).strip()
                if cleaned_cur and cleaned_cur not in text_lines:
                    text_lines.append(cleaned_cur)
                i += 1
                
            entry_text = "\n".join(text_lines).strip()
            if entry_text and entry_text != last_text:
                idx += 1
                srt_entries.append(f"{idx}\n{start_ts} --> {end_ts}\n{entry_text}\n")
                last_text = entry_text

    return "\n".join(srt_entries)


def json3_to_srt(json3_data: dict) -> str:
    """Convert YouTube json3 subtitle format to standard SRT."""
    events = json3_data.get("events", [])
    srt_entries = []
    idx = 0
    
    for ev in events:
        tStartMs = ev.get("tStartMs", 0)
        dDurationMs = ev.get("dDurationMs", 0)
        segs = ev.get("segs", [])
        
        text = "".join([s.get("utf8", "") for s in segs if "utf8" in s]).strip()
        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text or text == "\n":
            continue
            
        start_sec = tStartMs / 1000.0
        end_sec = (tStartMs + dDurationMs) / 1000.0
        
        idx += 1
        srt_entries.append(
            f"{idx}\n{format_timestamp(start_sec)} --> {format_timestamp(end_sec)}\n{text}\n"
        )
        
    return "\n".join(srt_entries)


class WhisperXEngine:
    """Lazy-loaded, GPU-optimized WhisperX transcription engine."""
    
    def __init__(
        self,
        model_size: str = "large-v2",
        device: str = "auto",
        compute_type: str = "auto",
        batch_size: int = 16,
        align: bool = True,
    ):
        self.model_size = model_size
        self.device = self._resolve_device(device)
        self.compute_type = self._resolve_compute_type(compute_type)
        self.batch_size = batch_size
        self.align = align
        self.model = None
        self._align_models = {}
        
    def _resolve_device(self, req: str) -> str:
        if req and req != "auto":
            return req
        if torch and torch.cuda.is_available():
            return "cuda"
        return "cpu"
        
    def _resolve_compute_type(self, req: str) -> str:
        if req and req != "auto":
            return req
        if self.device == "cuda":
            return "float16"
        return "int8"
        
    def _load_model_if_needed(self):
        if self.model is not None:
            return
            
        logger.info(
            f"Loading WhisperX model '{self.model_size}' on device={self.device}, compute_type={self.compute_type}..."
        )
        try:
            import whisperx
            self.model = whisperx.load_model(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                vad_options={"vad_onset": 0.500, "vad_offset": 0.363}
            )
            logger.info("WhisperX model loaded successfully on GPU.")
        except Exception as e:
            logger.error(f"Failed to load WhisperX model: {e}")
            raise

    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Transcribe audio file to SRT content.
        Returns (srt_string, detected_language).
        """
        self._load_model_if_needed()
        import whisperx
        
        audio = whisperx.load_audio(audio_path)
        
        transcribe_args = {"batch_size": self.batch_size}
        if language and language not in ("auto", "all"):
            transcribe_args["language"] = language
            
        result = self.model.transcribe(audio, **transcribe_args)
        detected_lang = result.get("language", language or "unknown")
        
        segments = result.get("segments", [])
        if self.align and segments and detected_lang and detected_lang != "unknown":
            try:
                if detected_lang not in self._align_models:
                    model_a, metadata = whisperx.load_align_model(
                        language_code=detected_lang,
                        device=self.device
                    )
                    self._align_models[detected_lang] = (model_a, metadata)
                else:
                    model_a, metadata = self._align_models[detected_lang]
                    
                aligned_result = whisperx.align(
                    segments,
                    model_a,
                    metadata,
                    audio,
                    self.device,
                    return_char_alignments=False
                )
                segments = aligned_result.get("segments", segments)
            except Exception as e:
                logger.warning(f"WhisperX alignment skipped ({e}), using standard VAD segments.")

        srt_lines = []
        for idx, seg in enumerate(segments, start=1):
            start = seg.get("start", 0.0)
            end = seg.get("end", start + 1.0)
            text = seg.get("text", "").strip()
            if not text:
                continue
            srt_lines.append(
                f"{idx}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n"
            )
            
        return "\n".join(srt_lines), detected_lang


class ManifestManager:
    """Manages persistent SQLite & JSON state store for resumable extraction."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.json_path = output_dir / "manifest.json"
        self.db_path = output_dir / "history.sqlite"
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    duration REAL,
                    source TEXT,
                    language TEXT,
                    srt_file TEXT,
                    status TEXT,
                    completed_at TEXT,
                    error_message TEXT
                )
            """)
            conn.commit()

    def get_completed_video_ids(self) -> set:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT video_id FROM videos WHERE status = 'completed'")
            return {row[0] for row in cursor.fetchall()}

    def record_video(
        self,
        video_id: str,
        title: str,
        url: str,
        duration: Optional[float],
        source: str,
        language: str,
        srt_file: str,
        status: str = "completed",
        error_message: Optional[str] = None,
    ):
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO videos 
                (video_id, title, url, duration, source, language, srt_file, status, completed_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (video_id, title, url, duration, source, language, srt_file, status, now_str, error_message))
            conn.commit()
        self._dump_json_manifest()

    def _dump_json_manifest(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos ORDER BY completed_at DESC")
            rows = cursor.fetchall()
            
        videos_dict = {}
        stats = {
            "total_records": len(rows),
            "completed": 0,
            "youtube_manual": 0,
            "youtube_auto": 0,
            "whisperx": 0,
            "failed": 0
        }
        
        for r in rows:
            d = dict(r)
            videos_dict[d["video_id"]] = d
            if d["status"] == "completed":
                stats["completed"] += 1
                src = d.get("source", "")
                if "manual" in src:
                    stats["youtube_manual"] += 1
                elif "auto" in src:
                    stats["youtube_auto"] += 1
                elif "whisperx" in src:
                    stats["whisperx"] += 1
            elif d["status"] == "failed":
                stats["failed"] += 1

        payload = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "stats": stats,
            "videos": videos_dict
        }
        
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


class ChannelSrtExtractor:
    """Master orchestrator for channel video enumeration, subtitle download, and WhisperX fallback."""
    
    def __init__(
        self,
        target_url: str,
        output_dir: Optional[str] = None,
        languages: str = "vi,en,auto",
        allow_auto_subs: bool = True,
        force_whisper: bool = False,
        whisper_model: str = "large-v2",
        whisper_device: str = "auto",
        whisper_compute_type: str = "auto",
        batch_size: int = 16,
        align: bool = True,
        max_workers: int = 2,
        limit: Optional[int] = None,
        include_shorts: bool = False,
        date_after: Optional[str] = None,
        date_before: Optional[str] = None,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
        chunk_size: int = 20,
        rest_seconds: float = 15.0,
        cookies: Optional[str] = None,
        cookies_from_browser: Optional[str] = None,
        keep_audio: bool = False,
        keep_video: bool = False,
        process_local: bool = False,
        export_txt: bool = True,
        export_jsonl: bool = True,
    ):
        self.raw_url = target_url.strip() if target_url else ""
        self.languages = [lang.strip().lower() for lang in languages.split(",") if lang.strip()]
        self.allow_auto_subs = allow_auto_subs
        self.force_whisper = force_whisper
        self.max_workers = max_workers
        self.limit = limit
        self.include_shorts = include_shorts
        self.date_after = date_after
        self.date_before = date_before
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.chunk_size = chunk_size
        self.rest_seconds = rest_seconds
        self.cookies = cookies
        self.cookies_from_browser = cookies_from_browser
        self.keep_audio = keep_audio
        self.keep_video = keep_video
        self.process_local = process_local
        self.export_txt = export_txt
        self.export_jsonl = export_jsonl
        
        self.channel_info = {}
        self.output_dir = Path(output_dir) if output_dir else None
        
        self.whisper_engine = WhisperXEngine(
            model_size=whisper_model,
            device=whisper_device,
            compute_type=whisper_compute_type,
            batch_size=batch_size,
            align=align,
        )
        self.manifest = None
        self._interrupted = False

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.manifest = ManifestManager(self.output_dir)

    def _get_base_ydl_opts(self) -> dict:
        """Construct standard ydl options with anti-bot mobile player clients and cookies."""
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios", "web"],
                }
            },
        }
        if self.cookies:
            opts["cookiefile"] = self.cookies
        if self.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        return opts

    def _sleep_jitter(self):
        """Randomized sleep between network requests to avoid bot triggers."""
        if self.delay_max > 0:
            jitter = random.uniform(self.delay_min, self.delay_max)
            time.sleep(jitter)

    def _get_target_urls_to_harvest(self) -> List[str]:
        """Normalize URL and determine target endpoints (/videos, /shorts, etc.)."""
        url = self.raw_url
        if url.startswith("@"):
            url = f"https://www.youtube.com/{url}"
        elif not url.startswith("http://") and not url.startswith("https://"):
            if url.startswith("UC"):
                url = f"https://www.youtube.com/channel/{url}"
            else:
                url = f"https://www.youtube.com/@{url}"

        if "/watch?" in url or "youtu.be/" in url or "/playlist?" in url:
            return [url]

        base_url = url.rstrip("/")
        if base_url.endswith(("/videos", "/shorts", "/streams", "/playlists", "/featured")):
            return [base_url]
        
        targets = [f"{base_url}/videos"]
        if self.include_shorts:
            targets.append(f"{base_url}/shorts")
        return targets

    def harvest_video_entries(self) -> List[Dict[str, Any]]:
        """Harvest all video metadata from the channel or playlist quickly."""
        target_urls = self._get_target_urls_to_harvest()
        logger.info(f"Harvesting video entries from {len(target_urls)} endpoint(s)...")
        
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts.update({
            "extract_flat": "in_playlist",
            "skip_download": True,
            "ignoreerrors": True,
        })
        
        if self.date_after:
            ydl_opts["daterange"] = yt_dlp.utils.DateRange(start=self.date_after, end=self.date_before)

        all_entries = []
        seen_ids = set()

        for harvest_url in target_urls:
            logger.info(f"Scanning: {harvest_url}")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(harvest_url, download=False)
            except Exception as e:
                logger.warning(f"Failed to scan {harvest_url}: {e}")
                continue
                
            if not info:
                continue
                
            if not self.channel_info:
                self.channel_info = {
                    "id": info.get("id"),
                    "title": info.get("title") or info.get("uploader") or info.get("channel") or "youtube_channel",
                    "url": self.raw_url,
                }

            if not self.output_dir:
                safe_channel_name = sanitize_filename(self.channel_info["title"])
                self.output_dir = Path(f"./output_srt/{safe_channel_name}")
                self.output_dir.mkdir(parents=True, exist_ok=True)
                self.manifest = ManifestManager(self.output_dir)

            if "entries" in info:
                for item in info["entries"]:
                    if not item:
                        continue
                    item_id = item.get("id")
                    if item_id and item_id not in seen_ids and len(item_id) == 11:
                        seen_ids.add(item_id)
                        all_entries.append({
                            "id": item_id,
                            "title": item.get("title") or item_id,
                            "url": f"https://www.youtube.com/watch?v={item_id}",
                            "duration": item.get("duration"),
                            "upload_date": item.get("upload_date"),
                        })
            else:
                item_id = info.get("id")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    all_entries.append({
                        "id": item_id,
                        "title": info.get("title") or item_id,
                        "url": info.get("webpage_url") or harvest_url,
                        "duration": info.get("duration"),
                        "upload_date": info.get("upload_date"),
                    })

        if not self.output_dir:
            safe_channel_name = sanitize_filename(self.channel_info.get("title", "youtube_channel"))
            self.output_dir = Path(f"./output_srt/{safe_channel_name}")
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.manifest = ManifestManager(self.output_dir)

        if self.limit and len(all_entries) > self.limit:
            all_entries = all_entries[:self.limit]
            
        logger.info(f"Discovered {len(all_entries)} unique videos for channel '{self.channel_info.get('title', 'Unknown')}'.")
        return all_entries

    def fetch_youtube_subtitles(self, video_id: str, video_url: str, retry_count: int = 2) -> Optional[Tuple[str, str, str]]:
        """
        Attempt to download YouTube subtitles (manual or auto-captions) directly with retry & backoff.
        Returns (srt_content, language, source_type) or None.
        """
        if self.force_whisper:
            return None

        self._sleep_jitter()
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts.update({
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": self.allow_auto_subs,
            "subtitlesformat": "vtt/json3/srt",
        })

        for attempt in range(retry_count + 1):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    if not info:
                        return None

                    subtitles = info.get("subtitles") or {}
                    auto_captions = info.get("automatic_captions") or {}

                    # 1. Manual subtitles
                    match = self._find_best_subtitle_track(subtitles)
                    if match:
                        lang, track_info = match
                        srt_text = self._download_and_convert_sub(track_info)
                        if srt_text:
                            return (srt_text, lang, "youtube_manual")

                    # 2. Auto-generated captions
                    if self.allow_auto_subs and auto_captions:
                        match = self._find_best_subtitle_track(auto_captions)
                        if match:
                            lang, track_info = match
                            srt_text = self._download_and_convert_sub(track_info)
                            if srt_text:
                                return (srt_text, lang, "youtube_auto")
                    return None

            except Exception as e:
                err_str = str(e).lower()
                if "bot" in err_str or "429" in err_str or "sign in" in err_str:
                    backoff = (attempt + 1) * 10
                    logger.warning(f"YouTube rate-limit/bot check hit on {video_id}. Pausing {backoff}s before retry ({attempt+1}/{retry_count})...")
                    time.sleep(backoff)
                else:
                    logger.debug(f"Subtitle check note for {video_id}: {e}")
                    return None

        return None

    def _find_best_subtitle_track(self, sub_dict: Dict[str, List[dict]]) -> Optional[Tuple[str, dict]]:
        """Match requested languages against available subtitle tracks."""
        if not sub_dict:
            return None

        for req_lang in self.languages:
            if req_lang in ("auto", "all"):
                for lang, tracks in sub_dict.items():
                    if "orig" in lang.lower() and tracks:
                        return (lang, tracks[0])
                for lang, tracks in sub_dict.items():
                    if tracks:
                        return (lang, tracks[0])
            for lang, tracks in sub_dict.items():
                if lang.lower().startswith(req_lang) and tracks:
                    return (lang, tracks[0])

        if "auto" in self.languages:
            for lang, tracks in sub_dict.items():
                if tracks:
                    return (lang, tracks[0])

        return None

    def _download_and_convert_sub(self, track_info: dict) -> Optional[str]:
        """Download subtitle data over HTTP and convert to standard SRT."""
        url = track_info.get("url")
        ext = track_info.get("ext", "vtt")
        if not url:
            return None

        try:
            import urllib.request
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_bytes = resp.read()
                
            raw_text = raw_bytes.decode("utf-8", errors="replace")
            
            if ext == "vtt" or "WEBVTT" in raw_text:
                return parse_vtt_to_srt(raw_text)
            elif ext == "json3" or raw_text.startswith("{"):
                try:
                    data = json.loads(raw_text)
                    return json3_to_srt(data)
                except Exception:
                    pass
            elif ext == "srt":
                return raw_text
                
            return parse_vtt_to_srt(raw_text)
        except Exception as e:
            logger.debug(f"Failed to download/parse sub track: {e}")
            return None

    def download_video_file(self, video_id: str, video_url: str, safe_title: str) -> Optional[Path]:
        """Download full MP4 video file directly into output_dir/video/."""
        video_dir = self.output_dir / "video"
        video_dir.mkdir(parents=True, exist_ok=True)
        video_out_tmpl = str(video_dir / f"{video_id}_{safe_title}.%(ext)s")
        
        self._sleep_jitter()
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": video_out_tmpl,
            "merge_output_format": "mp4",
        })
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            target_path = video_dir / f"{video_id}_{safe_title}.mp4"
            if target_path.exists():
                return target_path
            matched = list(video_dir.glob(f"{video_id}_*.*"))
            return matched[0] if matched else None
        except Exception as e:
            logger.error(f"Failed to download video {video_id}: {e}")
            return None

    def download_audio_file(self, video_id: str, video_url: str, safe_title: str) -> Optional[Path]:
        """Download and extract clean 16kHz WAV audio directly into output_dir/audio/."""
        audio_dir = self.output_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_out_tmpl = str(audio_dir / f"{video_id}_{safe_title}.%(ext)s")
        
        self._sleep_jitter()
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts.update({
            "format": "bestaudio/best",
            "outtmpl": audio_out_tmpl,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "16",
            }],
            "postprocessor_args": [
                "-ar", "16000",
                "-ac", "1",
            ],
        })
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            target_path = audio_dir / f"{video_id}_{safe_title}.wav"
            if target_path.exists():
                return target_path
            matched = list(audio_dir.glob(f"{video_id}_*.wav"))
            return matched[0] if matched else None
        except Exception as e:
            logger.error(f"Failed to download audio for {video_id}: {e}")
            return None

    def extract_audio_and_transcribe_whisperx(
        self,
        video_id: str,
        video_url: str,
        temp_dir: Path,
        safe_title: str = ""
    ) -> Tuple[str, str, str]:
        """
        Download minimal audio stream and run WhisperX GPU transcription.
        If keep_audio is True, saves permanently in output_dir/audio/.
        If keep_video is True, downloads full video into output_dir/video/.
        Returns (srt_content, detected_lang, "whisperx").
        """
        if not safe_title:
            safe_title = video_id

        # If keep_video requested, download video stream
        if self.keep_video:
            self.download_video_file(video_id, video_url, safe_title)

        # If keep_audio requested, extract directly into output_dir/audio/
        if self.keep_audio:
            dest_audio = self.output_dir / "audio" / f"{video_id}_{safe_title}.wav"
            if not dest_audio.exists():
                self.download_audio_file(video_id, video_url, safe_title)
            wav_path = dest_audio if dest_audio.exists() else None
        else:
            wav_path = None

        temp_created = False
        if not wav_path or not wav_path.exists():
            self._sleep_jitter()
            audio_out_tmpl = str(temp_dir / f"{video_id}.%(ext)s")
            
            ydl_opts = self._get_base_ydl_opts()
            ydl_opts.update({
                "format": "bestaudio/best",
                "outtmpl": audio_out_tmpl,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "16",
                }],
                "postprocessor_args": [
                    "-ar", "16000",
                    "-ac", "1",
                ],
            })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            wav_path = temp_dir / f"{video_id}.wav"
            if not wav_path.exists():
                possible = list(temp_dir.glob(f"{video_id}.*"))
                if possible:
                    wav_path = possible[0]
                else:
                    raise RuntimeError(f"Audio extraction failed for video {video_id}")
            temp_created = True

        preferred_lang = self.languages[0] if self.languages and self.languages[0] not in ("auto", "all") else None
        
        try:
            srt_content, detected_lang = self.whisper_engine.transcribe_audio(
                str(wav_path),
                language=preferred_lang
            )
            
            if self.keep_audio and temp_created:
                dest_audio = self.output_dir / "audio" / f"{video_id}_{safe_title}.wav"
                dest_audio.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(wav_path), str(dest_audio))
                
            return (srt_content, detected_lang, "whisperx")
        finally:
            if not self.keep_audio and temp_created and wav_path.exists():
                try:
                    wav_path.unlink()
                except Exception:
                    pass

    def save_outputs(
        self,
        video_entry: Dict[str, Any],
        srt_content: str,
        language: str,
        source: str
    ) -> Path:
        """Save SRT, plain text, and sidecar metadata."""
        safe_title = sanitize_filename(video_entry["title"])
        base_name = f"{video_entry['id']}_{safe_title}"
        
        # 1. Save .srt file
        srt_filename = f"{base_name}.{language}.srt"
        srt_path = self.output_dir / srt_filename
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content.strip() + "\n")
            
        # 2. Save .txt plain text transcript if requested
        if self.export_txt:
            clean_lines = []
            for line in srt_content.splitlines():
                line = line.strip()
                if not line or line.isdigit() or "-->" in line:
                    continue
                clean_lines.append(line)
            txt_path = self.output_dir / f"{base_name}.{language}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(clean_lines) + "\n")

        # 3. Check for existing audio/video media paths
        audio_file_path = self.output_dir / "audio" / f"{base_name}.wav"
        video_file_path = self.output_dir / "video" / f"{base_name}.mp4"

        # 4. Save sidecar JSON metadata
        meta_path = self.output_dir / f"{base_name}.json"
        meta_data = {
            "video_id": video_entry["id"],
            "title": video_entry["title"],
            "url": video_entry.get("url", ""),
            "duration": video_entry.get("duration"),
            "upload_date": video_entry.get("upload_date"),
            "language": language,
            "source": source,
            "srt_file": srt_filename,
            "audio_file": f"audio/{audio_file_path.name}" if audio_file_path.exists() else None,
            "video_file": f"video/{video_file_path.name}" if video_file_path.exists() else None,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

        return srt_path

    def process_local_pending_media(self) -> Tuple[int, int]:
        """
        Scan output_dir, output_dir/audio/, and output_dir/video/ for media files.
        If a media file lacks a corresponding .srt or force_whisper is enabled,
        transcribes directly via WhisperX on GPU without downloading from YouTube.
        Returns (completed_count, failed_count).
        """
        if not self.output_dir or not self.output_dir.exists():
            return 0, 0

        logger.info(f"Scanning {self.output_dir} for pending local audio/video files...")
        media_extensions = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".mkv", ".flac"}
        
        found_media: List[Path] = []
        for root, _, files in os.walk(self.output_dir):
            root_path = Path(root)
            for f in files:
                p = root_path / f
                if p.suffix.lower() in media_extensions:
                    found_media.append(p)

        if not found_media:
            logger.info("No local audio/video files found in output directory.")
            return 0, 0

        logger.info(f"Found {len(found_media)} local media file(s). Checking for missing/pending SRTs...")
        
        preferred_lang = self.languages[0] if self.languages and self.languages[0] not in ("auto", "all") else None
        completed_count = 0
        failed_count = 0

        for media_path in found_media:
            stem = media_path.stem
            # Parse video_id and safe title from filename
            if "_" in stem:
                video_id = stem.split("_")[0]
                title = stem[len(video_id) + 1:].strip()
            else:
                video_id = stem
                title = stem

            # Check if any valid non-empty .srt exists matching video_id in output_dir
            existing_srts = list(self.output_dir.glob(f"{video_id}*.srt"))
            has_valid_srt = False
            for s in existing_srts:
                if s.stat().st_size > 50:
                    has_valid_srt = True
                    break

            if has_valid_srt and not self.force_whisper:
                continue

            logger.info(f"⚡ Transcribing local media via WhisperX GPU: {media_path.name}")
            try:
                srt_content, detected_lang = self.whisper_engine.transcribe_audio(
                    str(media_path),
                    language=preferred_lang
                )
                video_entry = {
                    "id": video_id,
                    "title": title or media_path.stem,
                    "url": f"https://www.youtube.com/watch?v={video_id}" if len(video_id) == 11 else "",
                }
                srt_path = self.save_outputs(video_entry, srt_content, detected_lang, "local_whisperx")
                self.manifest.record_video(
                    video_id=video_id,
                    title=video_entry["title"],
                    url=video_entry["url"],
                    duration=None,
                    source="local_whisperx",
                    language=detected_lang,
                    srt_file=srt_path.name,
                    status="completed"
                )
                completed_count += 1
                logger.info(f" ✅ [Local WhisperX] Created: {srt_path.name} (Lang: {detected_lang})")
            except Exception as e:
                logger.error(f" ❌ Local WhisperX transcription failed for {media_path.name}: {e}")
                self.manifest.record_video(
                    video_id=video_id,
                    title=title or media_path.stem,
                    url=f"https://www.youtube.com/watch?v={video_id}" if len(video_id) == 11 else "",
                    duration=None,
                    source="failed",
                    language="unknown",
                    srt_file="",
                    status="failed",
                    error_message=str(e)
                )
                failed_count += 1

        logger.info(f"Local scan completed: {completed_count} transcribed, {failed_count} failed.")
        return completed_count, failed_count

    def run(self):
        """Execute complete extraction pipeline with batch chunking and rest intervals."""
        start_time = time.time()
        
        # 1. If process_local is requested or target_url is not a YouTube URL
        is_url_channel = bool(self.raw_url and ("youtube.com" in self.raw_url or "youtu.be" in self.raw_url or self.raw_url.startswith("@")))
        
        if self.process_local or not is_url_channel:
            logger.info("Running local scan and WhisperX transcription on existing media files...")
            wx_done, wx_fail = self.process_local_pending_media()
            if self.export_jsonl:
                self._export_combined_jsonl()
            elapsed = time.time() - start_time
            logger.info(f"Local batch processing completed in {elapsed:.1f}s.")
            return

        # 2. If running on a channel, first process any existing pending local files
        self.process_local_pending_media()

        entries = self.harvest_video_entries()
        if not entries:
            logger.info("No videos to process. Exiting.")
            return

        completed_ids = self.manifest.get_completed_video_ids()
        pending_entries = [e for e in entries if e["id"] not in completed_ids]
        
        logger.info(
            f"Total Videos: {len(entries)} | Already Completed: {len(completed_ids)} | Pending: {len(pending_entries)}"
        )
        
        if not pending_entries:
            logger.info("All videos are already processed!")
            self._print_summary_table(len(entries), 0, 0, 0)
            return

        downloaded_count = 0
        whisperx_count = 0
        failed_count = 0

        # Process in safe batches (chunks) to avoid triggering YouTube rate-limiting
        total_chunks = (len(pending_entries) + self.chunk_size - 1) // self.chunk_size
        logger.info(f"Processing {len(pending_entries)} pending videos in {total_chunks} batch(es) (Chunk Size: {self.chunk_size})...")

        for chunk_idx in range(0, len(pending_entries), self.chunk_size):
            chunk = pending_entries[chunk_idx:chunk_idx + self.chunk_size]
            current_batch_num = (chunk_idx // self.chunk_size) + 1
            logger.info(f"=== Starting Batch [{current_batch_num}/{total_chunks}] ({len(chunk)} videos) ===")

            # Phase 1: Subtitle check for this batch
            needs_whisperx = []
            
            # Using controlled concurrency (max_workers=1 or 2 by default for anti-bot safety)
            if self.max_workers > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_entry = {
                        executor.submit(self.fetch_youtube_subtitles, e["id"], e["url"]): e
                        for e in chunk
                    }
                    for future in concurrent.futures.as_completed(future_to_entry):
                        entry = future_to_entry[future]
                        try:
                            result = future.result()
                            if result and not self.force_whisper:
                                srt_content, lang, source = result
                                safe_t = sanitize_filename(entry["title"])
                                if self.keep_video:
                                    self.download_video_file(entry["id"], entry["url"], safe_t)
                                if self.keep_audio:
                                    self.download_audio_file(entry["id"], entry["url"], safe_t)
                                srt_path = self.save_outputs(entry, srt_content, lang, source)
                                self.manifest.record_video(
                                    video_id=entry["id"],
                                    title=entry["title"],
                                    url=entry["url"],
                                    duration=entry.get("duration"),
                                    source=source,
                                    language=lang,
                                    srt_file=srt_path.name,
                                    status="completed"
                                )
                                downloaded_count += 1
                                logger.info(f" [YouTube Sub] Saved: {entry['title']} ({lang})")
                            else:
                                needs_whisperx.append(entry)
                        except Exception as e:
                            logger.error(f"Error checking YouTube subs for {entry['id']}: {e}")
                            needs_whisperx.append(entry)
            else:
                # Sequential mode (Safest against bot filters)
                for entry in chunk:
                    try:
                        result = self.fetch_youtube_subtitles(entry["id"], entry["url"])
                        if result and not self.force_whisper:
                            srt_content, lang, source = result
                            safe_t = sanitize_filename(entry["title"])
                            if self.keep_video:
                                self.download_video_file(entry["id"], entry["url"], safe_t)
                            if self.keep_audio:
                                self.download_audio_file(entry["id"], entry["url"], safe_t)
                            srt_path = self.save_outputs(entry, srt_content, lang, source)
                            self.manifest.record_video(
                                video_id=entry["id"],
                                title=entry["title"],
                                url=entry["url"],
                                duration=entry.get("duration"),
                                source=source,
                                language=lang,
                                srt_file=srt_path.name,
                                status="completed"
                            )
                            downloaded_count += 1
                            logger.info(f" [YouTube Sub] Saved: {entry['title']} ({lang})")
                        else:
                            needs_whisperx.append(entry)
                    except Exception as e:
                        logger.error(f"Error checking YouTube subs for {entry['id']}: {e}")
                        needs_whisperx.append(entry)

            # Phase 2: WhisperX Fallback for videos in this batch that have no subtitles
            if needs_whisperx:
                logger.info(f"Running WhisperX GPU Fallback on {len(needs_whisperx)} videos in Batch {current_batch_num}...")
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_path = Path(tmp_dir)
                    for idx, entry in enumerate(needs_whisperx, start=1):
                        logger.info(
                            f"[{idx}/{len(needs_whisperx)}] WhisperX transcribing: {entry['title']}"
                        )
                        try:
                            safe_t = sanitize_filename(entry["title"])
                            srt_content, lang, source = self.extract_audio_and_transcribe_whisperx(
                                entry["id"],
                                entry["url"],
                                tmp_path,
                                safe_title=safe_t
                            )
                            srt_path = self.save_outputs(entry, srt_content, lang, source)
                            self.manifest.record_video(
                                video_id=entry["id"],
                                title=entry["title"],
                                url=entry["url"],
                                duration=entry.get("duration"),
                                source=source,
                                language=lang,
                                srt_file=srt_path.name,
                                status="completed"
                            )
                            whisperx_count += 1
                            logger.info(f" [WhisperX] Generated SRT: {entry['title']} (Language: {lang})")
                        except Exception as e:
                            logger.error(f" WhisperX transcription failed for {entry['id']}: {e}")
                            self.manifest.record_video(
                                video_id=entry["id"],
                                title=entry["title"],
                                url=entry["url"],
                                duration=entry.get("duration"),
                                source="failed",
                                language="unknown",
                                srt_file="",
                                status="failed",
                                error_message=str(e)
                            )
                            failed_count += 1

            # Rest interval between batches if more remain
            if chunk_idx + self.chunk_size < len(pending_entries) and self.rest_seconds > 0:
                logger.info(f"Batch [{current_batch_num}/{total_chunks}] done. Resting for {self.rest_seconds}s before next batch to protect rate limits...")
                time.sleep(self.rest_seconds)

        if self.export_jsonl:
            self._export_combined_jsonl()

        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed:.1f} seconds.")
        self._print_summary_table(
            total=len(entries),
            yt_count=downloaded_count,
            wx_count=whisperx_count,
            failed=failed_count
        )

    def _export_combined_jsonl(self):
        """Export all channel SRTs into a unified JSONL file suitable for RAG or datasets."""
        jsonl_path = self.output_dir / "channel_transcripts.jsonl"
        count = 0
        
        with open(jsonl_path, "w", encoding="utf-8") as out_f:
            for srt_file in self.output_dir.glob("*.srt"):
                sidecar_meta = srt_file.with_suffix("").with_suffix(".json")
                meta = {}
                if sidecar_meta.exists():
                    try:
                        with open(sidecar_meta, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                    except Exception:
                        pass
                        
                with open(srt_file, "r", encoding="utf-8") as f:
                    srt_text = f.read()
                    
                clean_lines = [
                    line.strip() for line in srt_text.splitlines()
                    if line.strip() and not line.strip().isdigit() and "-->" not in line
                ]
                
                record = {
                    "video_id": meta.get("video_id", srt_file.stem),
                    "title": meta.get("title", srt_file.stem),
                    "url": meta.get("url", ""),
                    "language": meta.get("language", ""),
                    "source": meta.get("source", ""),
                    "srt_filename": srt_file.name,
                    "text": "\n".join(clean_lines),
                    "srt_raw": srt_text,
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
                
        logger.info(f"Exported {count} transcripts to {jsonl_path}")

    def _print_summary_table(self, total: int, yt_count: int, wx_count: int, failed: int):
        """Display rich formatted summary table."""
        if console:
            table = Table(title=f"YouTube SRT Extraction Summary: {self.channel_info.get('title', '')}")
            table.add_column("Category", style="cyan", no_wrap=True)
            table.add_column("Count", style="magenta")
            table.add_column("Percentage", style="green")
            
            completed = yt_count + wx_count
            table.add_row("Total Videos Discovered", str(total), "100%")
            table.add_row("YouTube Subtitles Fetched", str(yt_count), f"{(yt_count/max(total,1))*100:.1f}%")
            table.add_row("WhisperX Transcribed (GPU)", str(wx_count), f"{(wx_count/max(total,1))*100:.1f}%")
            table.add_row("Failed", str(failed), f"{(failed/max(total,1))*100:.1f}%")
            table.add_row("Output Directory", str(self.output_dir), "")
            console.print(table)
        else:
            print("\n=== EXTRACTION SUMMARY ===")
            print(f"Total: {total} | YouTube Subs: {yt_count} | WhisperX: {wx_count} | Failed: {failed}")
            print(f"Output Directory: {self.output_dir}\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download all SRT subtitles from a YouTube channel/playlist with anti-bot throttling and WhisperX GPU fallback."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="",
        help="YouTube channel URL (e.g. https://www.youtube.com/channel/UC...), handle (@channel), playlist, video URL, or leave empty if using --process-local."
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Target folder for .srt files (defaults to ./output_srt/<channel_name>)"
    )
    parser.add_argument(
        "-l", "--languages",
        default="vi,en,auto",
        help="Preferred language codes, comma-separated (default: 'vi,en,auto')"
    )
    parser.add_argument(
        "--no-auto-subs",
        action="store_true",
        help="Do NOT use YouTube auto-generated captions; force WhisperX if manual subs are missing."
    )
    parser.add_argument(
        "--force-whisper",
        action="store_true",
        help="Ignore all YouTube subtitles and run WhisperX transcription on all videos/local files."
    )
    parser.add_argument(
        "--whisper-model",
        default="large-v2",
        choices=["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"],
        help="Whisper model size (default: large-v2)"
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device for WhisperX (default: auto -> CUDA if available)"
    )
    parser.add_argument(
        "--compute-type",
        default="auto",
        choices=["auto", "float16", "int8", "float32"],
        help="Compute type for WhisperX (default: float16 for CUDA, int8 for CPU)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="WhisperX batch size for audio VAD inference (default: 16)"
    )
    parser.add_argument(
        "--no-align",
        action="store_true",
        help="Disable WhisperX word-level alignment (faster transcription, coarser timing)."
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=2,
        help="Max parallel threads for metadata & YouTube subtitle downloads (default: 2 for anti-bot safety)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit maximum number of videos to process in this run."
    )
    parser.add_argument(
        "--include-shorts",
        action="store_true",
        help="Also harvest and download videos from /shorts tab."
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=20,
        help="Number of videos to process per batch before taking a rest (default: 20)"
    )
    parser.add_argument(
        "--rest-seconds",
        type=float,
        default=10.0,
        help="Rest interval in seconds between batches (default: 10s)"
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=1.0,
        help="Minimum randomized delay in seconds between video requests (default: 1.0)"
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=3.0,
        help="Maximum randomized delay in seconds between video requests (default: 3.0)"
    )
    parser.add_argument(
        "--cookies",
        help="Path to cookies.txt file."
    )
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "firefox", "brave", "edge", "safari", "opera", "vivaldi"],
        help="Extract cookies automatically from a local browser."
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously in background scheduler loop."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Interval in seconds between runs when --loop is enabled (default: 3600s = 1 hour)"
    )
    parser.add_argument(
        "--date-after",
        help="Filter videos uploaded on or after YYYYMMDD."
    )
    parser.add_argument(
        "--date-before",
        help="Filter videos uploaded on or before YYYYMMDD."
    )
    parser.add_argument(
        "--keep-audio", "--download-audio",
        dest="keep_audio",
        action="store_true",
        help="Download and keep clean 16kHz audio (.wav) permanently in output_dir/audio/."
    )
    parser.add_argument(
        "--keep-video", "--download-video",
        dest="keep_video",
        action="store_true",
        help="Download and keep full video files (.mp4) permanently in output_dir/video/."
    )
    parser.add_argument(
        "--process-local", "--reprocess-local",
        dest="process_local",
        action="store_true",
        help="Scan output_dir for existing local audio/video files and run WhisperX without downloading from YouTube."
    )
    parser.add_argument(
        "--no-txt",
        action="store_true",
        help="Do not generate plain text .txt transcripts."
    )
    parser.add_argument(
        "--no-jsonl",
        action="store_true",
        help="Do not generate combined dataset channel_transcripts.jsonl."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    def run_once():
        extractor = ChannelSrtExtractor(
            target_url=args.url,
            output_dir=args.output_dir,
            languages=args.languages,
            allow_auto_subs=not args.no_auto_subs,
            force_whisper=args.force_whisper,
            whisper_model=args.whisper_model,
            whisper_device=args.device,
            whisper_compute_type=args.compute_type,
            batch_size=args.batch_size,
            align=not args.no_align,
            max_workers=args.max_workers,
            limit=args.limit,
            include_shorts=args.include_shorts,
            date_after=args.date_after,
            date_before=args.date_before,
            delay_min=args.delay_min,
            delay_max=args.delay_max,
            chunk_size=args.chunk_size,
            rest_seconds=args.rest_seconds,
            cookies=args.cookies,
            cookies_from_browser=args.cookies_from_browser,
            keep_audio=args.keep_audio,
            keep_video=args.keep_video,
            process_local=args.process_local,
            export_txt=not args.no_txt,
            export_jsonl=not args.no_jsonl,
        )
        extractor.run()

    if args.loop:
        logger.info(f"Running in Scheduled Loop mode (Checking every {args.interval}s)... Press Ctrl+C to stop.")
        while True:
            try:
                run_once()
                logger.info(f"Cycle completed. Sleeping for {args.interval} seconds until next scheduled run...")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user. Exiting gracefully.")
                break
            except Exception as e:
                logger.error(f"Error in scheduler cycle: {e}. Retrying in {args.interval} seconds...")
                time.sleep(args.interval)
    else:
        run_once()


if __name__ == "__main__":
    main()
