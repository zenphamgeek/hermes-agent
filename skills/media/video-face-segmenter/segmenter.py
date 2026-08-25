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
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

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
        "gender_confidence": 0.60,
        "pass_ratio": 0.50,
    },
    "balanced": {
        "max_yaw": 45.0,
        "max_pitch": 35.0,
        "max_roll": 35.0,
        "max_occlusion": 0.35,
        "min_sharpness": 20.0,
        "min_face_height": 40,
        "gender_confidence": 0.50,
        "pass_ratio": 0.30,
    },
    "relaxed": {
        "max_yaw": 55.0,
        "max_pitch": 42.0,
        "max_roll": 45.0,
        "max_occlusion": 0.45,
        "min_sharpness": 12.0,
        "min_face_height": 30,
        "gender_confidence": 0.40,
        "pass_ratio": 0.20,
    },
    "permissive": {
        "max_yaw": 65.0,
        "max_pitch": 50.0,
        "max_roll": 50.0,
        "max_occlusion": 0.60,
        "min_sharpness": 6.0,
        "min_face_height": 20,
        "gender_confidence": 0.30,
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
    is_ok: bool


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
    output_filename: str


class VideoFaceSegmenter:
    def __init__(
        self,
        video_path: str,
        target_gender: str = "female",
        preset: str = "balanced",
        custom_thresholds: Optional[dict] = None,
        sample_fps: float = 6.0,
        min_scene_duration: float = 1.0,
        max_scene_duration: float = 30.0
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
                for f in faces:
                    # gender: 0 = female, 1 = male in insightface
                    gen_str = "female" if getattr(f, 'gender', 0) == 0 else "male"
                    if self.target_gender == "any" or gen_str == self.target_gender:
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

                    yaw, pitch, roll = estimate_head_pose_5pts(kps, frame.shape)
                    sharpness = calculate_sharpness(frame, bbox)
                    occlusion = estimate_occlusion(frame, bbox, kps)

                    # Evaluate thresholds
                    t = self.thresholds
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
                        is_ok=is_ok
                    ))

            curr_frame += 1

        cap.release()

        # Classify scene
        detected_frames = [m for m in metrics if m.detected]
        if not detected_frames or len(detected_frames) / max(1, len(metrics)) < 0.20:
            classification = "NOFACE"
        else:
            ok_frames = [m for m in detected_frames if m.is_ok]
            ratio = len(ok_frames) / len(detected_frames)
            classification = "OK" if ratio >= self.thresholds["pass_ratio"] else "NOT"

        return metrics, classification

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

        print(f"[*] Analyzing {len(scenes)} scenes for gender='{self.target_gender}' (Preset: {self.preset_name})...", file=sys.stderr)

        for idx, (start_sec, end_sec) in enumerate(scenes, start=1):
            metrics, classification = self.analyze_scene_frames(start_sec, end_sec)

            detected_frames = [m for m in metrics if m.detected]
            ok_frames = [m for m in detected_frames if m.is_ok]

            avg_yaw = float(np.mean([abs(m.yaw) for m in detected_frames])) if detected_frames else 0.0
            avg_pitch = float(np.mean([abs(m.pitch) for m in detected_frames])) if detected_frames else 0.0
            avg_roll = float(np.mean([abs(m.roll) for m in detected_frames])) if detected_frames else 0.0
            avg_sharpness = float(np.mean([m.sharpness for m in detected_frames])) if detected_frames else 0.0
            avg_occlusion = float(np.mean([m.occlusion for m in detected_frames])) if detected_frames else 1.0
            avg_height = int(np.mean([m.face_height for m in detected_frames])) if detected_frames else 0

            t_start = self.format_timestamp(start_sec)
            t_end = self.format_timestamp(end_sec)
            filename = f"segment_{idx:04d}_{t_start}_{t_end}_{self.target_gender}_{classification}.mp4"

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
                output_filename=filename
            )
            scene_analyses.append(analysis)

            # Slicing segment with FFmpeg Lossless Stream Copy
            target_out_path = out_dir / filename
            ffmpeg_bin = shutil.which("ffmpeg") or str(Path.home() / ".local/bin/ffmpeg")
            try:
                import imageio_ffmpeg
                ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                pass

            ffmpeg_cmd = [
                ffmpeg_bin, "-y", "-loglevel", "error",
                "-ss", str(start_sec),
                "-to", str(end_sec),
                "-i", str(self.video_path),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                str(target_out_path)
            ]
            subprocess.run(ffmpeg_cmd, check=True)
            print(f"  [{idx:03d}/{len(scenes):03d}] {filename} -> {classification}", file=sys.stderr)

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
        summary_data = {
            "source_video": str(self.video_path),
            "target_gender": self.target_gender,
            "preset": self.preset_name,
            "thresholds_used": self.thresholds,
            "total_duration_sec": self.duration_sec,
            "total_scenes": len(scene_analyses),
            "counts": {
                "OK": len([s for s in scene_analyses if s.classification == "OK"]),
                "NOT": len([s for s in scene_analyses if s.classification == "NOT"]),
                "NOFACE": len([s for s in scene_analyses if s.classification == "NOFACE"]),
            },
            "output_directory": str(out_dir),
            "scenes": [asdict(s) for s in scene_analyses]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

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
    parser.add_argument("--pass-ratio", type=float, default=None, help="Override minimum OK frames ratio (0.0 - 1.0) to label scene _OK")
    parser.add_argument("--json", action="store_true", help="Output summary in JSON format")

    args = parser.parse_args()

    custom_t = {}
    if args.max_yaw is not None:
        custom_t["max_yaw"] = args.max_yaw
    if args.max_pitch is not None:
        custom_t["max_pitch"] = args.max_pitch
    if args.min_sharpness is not None:
        custom_t["min_sharpness"] = args.min_sharpness
    if args.pass_ratio is not None:
        custom_t["pass_ratio"] = args.pass_ratio

    segmenter = VideoFaceSegmenter(
        video_path=args.input,
        target_gender=args.gender,
        preset=args.preset,
        custom_thresholds=custom_t if custom_t else None,
        sample_fps=args.sample_fps,
        max_scene_duration=args.max_scene_len
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
