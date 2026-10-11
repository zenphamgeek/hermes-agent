#!/usr/bin/env python3
import argparse
import contextlib
import fcntl
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from importlib.metadata import PackageNotFoundError, version as package_version
import urllib.request
import wave
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT))
from tools.media_asset_catalog import resolve_asset, scan_assets

DEFAULT_CONFIG = Path(__file__).parents[1] / "avatar_runtime.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".m4a"}
DIALECTS = {"north", "central", "south", "auto", "unknown"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command, cwd=None, timeout=None):
    started = time.monotonic()
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if process.returncode:
        raise RuntimeError(process.stderr[-2000:] or "Lệnh thất bại: " + " ".join(map(str, command)))
    return process, round(time.monotonic() - started, 3)


def wav_info(path):
    with wave.open(str(path), "rb") as audio:
        return {"sample_rate": audio.getframerate(), "duration": audio.getnframes() / audio.getframerate(), "channels": audio.getnchannels()}


def dialect(value, fallback="north"):
    if value not in DIALECTS:
        raise ValueError("dialect phải là north, central, south, auto hoặc unknown")
    return fallback if value in {"auto", "unknown"} else value


def speaker_profile(audio):
    info = wav_info(audio)
    return {
        "source": "generated_audio_metadata",
        "confidence": 0.35,
        "normalization": {
            "sample_rate": info["sample_rate"],
            "articulation_range": 1.0,
        },
        "limitations": ["Không suy luận hình học môi hoặc dialect từ audio khi chưa có model đã duyệt"],
    }


def resolve_actual_pronunciation(prior_segments, acoustic_segments=None, threshold=0.8):
    acoustic_segments = acoustic_segments or []
    realized = []
    for index, prior in enumerate(prior_segments):
        evidence = acoustic_segments[index] if index < len(acoustic_segments) else None
        use_audio = evidence is not None and evidence.get("confidence", 0) >= threshold
        realized.append({**prior, "realized": evidence.get("phoneme") if use_audio else None, "source": "audio" if use_audio else "g2p_prior_unverified", "confidence": evidence.get("confidence", 0.0) if use_audio else 0.0})
    return {"method": "acoustic-evidence-adapter", "actual_pronunciation_available": any(item["source"] == "audio" for item in realized), "segments": realized}


def articulation(text, selected_dialect, duration, profile=None):
    words = text.lower().split()
    step = duration / max(len(words), 1)
    scale = (profile or {}).get("normalization", {}).get("articulation_range", 1.0)
    frames = []
    for index, word in enumerate(words):
        plain = "".join(char for char in unicodedata.normalize("NFD", word) if unicodedata.category(char) != "Mn")
        kind = "neutral"
        target = {"closure": 0.0, "teeth": 0.0, "rounding": 0.0, "aperture": 0.35}
        if plain.startswith(("b", "m", "p")):
            kind, target["closure"] = "bilabial", 1.0
        elif plain.startswith(("f", "v")):
            kind, target["teeth"] = "labiodental", 1.0
        elif any(char in word for char in "ouôơư"):
            kind, target["rounding"] = "rounded_vowel", 0.9
        elif any(char in plain for char in "ae"):
            kind, target["aperture"] = "open_vowel", 0.9
        target = {key: round(value * scale, 3) for key, value in target.items()}
        frames.append({"token": word, "start": round(index * step, 3), "end": round((index + 1) * step, 3), "class": kind, "target": target, "context": {"previous": words[index - 1] if index else None, "next": words[index + 1] if index + 1 < len(words) else None}, "coarticulation": 0.15})
    return {"dialect": selected_dialect, "tone_as_mouth_shape": False, "speaker_normalization": bool(profile), "segments": frames}


