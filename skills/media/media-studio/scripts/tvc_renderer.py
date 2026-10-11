#!/usr/bin/env python3
import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

_AVATAR_SPEC = importlib.util.spec_from_file_location("media_studio_live_avatar", Path(__file__).with_name("live_avatar.py"))
_avatar = importlib.util.module_from_spec(_AVATAR_SPEC)
_AVATAR_SPEC.loader.exec_module(_avatar)
ffprobe, quality_gate, render_liveportrait, render_musetalk, render_swapface, write_json = (_avatar.ffprobe, _avatar.quality_gate, _avatar.render_liveportrait, _avatar.render_musetalk, _avatar.render_swapface, _avatar.write_json)

PROFILES = {
    "preview": {"width": 1280, "height": 720, "fps": 24, "crf": 26, "audio_bitrate": "128k"},
    "master": {"width": 1920, "height": 1080, "fps": 30, "crf": 18, "audio_bitrate": "192k"},
    "uhd": {"width": 3840, "height": 2160, "fps": 30, "crf": 16, "audio_bitrate": "256k"},
}
CAMERA_FILTERS = {
    "none": "null",
    "push-in": "zoompan=z='min(zoom+0.0008,1.12)':d=1:s={width}x{height}:fps={fps}",
    "pull-out": "zoompan=z='if(eq(on,1),1.12,max(zoom-0.0008,1.0))':d=1:s={width}x{height}:fps={fps}",
    "pan-left": "zoompan=z=1.08:x='max(0,(iw-iw/zoom)*(1-on/({fps}*10)))':y='(ih-ih/zoom)/2':d=1:s={width}x{height}:fps={fps}",
    "pan-right": "zoompan=z=1.08:x='min(iw-iw/zoom,(iw-iw/zoom)*on/({fps}*10))':y='(ih-ih/zoom)/2':d=1:s={width}x{height}:fps={fps}",
}


def command(args, config, duration):
    profile = PROFILES[args.profile]
    camera = CAMERA_FILTERS[args.camera].format(**profile)
    inputs = ["-i", str(args.video), "-i", str(args.voice)]
    audio = ["[1:a]volume=1[voice]"]
    labels = ["[voice]"]
    index = 2
    if args.music:
        inputs += ["-stream_loop", "-1", "-i", str(args.music)]
        audio.append(f"[{index}:a]volume={args.music_volume}[music]")
        labels.append("[music]"); index += 1
    for sfx in args.sfx:
        inputs += ["-i", str(sfx)]
        audio.append(f"[{index}:a]volume={args.sfx_volume}[sfx{index}]")
        labels.append(f"[sfx{index}]"); index += 1
    audio.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    video_filter = f"{camera},scale={profile['width']}:{profile['height']}:force_original_aspect_ratio=decrease,pad={profile['width']}:{profile['height']}:(ow-iw)/2:(oh-ih)/2,format=yuv420p[v]"
    return ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join([video_filter, *audio]), "-map", "[v]", "-map", "[a]", "-t", str(duration), "-r", str(profile["fps"]), "-c:v", "libx264", "-crf", str(profile["crf"]), "-c:a", "aac", "-b:a", profile["audio_bitrate"], str(args.output)]


def presenter(config, source, voice, identity, run_dir, fps):
    current = source
    if identity:
        current, _ = render_swapface(config, identity, current, run_dir)
    current, _ = render_liveportrait(config, current, run_dir)
    current, _ = render_musetalk(config, current, voice, run_dir, fps)
    return current


def main(argv=None):
    parser = argparse.ArgumentParser(description="Minimal TVC renderer")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--voice", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--music", type=Path)
    parser.add_argument("--sfx", type=Path, action="append", default=[])
    parser.add_argument("--music-volume", type=float, default=0.18)
    parser.add_argument("--sfx-volume", type=float, default=0.7)
    parser.add_argument("--camera", choices=CAMERA_FILTERS, default="none")
    parser.add_argument("--profile", choices=PROFILES, default="preview")
    parser.add_argument("--presenter-source", type=Path)
    parser.add_argument("--presenter-identity", type=Path)
    parser.add_argument("--avatar-config", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    for path in [args.video, args.voice, args.music, *args.sfx, args.presenter_source, args.presenter_identity, args.avatar_config]:
        if path and not path.is_file(): parser.error(f"Không tìm thấy file: {path}")
    profile = PROFILES[args.profile]
    config = json.loads(args.avatar_config.read_text()) if args.avatar_config else None
    run_dir = args.output.parent / f".{args.output.stem}-presenter"
    if args.presenter_source:
        if not config: parser.error("--avatar-config bắt buộc khi dùng presenter")
        run_dir.mkdir(parents=True, exist_ok=True)
        args.video = presenter(config, args.presenter_source, args.voice, args.presenter_identity, run_dir, profile["fps"])
    duration = float(ffprobe(args.voice)["format"]["duration"])
    ffmpeg = command(args, config, duration)
    if args.dry_run:
        print(json.dumps(ffmpeg, ensure_ascii=False)); return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(ffmpeg, check=True)
    probe = ffprobe(args.output)
    audio = {"duration": duration}
    critics = {name: {"status": "PASS", "method": "not_applicable_without_presenter"} for name in ("face_tracking", "identity", "background", "lipsync")} if not args.presenter_source else {}
    qc = quality_gate(probe, audio, profile["width"], profile["height"], critics)
    qc["profile"] = args.profile
    qc["presenter_qc_required"] = bool(args.presenter_source)
    report = args.output.with_suffix(".qc.json")
    write_json(report, qc)
    print(args.output)
    return 0 if qc["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
