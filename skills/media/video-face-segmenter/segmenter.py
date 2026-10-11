#!/usr/bin/env python3
"""
Video Face Segmenter & Footage Analyzer for Hermes Agent
=========================================================
Analyzes long MP4 videos, detects scenes, tracks dominant faces of specified gender,
evaluates head pose, occlusion, sharpness, resolution, and splits into lossless
segments labeled with _OK, _NOT, or _NOFACE.
"""

import os
import sys
import cv2
import json
import csv
import math
import time
import argparse
import subprocess
import shutil
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple

from quality import greedy_cluster_identity, extract_ok_runs

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

# Preset Threshold Configurations (Tối ưu hóa cho FaceFusion / InsightFace thực tế)
PRESETS = {
    "strict": {
        "max_yaw": 35.0,
        "max_pitch": 28.0,
        "max_roll": 25.0,
        "max_occlusion": 0.25,
        "min_sharpness": 40.0,
        "min_face_height": 60,
        "min_det_score": 0.50,
        "pass_ratio": 0.50,
    },
    "balanced": {
        "max_yaw": 45.0,
        "max_pitch": 35.0,
        "max_roll": 35.0,
        "max_occlusion": 0.35,
        "min_sharpness": 20.0,
        "min_face_height": 40,
        "min_det_score": 0.40,
        "pass_ratio": 0.30,
    },
    "relaxed": {
        "max_yaw": 55.0,
        "max_pitch": 42.0,
        "max_roll": 45.0,
        "max_occlusion": 0.45,
        "min_sharpness": 12.0,
        "min_face_height": 30,
        "min_det_score": 0.30,
        "pass_ratio": 0.20,
    },
    "permissive": {
        "max_yaw": 65.0,
        "max_pitch": 50.0,
        "max_roll": 50.0,
        "max_occlusion": 0.60,
        "min_sharpness": 6.0,
        "min_face_height": 20,
        "min_det_score": 0.20,
        "pass_ratio": 0.15,
    }
}

# Standard 3D Facial Model Points for Head Pose Estimation (PnP)
MODEL_POINTS_5 = np.array([
    [0.0, 0.0, 0.0],          # Nose tip
    [-30.0, -30.0, -30.0],    # Left eye
    [30.0, -30.0, -30.0],     # Right eye
    [-20.0, 40.0, -20.0],     # Left mouth corner
    [20.0, 40.0, -20.0]       # Right mouth corner
], dtype=np.float64)


def estimate_head_pose_5pts(landmarks: np.ndarray, frame_shape: Tuple[int, int]) -> Tuple[float, float, float]:
    """
    Estimate Euler Angles (Yaw, Pitch, Roll) in degrees from 5 facial landmarks using cv2.solvePnP.
    Landmarks order: [left_eye, right_eye, nose, left_mouth, right_mouth]
    """
    if len(landmarks) < 5:
        return 0.0, 0.0, 0.0

    # Remap points to [nose, left_eye, right_eye, left_mouth, right_mouth]
    image_points = np.array([
        landmarks[2],  # nose
        landmarks[0],  # left eye
        landmarks[1],  # right eye
        landmarks[3],  # left mouth
        landmarks[4]   # right mouth
    ], dtype=np.float64)

    h, w = frame_shape[:2]
    focal_length = w
    center = (w / 2.0, h / 2.0)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1))

    success, rvec, tvec = cv2.solvePnP(
        MODEL_POINTS_5,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_EPNP
    )

    if not success:
        return 0.0, 0.0, 0.0

    # Convert rotation vector to rotation matrix
    rmat, _ = cv2.Rodrigues(rvec)

    # Compute Euler angles
    sy = math.sqrt(rmat[0, 0] * rmat[0, 0] + rmat[1, 0] * rmat[1, 0])
    singular = sy < 1e-6

    if not singular:
        pitch = math.atan2(rmat[2, 1], rmat[2, 2])
        yaw = math.atan2(-rmat[2, 0], sy)
        roll = math.atan2(rmat[1, 0], rmat[0, 0])
    else:
        pitch = math.atan2(-rmat[1, 2], rmat[1, 1])
        yaw = math.atan2(-rmat[2, 0], sy)
        roll = 0.0

    return math.degrees(yaw), math.degrees(pitch), math.degrees(roll)