def ffprobe(path):
    try:
        process, _ = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate:format=duration", "-of", "json", str(path)])
        return json.loads(process.stdout)
    except FileNotFoundError:
        process, _ = run(["ffmpeg", "-i", str(path), "-f", "null", "-"])
        duration = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", process.stderr)
        video = re.search(r"Video: ([^,]+).*?, (\d+)x(\d+)", process.stderr)
        audio = re.search(r"Audio: ([^,]+)", process.stderr)
        if not duration or not video or not audio:
            raise RuntimeError("Không đọc được metadata output bằng ffmpeg")
        seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3])
        return {"format": {"duration": str(seconds)}, "streams": [{"codec_name": video[1].split()[0], "width": int(video[2]), "height": int(video[3])}, {"codec_name": audio[1].split()[0]}]}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def runtime_report(config):
    packages = {}
    for name in ("Pillow", "numpy", "opencv-python", "onnxruntime-gpu", "torch"):
        try:
            packages[name] = package_version(name)
        except PackageNotFoundError:
            packages[name] = None
    tools = {}
    for name in ("ffmpeg", "ffprobe"):
        try:
            process, _ = run([name, "-version"])
            tools[name] = process.stdout.splitlines()[0]
        except (FileNotFoundError, RuntimeError):
            tools[name] = None
    models = {}
    for name, item in config["models"].items():
        root = Path(item["root"])
        try:
            process, _ = run(["git", "-C", str(root), "rev-parse", "HEAD"])
            revision = process.stdout.strip()
        except (FileNotFoundError, RuntimeError):
            revision = None
        models[name] = {"revision": revision, "checkpoint": str(item["checkpoint"])}
    return {"python": sys.version.split()[0], "packages": packages, "tools": tools, "models": models}


def gpu_report():
    try:
        process, _ = run(["nvidia-smi", "--query-gpu=index,name,driver_version,memory.total,memory.free,memory.used", "--format=csv,noheader,nounits"])
    except (FileNotFoundError, RuntimeError):
        return {"available": False, "devices": []}
    devices = []
    for line in process.stdout.splitlines():
        index, name, driver, total, free, used = (part.strip() for part in line.split(",", 5))
        devices.append({"index": int(index), "name": name, "driver_version": driver, "memory_total_mib": int(total), "memory_free_mib": int(free), "memory_used_mib": int(used)})
    return {"available": bool(devices), "devices": devices}