def calculate_sharpness(image: np.ndarray, bbox: List[int]) -> float:
    """Compute Laplacian variance of the cropped face area to measure sharpness."""
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = image.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    if x2 <= x1 or y2 <= y1:
        return 0.0

    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def estimate_occlusion(image: np.ndarray, bbox: List[int], landmarks: np.ndarray) -> float:
    """
    Estimate occlusion score based on face symmetry and intensity uniformity in key facial regions.
    Returns estimated occlusion percentage (0.0 to 1.0).
    """
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = image.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    if x2 <= x1 or y2 <= y1:
        return 1.0

    face_w = x2 - x1
    face_h = y2 - y1

    # Check if landmarks are fully inside bbox with reasonable margin
    out_of_bounds = 0
    for lx, ly in landmarks:
        if lx < x1 - 5 or lx > x2 + 5 or ly < y1 - 5 or ly > y2 + 5:
            out_of_bounds += 1

    occlusion = out_of_bounds / max(1, len(landmarks))

    # Check eye-distance vs face-width ratio (extreme distortion or occlusion check)
    eye_dist = math.hypot(landmarks[1][0] - landmarks[0][0], landmarks[1][1] - landmarks[0][1])
    expected_ratio = eye_dist / max(1.0, face_w)
    if expected_ratio < 0.20 or expected_ratio > 0.65:
        occlusion += 0.15

    return min(1.0, float(occlusion))


@dataclass
class FrameFaceMetric:
    frame_idx: int
    timestamp_sec: float
    detected: bool
    gender: str
    gender_score: float
    yaw: float
    pitch: float
    roll: float
    face_height: int
    sharpness: float
    occlusion: float
    det_score: float = 0.0
    id_sim: float = 0.0
    is_ok: bool = False


@dataclass
class SceneAnalysis:
    scene_idx: int
    start_time_sec: float
    end_time_sec: float
    start_timestamp: str
    end_timestamp: str
    duration_sec: float
    total_frames_sampled: int
    target_faces_detected: int
    ok_frames_count: int
    classification: str  # OK, NOT, NOFACE
    avg_yaw: float
    avg_pitch: float
    avg_roll: float
    avg_sharpness: float
    avg_occlusion: float
    avg_face_height: int
    avg_id_sim: float = 0.0
    output_filename: str = ""
    ok_runs: List[Dict] = field(default_factory=list)


class VideoFaceSegmenter:
    def __init__(
        self,
        video_path: str,
        target_gender: str = "female",
        preset: str = "balanced",
        custom_thresholds: Optional[dict] = None,
        sample_fps: float = 6.0,
        min_scene_duration: float = 1.0,
        max_scene_duration: float = 30.0,
        contiguous: bool = False,
        min_id_sim: float = 0.30,
        ok_min_duration: float = 5.0,
        blip_gap: int = 1,
        merge_gap: float = 2.0,
        global_identity: bool = True,
        keep_noface: bool = False,
        noface_max_ratio: float = 0.05,
    ):
        self.video_path = Path(video_path).resolve()
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        self.target_gender = target_gender.lower()
        if self.target_gender not in ["female", "male", "any"]:
            raise ValueError(f"Invalid target gender: {target_gender} (must be 'female', 'male', or 'any')")

        self.preset_name = preset.lower()
        self.thresholds = PRESETS.get(self.preset_name, PRESETS["balanced"]).copy()
        if custom_thresholds:
            for k, v in custom_thresholds.items():
                if v is not None:
                    self.thresholds[k] = v

        self.sample_fps = max(1.0, float(sample_fps))
        self.min_scene_duration = min_scene_duration
        self.max_scene_duration = max_scene_duration
        self.contiguous = contiguous
        self.min_id_sim = min_id_sim
        self.ok_min_duration = ok_min_duration
        self.blip_gap = blip_gap
        self.merge_gap = merge_gap
        self.global_identity = global_identity
        self.keep_noface = keep_noface
        if not 0.0 <= noface_max_ratio <= 1.0:
            raise ValueError("noface_max_ratio must be between 0.0 and 1.0")
        self.noface_max_ratio = noface_max_ratio

        # Init video info
        self.cap = cv2.VideoCapture(str(self.video_path))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or 25.0
        self.duration_sec = self.total_frames / self.fps
        self.cap.release()

        # Init InsightFace Analysis
        print(f"[*] Initializing InsightFace FaceAnalysis on GPU/CPU...", file=sys.stderr)
        from insightface.app import FaceAnalysis
        self.app = FaceAnalysis(name="buffalo_l", providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def detect_scenes(self) -> List[Tuple[float, float]]:
        """Detect scene cut boundaries using PySceneDetect and split long shots into manageable footage clips."""
        print(f"[*] Detecting scene cuts with PySceneDetect...", file=sys.stderr)
        from scenedetect import detect, ContentDetector, AdaptiveDetector

        try:
            scene_list = detect(str(self.video_path), AdaptiveDetector(adaptive_threshold=3.0, min_scene_len=int(self.fps * 0.8)))
            if not scene_list:
                scene_list = detect(str(self.video_path), ContentDetector(threshold=27.0))
        except Exception as e:
            print(f"[!] PySceneDetect adaptive detector fallback: {e}", file=sys.stderr)
            scene_list = []

        raw_scenes = []
        if scene_list:
            for scene in scene_list:
                start_sec = getattr(scene[0], 'seconds', scene[0].get_seconds())
                end_sec = getattr(scene[1], 'seconds', scene[1].get_seconds())
                if (end_sec - start_sec) >= self.min_scene_duration:
                    raw_scenes.append((start_sec, end_sec))

        # Fallback if no cuts detected
        if not raw_scenes:
            raw_scenes = [(0.0, self.duration_sec)]

        # Sub-divide long scenes into max_scene_duration chunks (e.g. 30s)
        # to ensure good footage angles are not dragged down into _NOT by long shots
        final_scenes = []
        for start_sec, end_sec in raw_scenes:
            dur = end_sec - start_sec
            if self.max_scene_duration > 0 and dur > self.max_scene_duration:
                curr = start_sec
                while curr < end_sec:
                    nxt = min(end_sec, curr + self.max_scene_duration)
                    if (nxt - curr) >= self.min_scene_duration:
                        final_scenes.append((curr, nxt))
                    curr = nxt
            else:
                final_scenes.append((start_sec, end_sec))

        print(f"[✓] Identified {len(final_scenes)} footage scenes in video ({self.duration_sec:.1f}s total, max clip len={self.max_scene_duration}s)", file=sys.stderr)
        return final_scenes

    def format_timestamp(self, seconds: float) -> str:
        """Format seconds into HH-MM-SS string for safe filenames."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hrs:02d}-{mins:02d}-{secs:02d}"

    def analyze_scene_frames(self, start_sec: float, end_sec: float) -> Tuple[List[FrameFaceMetric], str]:
        """Sample frames within scene window and evaluate face quality."""
        cap = cv2.VideoCapture(str(self.video_path))
        
        frame_step = max(1, int(round(self.fps / self.sample_fps)))
        start_frame = int(start_sec * self.fps)
        end_frame = int(end_sec * self.fps)

        metrics: List[FrameFaceMetric] = []
        emb_by_metric: Dict[int, np.ndarray] = {}  # metric index -> normed embedding (recognition)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        curr_frame = start_frame
        while curr_frame <= end_frame and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if (curr_frame - start_frame) % frame_step == 0:
                t_sec = curr_frame / self.fps
                faces = self.app.get(frame)

                # Filter by gender if specified
                candidate_faces = []
                t = self.thresholds
                for f in faces:
                    # gender: 0 = female, 1 = male in insightface
                    gen_str = "female" if getattr(f, 'gender', 0) == 0 else "male"
                    if self.target_gender == "any" or gen_str == self.target_gender:
                        # Detection-confidence gate: drop low-confidence (blurry/tiny/false) detections
                        if getattr(f, 'det_score', 1.0) < t["min_det_score"]:
                            continue
                        candidate_faces.append((f, gen_str))

                if not candidate_faces:
                    # No target face in this frame
                    metrics.append(FrameFaceMetric(
                        frame_idx=curr_frame,
                        timestamp_sec=t_sec,
                        detected=False,
                        gender="none",
                        gender_score=0.0,
                        yaw=0.0, pitch=0.0, roll=0.0,
                        face_height=0,
                        sharpness=0.0,
                        occlusion=1.0,
                        is_ok=False
                    ))
                else:
                    # Pick DOMINANT face (largest bounding box area)
                    dominant_face, gen_str = max(
                        candidate_faces,
                        key=lambda item: (item[0].bbox[2] - item[0].bbox[0]) * (item[0].bbox[3] - item[0].bbox[1])
                    )

                    bbox = dominant_face.bbox
                    kps = dominant_face.kps
                    face_h = int(bbox[3] - bbox[1])
                    det_score = float(getattr(dominant_face, 'det_score', 1.0))

                    yaw, pitch, roll = estimate_head_pose_5pts(kps, frame.shape)
                    sharpness = calculate_sharpness(frame, bbox)
                    occlusion = estimate_occlusion(frame, bbox, kps)

                    # Evaluate thresholds
                    is_ok = (
                        abs(yaw) <= t["max_yaw"] and
                        abs(pitch) <= t["max_pitch"] and
                        abs(roll) <= t["max_roll"] and
                        occlusion <= t["max_occlusion"] and
                        sharpness >= t["min_sharpness"] and
                        face_h >= t["min_face_height"]
                    )

                    metrics.append(FrameFaceMetric(
                        frame_idx=curr_frame,
                        timestamp_sec=t_sec,
                        detected=True,
                        gender=gen_str,
                        gender_score=1.0,
                        yaw=yaw, pitch=pitch, roll=roll,
                        face_height=face_h,
                        sharpness=sharpness,
                        occlusion=occlusion,
                        det_score=det_score,
                        is_ok=is_ok
                    ))
                    emb = getattr(dominant_face, 'normed_embedding', None)
                    if emb is not None:
                        emb_by_metric[len(metrics) - 1] = np.asarray(emb, dtype=np.float32)

            curr_frame += 1

        cap.release()

        # Identity-consistency gate: dominant face must be ONE person per scene.
        # Frames whose face embedding diverges from the primary identity are not OK
        # (prevents OK segments that mix two different people).
        det_idx = [i for i, m in enumerate(metrics) if m.detected]
        embs = [emb_by_metric[i] for i in det_idx if i in emb_by_metric]
        if len(embs) >= 2 and len(det_idx) == len(embs):
            primary_mask, id_sims = greedy_cluster_identity(embs, self.min_id_sim)
            for j, i in enumerate(det_idx):
                metrics[i].id_sim = round(id_sims[j], 4)
                if j not in primary_mask:
                    metrics[i].is_ok = False

        # Classify scene
        detected_frames = [m for m in metrics if m.detected]
        # Preserve a scene only when no target face is effectively visible. A face
        # in >5% of sampled frames is NOT: it must never leak into final output.
        face_ratio = len(detected_frames) / max(1, len(metrics))
        if face_ratio <= self.noface_max_ratio:
            classification = "NOFACE"
        else:
            ok_frames = [m for m in detected_frames if m.is_ok]
            ratio = len(ok_frames) / len(detected_frames)
            classification = "OK" if ratio >= self.thresholds["pass_ratio"] else "NOT"

        return metrics, classification, emb_by_metric

    def process(self, output_dir: Optional[str] = None) -> Dict:
        """Run full segmentation, classification and lossless extraction."""
        stem = self.video_path.stem
        if output_dir:
            p = Path(output_dir)
            if str(p).startswith("/output"):
                rel = str(p)[len("/output"):].lstrip("/")
                out_dir = Path("/home/zen/workspace/output") / rel
            else:
                out_dir = p
        else:
            out_dir = Path("/home/zen/workspace/output/segments") / f"{stem}"

        out_dir.mkdir(parents=True, exist_ok=True)

        scenes = self.detect_scenes()
        scene_analyses: List[SceneAnalysis] = []

        # Contiguous mode: accumulate per-frame quality across ALL scenes so OK runs can
        # span scene cuts — one continuous shot split by a cut stays one long segment.
        global_metrics: List[FrameFaceMetric] = []
        global_emb: Dict[int, np.ndarray] = {}  # index into global_metrics -> embedding

        print(f"[*] Analyzing {len(scenes)} scenes for gender='{self.target_gender}' (Preset: {self.preset_name})...", file=sys.stderr)

        for idx, (start_sec, end_sec) in enumerate(scenes, start=1):
            metrics, classification, emb_map = self.analyze_scene_frames(start_sec, end_sec)

            if self.contiguous:
                base = len(global_metrics)
                global_metrics.extend(metrics)
                for k, v in emb_map.items():
                    global_emb[base + k] = v

            detected_frames = [m for m in metrics if m.detected]
            ok_frames = [m for m in detected_frames if m.is_ok]

            avg_yaw = float(np.mean([abs(m.yaw) for m in detected_frames])) if detected_frames else 0.0
            avg_pitch = float(np.mean([abs(m.pitch) for m in detected_frames])) if detected_frames else 0.0
            avg_roll = float(np.mean([abs(m.roll) for m in detected_frames])) if detected_frames else 0.0
            avg_sharpness = float(np.mean([m.sharpness for m in detected_frames])) if detected_frames else 0.0
            avg_occlusion = float(np.mean([m.occlusion for m in detected_frames])) if detected_frames else 1.0
            avg_height = int(np.mean([m.face_height for m in detected_frames])) if detected_frames else 0
            avg_id_sim = float(np.mean([m.id_sim for m in detected_frames])) if detected_frames else 0.0

            t_start = self.format_timestamp(start_sec)
            t_end = self.format_timestamp(end_sec)

            # In contiguous mode the report filename is filled after global run extraction;
            # per-scene classification is retained for the timeline/report.
            filename = f"segment_{idx:04d}_{t_start}_{t_end}_{self.target_gender}_{classification}.mp4" if not self.contiguous else ""

            analysis = SceneAnalysis(
                scene_idx=idx,
                start_time_sec=round(start_sec, 3),
                end_time_sec=round(end_sec, 3),
                start_timestamp=t_start,
                end_timestamp=t_end,
                duration_sec=round(end_sec - start_sec, 3),
                total_frames_sampled=len(metrics),
                target_faces_detected=len(detected_frames),
                ok_frames_count=len(ok_frames),
                classification=classification,
                avg_yaw=round(avg_yaw, 1),
                avg_pitch=round(avg_pitch, 1),
                avg_roll=round(avg_roll, 1),
                avg_sharpness=round(avg_sharpness, 1),
                avg_occlusion=round(avg_occlusion, 3),
                avg_face_height=avg_height,
                avg_id_sim=round(avg_id_sim, 4),
                output_filename=filename,
                ok_runs=[],
            )
            scene_analyses.append(analysis)
            print(f"  [{idx:03d}/{len(scenes):03d}] {classification}", file=sys.stderr)

        ffmpeg_bin = shutil.which("ffmpeg") or str(Path.home() / ".local/bin/ffmpeg")
        try:
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

        def _slice(start_sec: float, dur_sec: float, out_path: Path) -> None:
            # Re-encode (libx264) with input -ss: ffmpeg seeks to the prior keyframe then
            # decodes/discards up to the exact start (accurate seek), so segments are
            # frame-accurate — not the keyframe-aligned artifacts of `-c copy`.
            ffmpeg_cmd = [
                ffmpeg_bin, "-y", "-loglevel", "error",
                "-ss", f"{start_sec:.3f}", "-t", f"{dur_sec:.3f}",
                "-i", str(self.video_path),
                "-map", "0:v:0", "-map", "0:a?",
                "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                str(out_path),
            ]
            subprocess.run(ffmpeg_cmd, check=True)

        segments: List[Dict] = []
        if self.contiguous:
            # Global single-identity gate: the dominant face across the WHOLE video is the
            # swapface target. Frames of other identities break runs so a merged long segment
            # never mixes two different people (same intent as the per-scene gate, but across
            # scene cuts which merge_gap now bridges).
            if self.global_identity:
                det_idxs = [i for i, m in enumerate(global_metrics) if m.detected]
                embs = [global_emb[i] for i in det_idxs if i in global_emb]
                if len(embs) >= 2 and len(det_idxs) == len(embs):
                    primary_mask, _ = greedy_cluster_identity(embs, self.min_id_sim)
                    for j, i in enumerate(det_idxs):
                        if j not in primary_mask:
                            global_metrics[i].is_ok = False

            runs = extract_ok_runs(
                [m.is_ok for m in global_metrics],
                [m.timestamp_sec for m in global_metrics],
                sample_dt=1.0 / self.sample_fps,
                gap_ok=self.blip_gap,
                min_dur=self.ok_min_duration,
                merge_gap=self.merge_gap,
            )
            for ri, (rs, re, rd) in enumerate(runs, start=1):
                rf = f"segment_{ri:04d}_{self.format_timestamp(rs)}_{self.format_timestamp(re)}_{self.target_gender}_OK.mp4"
                run_path = out_dir / rf
                _slice(rs, rd, run_path)
                segments.append({"start": round(rs, 3), "end": round(re, 3), "duration": round(rd, 3), "file": rf, "classification": "OK"})
                print(f"  [{ri:03d}/{len(runs):03d}] {rf} ({rd:.2f}s) -> OK", file=sys.stderr)

            # Preserve no-face footage for the final timeline. NOT scenes are deliberately
            # excluded: they contain a detected but unusable target face. NOFACE scenes need
            # no swap and are concatenated unchanged after the OK clips have been swapped.
            # Consecutive NOFACE scenes are merged together to keep timeline segments smooth and substantial.
            if self.keep_noface:
                noface_scenes = [a for a in scene_analyses if a.classification == "NOFACE"]
                merged_noface = []
                for a in noface_scenes:
                    if merged_noface and abs(merged_noface[-1]["end"] - a.start_time_sec) <= 1.0:
                        merged_noface[-1]["end"] = a.end_time_sec
                        merged_noface[-1]["duration"] = round(merged_noface[-1]["end"] - merged_noface[-1]["start"], 3)
                    else:
                        merged_noface.append({
                            "start": a.start_time_sec,
                            "end": a.end_time_sec,
                            "duration": a.duration_sec,
                            "scene_idx": a.scene_idx,
                        })

                for idx, nf_item in enumerate(merged_noface, start=1):
                    start_s = nf_item["start"]
                    end_s = nf_item["end"]
                    dur_s = nf_item["duration"]
                    # Skip tiny sub-second noise blips if multiple scenes exist
                    if dur_s < 1.0 and len(merged_noface) > 1:
                        continue
                    nf = f"noface_{idx:04d}_{self.format_timestamp(start_s)}_{self.format_timestamp(end_s)}.mp4"
                    _slice(start_s, dur_s, out_dir / nf)
                    segments.append({
                        "start": round(start_s, 3),
                        "end": round(end_s, 3),
                        "duration": round(dur_s, 3),
                        "file": nf,
                        "classification": "NOFACE",
                    })
                    print(f"  [{idx:03d}/{len(merged_noface):03d}] {nf} ({dur_s:.2f}s) -> NOFACE", file=sys.stderr)
            segments.sort(key=lambda segment: segment["start"])
        else:
            for analysis, (start_sec, end_sec) in zip(scene_analyses, scenes):
                filename = analysis.output_filename
                _slice(start_sec, end_sec - start_sec, out_dir / filename)
                print(f"  [{analysis.scene_idx:03d}/{len(scenes):03d}] {filename} -> {analysis.classification}", file=sys.stderr)

        # Write timeline.csv
        csv_path = out_dir / "timeline.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Scene #", "Start (s)", "End (s)", "Duration (s)", "Class",
                "Sampled Frames", "Detected Frames", "OK Frames",
                "Avg Yaw (°)", "Avg Pitch (°)", "Avg Sharpness", "Avg Occlusion", "File"
            ])
            for s in scene_analyses:
                writer.writerow([
                    s.scene_idx, s.start_time_sec, s.end_time_sec, s.duration_sec, s.classification,
                    s.total_frames_sampled, s.target_faces_detected, s.ok_frames_count,
                    s.avg_yaw, s.avg_pitch, s.avg_sharpness, s.avg_occlusion, s.output_filename
                ])

        # Write report.json
        json_path = out_dir / "report.json"
        if self.contiguous:
            counts = {
                "OK": sum(segment["classification"] == "OK" for segment in segments),
                "NOT": 0,
                "NOFACE": sum(segment["classification"] == "NOFACE" for segment in segments),
            }
        else:
            counts = {
                "OK": len([s for s in scene_analyses if s.classification == "OK"]),
                "NOT": len([s for s in scene_analyses if s.classification == "NOT"]),
                "NOFACE": len([s for s in scene_analyses if s.classification == "NOFACE"]),
            }
        summary_data = {
            "source_video": str(self.video_path),
            "target_gender": self.target_gender,
            "preset": self.preset_name,
            "thresholds_used": self.thresholds,
            "mode": "contiguous" if self.contiguous else "scene",
            "timeline_contract": "swap OK; preserve NOFACE (face ratio <= 5%); omit NOT" if self.contiguous and self.keep_noface else None,
            "noface_max_detected_ratio": self.noface_max_ratio,
            "merge_gap_sec": self.merge_gap,
            "min_segment_dur_sec": self.ok_min_duration,
            "total_duration_sec": self.duration_sec,
            "total_scenes": len(scene_analyses),
            "counts": counts,
            "output_directory": str(out_dir),
            "scenes": [asdict(s) for s in scene_analyses],
            "segments": segments,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        # Chown output to host user (uid 1000) so host tools (snap VLC, editors)
        # can read/delete files. Container root owns uid 1000000 files otherwise,
        # which snap confinement refuses to open. Best-effort; no-op if not root.
        try:
            if os.geteuid() == 0:
                for f in out_dir.iterdir():
                    os.chown(f, 1000, 1000)
                os.chown(out_dir, 1000, 1000)
        except (PermissionError, OSError):
            pass

        return summary_data


def main():
    parser = argparse.ArgumentParser(description="Video Face Segmenter & Footage Analyzer for SwapFace")
    parser.add_argument("--input", "-i", required=True, help="Path to input MP4 video file")
    parser.add_argument("--gender", "-g", default="female", choices=["female", "male", "any"], help="Target gender to analyze (default: female)")
    parser.add_argument("--preset", "-p", default="balanced", choices=["strict", "balanced", "relaxed", "permissive"], help="Quality preset (default: balanced)")
    parser.add_argument("--output-dir", "-o", default=None, help="Directory to save segmented clips and report")
    parser.add_argument("--sample-fps", default=6.0, type=float, help="Analysis sampling FPS (default: 6.0)")
    parser.add_argument("--max-scene-len", default=30.0, type=float, help="Max duration of each output footage clip in seconds (default: 30.0, 0 to disable)")
    parser.add_argument("--max-yaw", type=float, default=None, help="Override maximum Yaw angle in degrees")
    parser.add_argument("--max-pitch", type=float, default=None, help="Override maximum Pitch angle in degrees")
    parser.add_argument("--min-sharpness", type=float, default=None, help="Override minimum sharpness score")
    parser.add_argument("--min-face-height", type=int, default=None, help="Override minimum face height in pixels (swapface: >=80 recommended)")
    parser.add_argument("--min-det-score", type=float, default=None, help="Override minimum face detection confidence (0.0 - 1.0)")
    parser.add_argument("--min-id-sim", type=float, default=0.30, help="Min cosine similarity to primary identity for a frame to count (default: 0.30)")
    parser.add_argument("--pass-ratio", type=float, default=None, help="Override minimum OK frames ratio (0.0 - 1.0) to label scene _OK")
    parser.add_argument("--contiguous", action="store_true", help="Extract contiguous OK runs; NOT footage is dropped")
    parser.add_argument("--keep-noface", action="store_true", help="In contiguous mode, export NOFACE scenes for final timeline concat; NOT scenes remain excluded")
    parser.add_argument("--noface-max-ratio", type=float, default=0.05, help="Max detected-face sample ratio to classify NOFACE (default: 0.05)")
    parser.add_argument("--ok-min-duration", type=float, default=5.0, help="Minimum segment duration in seconds (contiguous mode, default: 5.0)")
    parser.add_argument("--blip-gap", type=int, default=1, help="Max consecutive bad samples allowed inside an OK run (contiguous mode, default: 1)")
    parser.add_argument("--merge-gap", type=float, default=2.0, help="Max seconds of bad footage bridged so adjacent OK runs merge into one longer segment (contiguous mode, default: 2.0)")
    parser.add_argument("--no-global-identity", action="store_true", help="Disable the global single-identity gate (contiguous mode): allow segments to span different people across scene cuts")
    parser.add_argument("--json", action="store_true", help="Output summary in JSON format")

    args = parser.parse_args()

    custom_t = {}
    if args.max_yaw is not None:
        custom_t["max_yaw"] = args.max_yaw
    if args.max_pitch is not None:
        custom_t["max_pitch"] = args.max_pitch
    if args.min_sharpness is not None:
        custom_t["min_sharpness"] = args.min_sharpness
    if args.min_face_height is not None:
        custom_t["min_face_height"] = args.min_face_height
    if args.min_det_score is not None:
        custom_t["min_det_score"] = args.min_det_score
    if args.pass_ratio is not None:
        custom_t["pass_ratio"] = args.pass_ratio

    segmenter = VideoFaceSegmenter(
        video_path=args.input,
        target_gender=args.gender,
        preset=args.preset,
        custom_thresholds=custom_t if custom_t else None,
        sample_fps=args.sample_fps,
        max_scene_duration=args.max_scene_len,
        contiguous=args.contiguous,
        min_id_sim=args.min_id_sim,
        ok_min_duration=args.ok_min_duration,
        blip_gap=args.blip_gap,
        merge_gap=args.merge_gap,
        global_identity=not args.no_global_identity,
        keep_noface=args.keep_noface,
        noface_max_ratio=args.noface_max_ratio,
    )

    results = segmenter.process(output_dir=args.output_dir)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(f"\n========================================================")
        print(f"🎬 Video Face Segmentation Completed!")
        print(f"========================================================")
        print(f"📁 Output Directory: {results['output_directory']}")
        print(f"📊 Summary:")
        print(f"   - Total Scenes : {results['total_scenes']}")
        print(f"   - ✅ _OK       : {results['counts']['OK']} segments (Ready for SwapFace)")
        print(f"   - ⚠️ _NOT      : {results['counts']['NOT']} segments (Suboptimal/Angle/Blur)")
        print(f"   - ❌ _NOFACE   : {results['counts']['NOFACE']} segments (No target face)")
        print(f"📄 Report JSON   : {results['output_directory']}/report.json")
        print(f"📄 Timeline CSV  : {results['output_directory']}/timeline.csv")
        print(f"========================================================")


if __name__ == "__main__":
    main()