def available_critics(video, source, source_analysis, audio):
    import cv2
    import numpy as np

    capture = cv2.VideoCapture(str(video))
    frames = []
    while len(frames) < 120:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    if len(frames) < 2:
        raise RuntimeError("Không đủ frame để chạy critic")
    source_frame = cv2.imread(str(source))
    sx, sy = frames[0].shape[1] / source_analysis["image_size"][0], frames[0].shape[0] / source_analysis["image_size"][1]
    x1, y1, x2, y2 = source_analysis["face"]["roi"]
    box = [max(0, round(x1 * sx)), max(0, round(y1 * sy)), min(frames[0].shape[1], round(x2 * sx)), min(frames[0].shape[0], round(y2 * sy))]
    crops = [frame[box[1]:box[3], box[0]:box[2]] for frame in frames]
    gray = [cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) for crop in crops if crop.size]
    tracked_fraction = sum(float(item.std()) > 8 for item in gray) / len(frames)
    source_crop = source_frame[round(y1):round(y2), round(x1):round(x2)]
    reference_hist = cv2.normalize(cv2.calcHist([source_crop], [0], None, [64], [0, 256]), None).flatten()
    identity_similarity = float(np.median([cv2.compareHist(reference_hist, cv2.normalize(cv2.calcHist([crop], [0], None, [64], [0, 256]), None).flatten(), cv2.HISTCMP_CORREL) for crop in crops]))
    h, w = frames[0].shape[:2]
    corners = [np.concatenate((frame[:h // 8].ravel(), frame[-h // 8:].ravel(), frame[:, :w // 8].ravel(), frame[:, -w // 8:].ravel())).astype(np.float32) for frame in frames]
    background_mae = float(np.mean([np.mean(np.abs(item - corners[0])) for item in corners[1:]]) / 255)
    mouth = [item[item.shape[0] // 2:, :] for item in gray]
    mouth_motion = np.array([np.mean(cv2.absdiff(mouth[index], mouth[index - 1])) / 255 for index in range(1, len(mouth))])
    with wave.open(str(audio), "rb") as stream:
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype=np.int16).astype(np.float32)
        sample_rate = stream.getframerate()
    window = max(1, round(sample_rate / max(capture.get(cv2.CAP_PROP_FPS), 1)))
    energy = np.array([np.sqrt(np.mean(samples[index:index + window] ** 2)) for index in range(0, len(samples) - window + 1, window)])
    count = min(len(mouth_motion), max(0, len(energy) - 1))
    lipsync_correlation = float(np.corrcoef(mouth_motion[:count], energy[1:count + 1])[0, 1]) if count > 2 and mouth_motion[:count].std() and energy[1:count + 1].std() else 0.0
    values = {
        "face_tracking": (tracked_fraction, tracked_fraction >= 0.98, "nonblank_face_roi_fraction"),
        "identity": (identity_similarity, identity_similarity >= 0.35, "source_face_histogram_correlation"),
        "background": (background_mae, background_mae <= 0.08, "temporal_border_mae"),
        "lipsync": (lipsync_correlation, lipsync_correlation >= 0.05, "mouth_motion_audio_energy_correlation"),
    }
    return {name: {"status": "PASS" if passed else "FAIL", "metric": round(metric, 6), "method": method, "frames": len(frames)} for name, (metric, passed, method) in values.items()}


def quality_gate(probe, audio, width, height, critics):
    video = next(stream for stream in probe["streams"] if "width" in stream)
    codecs = {stream["codec_name"] for stream in probe["streams"]}
    technical = {
        "duration_ok": abs(float(probe["format"]["duration"]) - audio["duration"]) < 0.25,
        "resolution_ok": [video["width"], video["height"]] == [width, height],
        "codecs_ok": {"h264", "aac"} <= codecs,
    }
    required = ("face_tracking", "identity", "background", "lipsync")
    missing = [name for name in required if critics.get(name, {}).get("status") not in {"PASS", "FAIL"}]
    failed = [name for name in required if critics.get(name, {}).get("status") == "FAIL"]
    status = "PASS" if all(technical.values()) and not missing and not failed else "FAIL"
    return {**technical, "critics": critics, "missing_critics": missing, "failed_critics": failed, "status": status, "production_ready": status == "PASS"}


def analyze_source(config, source):
    root = Path(config["models"]["liveportrait"]["root"])
    python = root.parent / ".venv/bin/python"
    script = """import cv2,json,sys,numpy as np
sys.path.insert(0,sys.argv[1])
from src.utils.face_analysis_diy import FaceAnalysisDIY
image=cv2.imread(sys.argv[2]); h,w=image.shape[:2]
model=FaceAnalysisDIY(name='buffalo_l',root=sys.argv[3],providers=['CUDAExecutionProvider','CPUExecutionProvider'])
model.prepare(ctx_id=0,det_size=(512,512),det_thresh=.15)
faces=model.get(image,max_face_num=0,flag_do_landmark_2d_106=True)
if not faces: raise RuntimeError('Không phát hiện khuôn mặt')
face=faces[0]; x1,y1,x2,y2=map(float,face.bbox); fw,fh=x2-x1,y2-y1
landmarks=np.asarray(face.landmark_2d_106); kps=np.asarray(face.kps)
model3=np.array([[-30,30,30],[30,30,30],[0,0,0],[-25,-30,20],[25,-30,20]],dtype=np.float64)
cam=np.array([[w,0,w/2],[0,w,h/2],[0,0,1]],dtype=np.float64)
ok,rvec,_=cv2.solvePnP(model3,kps.astype(np.float64),cam,np.zeros(4),flags=cv2.SOLVEPNP_EPNP)
angles=[0.,0.,0.]
if ok: angles=cv2.RQDecomp3x3(cv2.Rodrigues(rvec)[0])[0]
angles=[angle-180 if angle>90 else angle+180 if angle < -90 else angle for angle in angles]
warning='reject' if min(fw,fh)<120 else ('warning' if min(fw,fh)<180 else None)
head=[max(0,x1-.35*fw),max(0,y1-.45*fh),min(w,x2+.35*fw),min(h,y2+.25*fh)]
person=[max(0,x1-1.15*fw),max(0,y1-.55*fh),min(w,x2+1.15*fw),h]
shoulders=[person[0],min(h,y2+.1*fh),person[2],min(h,y2+1.15*fh)]
print(json.dumps({'image_size':[w,h],'faces_detected':len(faces),'face':{'roi':[x1,y1,x2,y2],'size_px':[fw,fh],'confidence':float(face.det_score),'landmarks_106':landmarks.tolist()},'head_roi':head,'person_roi':person,'shoulder_roi':shoulders,'pose_deg':{'pitch':angles[0],'yaw':angles[1],'roll':angles[2]},'face_size_status':warning,'face_min_warning_px':180,'face_reject_px':120}))
"""
    process, elapsed = run([str(python), "-c", script, str(root), str(Path(source).resolve()), str(root / "pretrained_weights/insightface")], cwd=root, timeout=180)
    return json.loads(process.stdout.splitlines()[-1]), elapsed


def facefusion_service(config, action):
    face = config["facefusion"]
    process, _ = run(["lxc", "exec", face["container"], "--", "systemctl", action, face["service"]], timeout=30)
    return process.stdout.strip()


@contextlib.contextmanager
def reserve_facefusion(config, enabled):
    if not enabled:
        yield
        return
    facefusion_service(config, "stop")
    try:
        yield
    finally:
        facefusion_service(config, "start")


def render_swapface(config, identity_source, target, run_dir):
    output = run_dir / "swapface.png"
    shared = Path(config["output_root"])
    staged_source = shared / f".swapface-{run_dir.name}-source{Path(identity_source).suffix}"
    staged_target = shared / f".swapface-{run_dir.name}-target{Path(target).suffix}"
    shutil.copy2(identity_source, staged_source)
    shutil.copy2(target, staged_target)
    try:
        root = config["facefusion"]["root"]
        command = ["lxc", "exec", config["facefusion"]["container"], "--", f"{root}/venv/bin/python", f"{root}/facefusion.py", "headless-run", "--processors", "face_swapper", "-s", f"/output/{staged_source.name}", "-t", f"/output/{staged_target.name}", "-o", f"/output/{output.relative_to(shared)}", "--execution-providers", "cuda"]
        _, elapsed = run(command, timeout=1800)
    finally:
        staged_source.unlink(missing_ok=True)
        staged_target.unlink(missing_ok=True)
    if not output.exists():
        raise RuntimeError("SwapFace không tạo output")
    return output, elapsed


def render_liveportrait(config, source, run_dir):
    root = Path(config["models"]["liveportrait"]["root"])
    driving = root / "assets/examples/driving/d0.mp4"
    output = run_dir / "liveportrait"
    output.mkdir(exist_ok=True)
    before = set(output.glob("*.mp4"))
    python = root.parent / ".venv/bin/python"
    _, elapsed = run([str(python), "inference.py", "-s", str(source), "-d", str(driving), "-o", str(output), "--driving-multiplier", "0.35", "--animation-region", "exp"], cwd=root, timeout=1800)
    rendered = sorted(set(output.glob("*.mp4")) - before or set(output.glob("*.mp4")), key=lambda path: path.stat().st_mtime)[-1]
    return rendered, elapsed


def decomposition_cache_key(config, source):
    model = config["models"]["birefnet"]
    return hashlib.sha256(json.dumps({"source": sha256(source), "checkpoint": str(model["checkpoint"]), "version": 1}, sort_keys=True).encode()).hexdigest()[:16]


def restore_decomposition_cache(config, source, run_dir):
    cache = Path(config["output_root"]) / ".source_cache" / decomposition_cache_key(config, source)
    names = ("foreground.png", "source_mask.png", "clean_background.png", "mask_diagnostics.json")
    if not all((cache / name).exists() for name in names):
        return False
    for name in names:
        shutil.copy2(cache / name, run_dir / name)
    return True


def store_decomposition_cache(config, source, run_dir):
    cache = Path(config["output_root"]) / ".source_cache" / decomposition_cache_key(config, source)
    cache.mkdir(parents=True, exist_ok=True)
    for name in ("foreground.png", "source_mask.png", "clean_background.png", "mask_diagnostics.json"):
        shutil.copy2(run_dir / name, cache / name)


def render_birefnet(config, source, run_dir):
    root = Path(config["models"]["birefnet"]["root"])
    output = run_dir / "foreground.png"
    script = "from weights.handler import EndpointHandler; import sys; EndpointHandler()(dict(inputs=sys.argv[1])).save(sys.argv[2])"
    python = root.parent / ".venv/bin/python"
    _, elapsed = run([str(python), "-c", script, str(source), str(output)], cwd=root, timeout=1800)
    if not output.exists():
        raise RuntimeError("BiRefNet không tạo foreground RGBA")
    with Image.open(output) as foreground:
        alpha = foreground.getchannel("A")
        alpha.save(run_dir / "source_mask.png")
        # Clean plate tối thiểu: nền suy rộng từ biên, không bịa chi tiết sau chủ thể.
        background = Image.new("RGB", foreground.size, foreground.convert("RGB").getpixel((0, 0)))
        background.save(run_dir / "clean_background.png")
        histogram = alpha.histogram()
        pixels = foreground.width * foreground.height
        write_json(run_dir / "mask_diagnostics.json", {"size": list(foreground.size), "foreground_fraction": round(sum(histogram[128:]) / pixels, 6), "soft_edge_fraction": round(sum(histogram[1:255]) / pixels, 6), "alpha_extrema": list(alpha.getextrema())})
    return output, elapsed


def composite(config, video, run_dir, fps, refine_interval=0):
    root = Path(config["models"]["birefnet"]["root"])
    python = root.parent / ".venv/bin/python"
    frames = run_dir / "matte_frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()
    # Warp alpha bằng optical flow; BiRefNet chỉ nạp khi người dùng yêu cầu refine định kỳ.
    script = """import cv2,sys,numpy as np
from PIL import Image
video,source_mask,out,checkpoint,interval=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],int(sys.argv[5])
c=cv2.VideoCapture(video); ok,prev=c.read()
if not ok: raise RuntimeError('Video không có frame')
h,w=prev.shape[:2]; mask=np.asarray(Image.open(source_mask).convert('L').resize((w,h)),dtype=np.float32)/255
model=transform=None
if interval>0:
 import torch
 from torchvision import transforms
 from transformers import AutoModelForImageSegmentation
 model=AutoModelForImageSegmentation.from_pretrained(checkpoint,trust_remote_code=True).cuda().eval()
 transform=transforms.Compose([transforms.ToPILImage(),transforms.Resize((512,512)),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
def refine(frame):
 import torch
 x=transform(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).unsqueeze(0).cuda()
 with torch.inference_mode(): p=model(x)[-1].sigmoid().float().cpu().numpy()[0,0]
 return cv2.resize(p,(w,h),interpolation=cv2.INTER_LINEAR)
def save(i): cv2.imwrite(f'{out}/{i:08d}.png',np.clip(mask*255,0,255).astype(np.uint8))
flow_w=min(w,512); flow_h=max(1,round(h*flow_w/w)); x,y=np.meshgrid(np.arange(w),np.arange(h))
def gray_small(frame): return cv2.resize(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),(flow_w,flow_h),interpolation=cv2.INTER_AREA)
save(0); i=1; prev_gray=gray_small(prev)
while True:
 ok,frame=c.read()
 if not ok: break
 gray=gray_small(frame)
 small=cv2.calcOpticalFlowFarneback(prev_gray,gray,None,.5,3,15,3,5,1.2,0)
 flow=cv2.resize(small,(w,h),interpolation=cv2.INTER_LINEAR); flow[...,0]*=w/flow_w; flow[...,1]*=h/flow_h
 mask=cv2.remap(mask,(x-flow[...,0]).astype(np.float32),(y-flow[...,1]).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 if interval>0 and i%interval==0: mask=.75*refine(frame)+.25*mask
 save(i); prev_gray=gray; i+=1
"""
    _, elapsed = run([str(python), "-c", script, str(video), str(run_dir / "source_mask.png"), str(frames), str(Path(config["models"]["birefnet"]["checkpoint"])), str(refine_interval)], cwd=root, timeout=3600)
    output = run_dir / "composited.mp4"
    background = run_dir / "clean_background.png"
    filter_graph = "[0:v]format=gbrpf32le,colorspace=all=bt709:iall=bt709:fast=1[fg];[1:v]format=gray,tmix=frames=3:weights='1 2 1',format=gbrpf32le[a];[2:v]format=gbrpf32le,colorspace=all=bt709:iall=bt709:fast=1[bg];[fg][a][bg]maskedmerge,format=yuv420p"
    duration = ffprobe(video)["format"]["duration"]
    _, encode_elapsed = run(["ffmpeg", "-y", "-i", str(video), "-framerate", str(fps), "-i", str(frames / "%08d.png"), "-loop", "1", "-i", str(background), "-filter_complex", filter_graph, "-t", str(duration), "-an", "-c:v", "libx264", str(output)], timeout=1800)
    return output, elapsed + encode_elapsed


def render_musetalk(config, source, audio, run_dir, fps):
    root = Path(config["models"]["musetalk"]["root"])
    python = root / ".venv310/bin/python"
    checkpoint = Path(config["models"]["musetalk"]["checkpoint"])
    required = [python, checkpoint / "unet.pth", checkpoint / "musetalk.json", root / "models/sd-vae/config.json", root / "models/whisper/config.json"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("MuseTalk runtime thiếu: " + ", ".join(missing))
    safe_source = run_dir / "motion.mp4"
    if source != safe_source:
        shutil.copy2(source, safe_source)
    task = run_dir / "musetalk.yaml"
    task.write_text(f'task_0:\n video_path: "{safe_source}"\n audio_path: "{audio}"\n result_name: "lipsync.mp4"\n', encoding="utf-8")
    result_dir = run_dir / "musetalk"
    if result_dir.exists():
        shutil.rmtree(result_dir)
    process, elapsed = run([str(python), "-m", "scripts.inference", "--inference_config", str(task), "--result_dir", str(result_dir), "--unet_model_path", str(checkpoint / "unet.pth"), "--unet_config", str(checkpoint / "musetalk.json"), "--version", "v15", "--fps", str(fps), "--use_float16"], cwd=root, timeout=1800)
    candidates = list(result_dir.rglob("*.mp4"))
    if not candidates:
        raise RuntimeError("MuseTalk không tạo lipsync.mp4: " + process.stdout[-2000:])
    return max(candidates, key=lambda path: path.stat().st_mtime), elapsed


def health(config):
    omni = config["omnivoice"]
    with urllib.request.urlopen(omni["base_url"] + omni["health_path"], timeout=5) as response:
        value = json.load(response)
    if value.get("engines", {}).get(omni["required_engine"], {}).get("status") != "ok":
        raise RuntimeError("OmniVoice chưa sẵn sàng")


def tts(config, text, voice, output):
    payload = json.dumps({"text": text, "voice": voice, "engine": config["omnivoice"]["required_engine"]}).encode()
    last = None
    for path in ("/tts", "/tts/omnivoice"):
        try:
            request = urllib.request.Request(config["omnivoice"]["base_url"] + path, payload, {"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=180) as response:
                body = response.read()
                content_type = response.headers.get_content_type()
            if content_type == "application/json" or body.lstrip().startswith(b"{"):
                result = json.loads(body)
                download_url = result.get("download_url")
                if not download_url:
                    raise RuntimeError("OmniVoice không trả audio hoặc download_url")
                with urllib.request.urlopen(download_url, timeout=180) as response:
                    body = response.read()
            output.write_bytes(body)
            return path
        except Exception as error:
            last = error
    raise RuntimeError(f"OmniVoice TTS thất bại: {last}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Vietnamese live avatar pipeline")
    parser.add_argument("--source-image", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--voice-reference", required=True)
    parser.add_argument("--dialect", default="auto")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=2560)
    parser.add_argument("--height", type=int, default=1440)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--matte-refine-interval", type=int, default=0, help="BiRefNet refine mỗi N frame; 0 chỉ warp source mask")
    parser.add_argument("--swapface-source", help="Ảnh identity tùy chọn để SwapFace vào source trước animation")
    parser.add_argument("--reserve-facefusion-gpu", action="store_true", help="Dừng FaceFusion trong lúc render, luôn phục hồi sau đó")
    args = parser.parse_args(argv)
    if not args.text.strip() or args.fps <= 0 or args.width <= 0 or args.height <= 0 or args.matte_refine_interval < 0:
        parser.error("text, fps, kích thước và matte-refine-interval phải hợp lệ")

    config = json.loads(args.config.read_text())
    assets = scan_assets(ROOT / "assets")
    source = resolve_asset(args.source_image, [item for item in assets if item["type"] == "image"], category="face")
    voice = resolve_asset(args.voice_reference, [item for item in assets if item["type"] == "audio"], category="voice")
    selected_dialect = dialect(args.dialect, config.get("phonetics", {}).get("fallback_dialect", "north"))
    swapface_source = resolve_asset(args.swapface_source, [item for item in assets if item["type"] == "image"], category="face") if args.swapface_source else None
    model_hashes = {name: sha256(next((p for p in Path(item["checkpoint"]).rglob("*") if p.is_file()), Path(item["checkpoint"]))) for name, item in config["models"].items()}
    identity = hashlib.sha256(json.dumps({"pipeline": 4, "source": sha256(source), "swapface_source": sha256(swapface_source) if swapface_source else None, "voice": sha256(voice), "text": args.text, "dialect": selected_dialect, "fps": args.fps, "size": [args.width, args.height], "matte_refine_interval": args.matte_refine_interval, "models": model_hashes}, sort_keys=True).encode()).hexdigest()[:16]
    run_dir = Path(config["output_root"]) / identity
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"run_id": identity, "config": config, "inputs": {"source_image": str(source), "voice_reference": str(voice), "text": args.text, "dialect": selected_dialect, "fps": args.fps, "size": [args.width, args.height]}, "hashes": {"source": sha256(source), "voice": sha256(voice), "models": model_hashes}, "versions": runtime_report(config)}
    write_json(run_dir / "manifest.json", manifest)
    if args.dry_run:
        print(run_dir)
        return 0

    timings = {}
    retries = {}
    gpu = {"before_lock": gpu_report()}
    lock_path = Path(config["gpu"]["lock_path"])
    lock_started = time.monotonic()
    with lock_path.open("w") as lock, reserve_facefusion(config, args.reserve_facefusion_gpu):
        fcntl.flock(lock, fcntl.LOCK_EX)
        timings["gpu_lock_wait"] = round(time.monotonic() - lock_started, 3)
        gpu["before_render"] = gpu_report()
        health(config)
        master = run_dir / "master.wav"
        if not master.exists():
            started = time.monotonic(); endpoint = tts(config, args.text, voice.stem, master); timings["tts"] = round(time.monotonic() - started, 3)
        else:
            endpoint = "cache"
        audio = wav_info(master)
        phonetic = run_dir / "phonetic.wav"
        if not phonetic.exists():
            _, timings["phonetic_audio"] = run(["ffmpeg", "-y", "-i", str(master), "-ac", "1", "-ar", "16000", str(phonetic)])
        profile = speaker_profile(master)
        write_json(run_dir / "speaker_profile.json", profile)
        timeline = articulation(args.text, selected_dialect, audio["duration"], profile)
        pronunciation = resolve_actual_pronunciation(timeline["segments"])
        write_json(run_dir / "alignment.json", {"method": pronunciation["method"], "dialect": selected_dialect, "actual_pronunciation_available": pronunciation["actual_pronunciation_available"], "confidence": 0.0, "segments": pronunciation["segments"], "limitations": ["Chưa có acoustic phoneme decoder/forced aligner được duyệt; timing chỉ là duration prior"]})
        write_json(run_dir / "articulation_timeline.json", timeline)

        render_source = source
        if swapface_source:
            swapped = run_dir / "swapface.png"
            if not swapped.exists():
                swapped, timings["swapface"] = render_swapface(config, swapface_source, source, run_dir)
            render_source = swapped
        source_analysis, timings["source_analysis"] = analyze_source(config, render_source)
        source_analysis.update({"source": str(render_source), "motion_limits_deg": {"yaw": 7, "pitch": 5, "roll": 3}})
        write_json(run_dir / "source_analysis.json", source_analysis)
        foreground = run_dir / "foreground.png"
        if not foreground.exists():
            if restore_decomposition_cache(config, render_source, run_dir):
                timings["birefnet_source"] = 0.0
            else:
                _, timings["birefnet_source"] = render_birefnet(config, render_source, run_dir)
                store_decomposition_cache(config, render_source, run_dir)
        final = run_dir / "avatar.mp4"
        if not final.exists():
            motion, timings["liveportrait"] = render_liveportrait(config, render_source, run_dir)
            lipsync, timings["musetalk"] = render_musetalk(config, motion, master, run_dir, args.fps)
            composited, timings["dynamic_matte_composite"] = composite(config, lipsync, run_dir, args.fps, args.matte_refine_interval)
            _, timings["encode"] = run(["ffmpeg", "-y", "-i", str(composited), "-i", str(master), "-vf", f"scale={args.width}:{args.height}:force_original_aspect_ratio=decrease,pad={args.width}:{args.height}:(ow-iw)/2:(oh-ih)/2", "-r", str(args.fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)], timeout=600)
        probe = ffprobe(final)
        critic_path = run_dir / "critic_report.json"
        critics = available_critics(final, render_source, source_analysis, master)
        write_json(critic_path, critics)
        qc = quality_gate(probe, audio, args.width, args.height, critics)
        write_json(run_dir / "quality_report.json", qc)
        write_json(run_dir / "visual_phonemes.json", {"status": "unavailable", "segments": [], "reason": "ViVSE chưa có checkpoint đã đánh giá"})
        write_json(run_dir / "vivse_report.json", {"enabled": False, "status": "unavailable", "reason": "Không có checkpoint, dataset đánh giá và ngưỡng nghiệm thu ViVSE"})
        gpu["after_render"] = gpu_report()
        write_json(run_dir / "run_report.json", {**manifest, "status": qc["status"], "tts_endpoint": endpoint, "audio": audio, "timings": timings, "gpu": gpu, "qc": qc, "retries": retries, "diagnostics": {"critic_report": str(critic_path), "critic_report_exists": True, "vivse": {"enabled": False, "reason": "Không có checkpoint, dataset đánh giá và ngưỡng nghiệm thu ViVSE"}}})
    print(final)
    return 0 if qc["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
