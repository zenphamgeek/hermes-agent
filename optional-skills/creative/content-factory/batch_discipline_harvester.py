#!/usr/bin/env python3
"""
Multi-Discipline High-Quality Footage Harvester & S3 Vault Indexer.
Disciplines:
  1. Mathematics (Toán học): Fractals, 3D Geometry, Algorithm Visualizations.
  2. Technology (Công nghệ): Server Racks, Cyber Defense, AI Synapses, IDE Coding.
  3. Chemistry (Hóa học): Molecular Structures, Crystal Growth, Reactions.
  4. Biology (Sinh học): DNA Helix, Cellular Mitosis, Neural Synapses, Protein Folding.
  5. Occupational Safety (An toàn lao động / HSE): PPE Gear, GHS Hazards, Fire Safety.
"""

import os
import sys
import json
import math
import time
import shutil
import tempfile
import argparse
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, List, Any
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path.home() / "workspace" / "output" / "factory"
FACTORY_DIR = Path(__file__).parent
STUDIO_DIR = Path(__file__).parent.parent / "video-motion-studio"
sys.path.insert(0, str(FACTORY_DIR))
sys.path.insert(0, str(STUDIO_DIR))

from footage_vault import FootageVault, S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET


class DisciplineFootageHarvester:
    """Creates, segments, and ingests high-definition footage across 5 core disciplines."""

    def __init__(self, vault: FootageVault = None):
        self.vault = vault or FootageVault()

    def generate_mathematics_footage(self, output_mp4: Path, duration_sec: int = 12, fps: int = 30) -> bool:
        """Render high-math 1080p footage: Fractal Mandelbrot / Torus knot & Matrix transformations."""
        w, h = 1920, 1080
        total_frames = duration_sec * fps
        temp_dir = Path(tempfile.mkdtemp(prefix="math_frames_"))

        try:
            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (8, 12, 24, 255))
                draw = ImageDraw.Draw(img)

                # Background Cartesian Grid
                for gx in range(0, w, 80):
                    draw.line([(gx, 0), (gx, h)], fill=(20, 35, 60, 80), width=1)
                for gy in range(0, h, 80):
                    draw.line([(0, gy), (w, gy)], fill=(20, 35, 60, 80), width=1)

                cx, cy = w // 2, h // 2

                # 3D Rotating Torus Knot / Lissajous Curve
                points = []
                for step in range(250):
                    theta = step * 0.05 + t * 0.8
                    r = 260 + 90 * math.cos(3 * theta)
                    x = cx + int(r * math.cos(2 * theta))
                    y = cy + int((r * math.sin(2 * theta) * 0.6) + 120 * math.sin(3 * theta))
                    points.append((x, y))

                for p_idx in range(len(points) - 1):
                    color_hue = int((p_idx * 1.4 + t * 60) % 255)
                    draw.line([points[p_idx], points[p_idx + 1]], fill=(56, 189, 248, 220), width=3)
                    if p_idx % 8 == 0:
                        draw.ellipse([points[p_idx][0]-4, points[p_idx][1]-4, points[p_idx][0]+4, points[p_idx][1]+4], fill=(244, 114, 182))

                # Mathematical Equations HUD
                draw.rectangle([80, 60, 520, 160], fill=(15, 23, 42, 230), outline=(56, 189, 248), width=2)
                draw.text((100, 75), "📐 MATHEMATICS & TOPOLOGY VISUALIZATION", fill=(56, 189, 248))
                draw.text((100, 105), f"z = e^(i*θ) | det(A - λI) = 0 | t={t:.2f}s", fill=(255, 255, 255))
                draw.text((100, 130), "Parametric Torus Knot: R=260, r=90, p=2, q=3", fill=(148, 163, 184))

                frame_path = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_path, "PNG")

            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_chemistry_footage(self, output_mp4: Path, duration_sec: int = 12, fps: int = 30) -> bool:
        """Render Chemistry 1080p footage: 3D Molecular orbital bonding & Crystal lattice."""
        w, h = 1920, 1080
        total_frames = duration_sec * fps
        temp_dir = Path(tempfile.mkdtemp(prefix="chem_frames_"))

        try:
            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (12, 10, 24, 255))
                draw = ImageDraw.Draw(img)

                # Molecular Ring Structure (Benzene / Fullerene rotating)
                cx, cy = w // 2, h // 2
                ring_r = 180 + int(20 * math.sin(t * 2))
                num_atoms = 6
                atoms = []
                for a_i in range(num_atoms):
                    angle = a_i * (2 * math.pi / num_atoms) + t * 0.5
                    ax = cx + int(ring_r * math.cos(angle))
                    ay = cy + int(ring_r * math.sin(angle) * 0.7)
                    atoms.append((ax, ay))

                for i in range(num_atoms):
                    next_i = (i + 1) % num_atoms
                    draw.line([atoms[i], atoms[next_i]], fill=(251, 146, 60, 240), width=4)
                    # Exothermic orbital glow
                    orb_r = 22 + int(6 * math.sin(t * 5 + i))
                    draw.ellipse([atoms[i][0]-orb_r, atoms[i][1]-orb_r, atoms[i][0]+orb_r, atoms[i][1]+orb_r], fill=(234, 88, 12, 160), outline=(255, 255, 255), width=2)
                    draw.text((atoms[i][0]-5, atoms[i][1]-6), "C", fill=(255, 255, 255))

                # HUD Label
                draw.rectangle([80, 60, 520, 160], fill=(15, 23, 42, 230), outline=(251, 146, 60), width=2)
                draw.text((100, 75), "🧪 ORGANIC CHEMISTRY & MOLECULAR DYNAMICS", fill=(251, 146, 60))
                draw.text((100, 105), f"sp2 Aromatic Resonance | C6H6 | ΔH < 0", fill=(255, 255, 255))
                draw.text((100, 130), f"Orbital Hybridization: t={t:.2f}s | Energy: 320 kJ/mol", fill=(148, 163, 184))

                frame_path = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_path, "PNG")

            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_biology_footage(self, output_mp4: Path, duration_sec: int = 12, fps: int = 30) -> bool:
        """Render Biology 1080p footage: DNA Double Helix rotation & Protein folding."""
        w, h = 1920, 1080
        total_frames = duration_sec * fps
        temp_dir = Path(tempfile.mkdtemp(prefix="bio_frames_"))

        try:
            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (8, 20, 18, 255))
                draw = ImageDraw.Draw(img)

                # DNA Double Helix
                num_base_pairs = 28
                for bp in range(num_base_pairs):
                    y_pos = int(220 + bp * 24)
                    phase = bp * 0.35 + t * 2.0
                    x1 = int(w // 2 + 220 * math.cos(phase))
                    x2 = int(w // 2 - 220 * math.cos(phase))

                    # Hydrogen bond
                    draw.line([(x1, y_pos), (x2, y_pos)], fill=(74, 222, 128, 160), width=3)

                    # Nucleotide nodes (A-T, G-C)
                    draw.ellipse([x1 - 8, y_pos - 8, x1 + 8, y_pos + 8], fill=(34, 197, 94), outline=(255, 255, 255), width=1)
                    draw.ellipse([x2 - 8, y_pos - 8, x2 + 8, y_pos + 8], fill=(59, 130, 246), outline=(255, 255, 255), width=1)

                # HUD Label
                draw.rectangle([80, 60, 520, 160], fill=(15, 23, 42, 230), outline=(74, 222, 128), width=2)
                draw.text((100, 75), "🧬 GENETICS & MOLECULAR BIOLOGY DYNAMICS", fill=(74, 222, 128))
                draw.text((100, 105), "DNA Double Helix (A-T / G-C Base Pairing)", fill=(255, 255, 255))
                draw.text((100, 130), f"CRISPR-Cas9 Target Sequence | t={t:.2f}s", fill=(148, 163, 184))

                frame_path = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_path, "PNG")

            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_safety_footage(self, output_mp4: Path, duration_sec: int = 12, fps: int = 30) -> bool:
        """Render Occupational Safety / HSE 1080p footage: PPE Shield, GHS Hazards, Fire Radar."""
        w, h = 1920, 1080
        total_frames = duration_sec * fps
        temp_dir = Path(tempfile.mkdtemp(prefix="safety_frames_"))

        try:
            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (20, 16, 10, 255))
                draw = ImageDraw.Draw(img)

                # Warning Grid & Industrial Hazard Lines
                for gy in range(0, h, 60):
                    draw.line([(0, gy), (w, gy)], fill=(45, 35, 15, 80), width=1)

                cx, cy = w // 2, h // 2

                # Safety Shield & Radar Scanner
                pulse_r = int(220 + 20 * math.sin(t * 3))
                draw.ellipse([cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r], outline=(234, 179, 8, 180), width=3)
                draw.polygon([
                    (cx, cy - 140), (cx + 120, cy - 60), (cx + 100, cy + 90),
                    (cx, cy + 150), (cx - 100, cy + 90), (cx - 120, cy - 60)
                ], fill=(161, 98, 7, 180), outline=(253, 224, 71), width=4)

                draw.text((cx - 70, cy - 10), "PPE SECURED", fill=(255, 255, 255))
                draw.text((cx - 65, cy + 20), "ZERO INCIDENT", fill=(254, 240, 138))

                # HUD Label
                draw.rectangle([80, 60, 560, 160], fill=(15, 23, 42, 230), outline=(234, 179, 8), width=2)
                draw.text((100, 75), "🦺 OCCUPATIONAL HEALTH & SAFETY (HSE 2026)", fill=(234, 179, 8))
                draw.text((100, 105), "GHS Chemical Safety | Industrial PPE Compliance", fill=(255, 255, 255))
                draw.text((100, 130), f"Incident Free: 100% | ISO 45001 Standard | t={t:.2f}s", fill=(148, 163, 184))

                frame_path = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_path, "PNG")

            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_cafe_footage(self, output_mp4: Path, duration_sec: int = 12, fps: int = 30) -> bool:
        """Render Cafe & Coffee 1080p footage: Espresso extraction, Latte Art swirl & roasted coffee beans."""
        w, h = 1920, 1080
        total_frames = duration_sec * fps
        temp_dir = Path(tempfile.mkdtemp(prefix="cafe_frames_"))

        try:
            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (26, 18, 12, 255))
                draw = ImageDraw.Draw(img)

                # Warm Cozy Coffee Shop Lighting
                for gx in range(0, w, 120):
                    draw.line([(gx, 0), (gx, h)], fill=(45, 30, 20, 70), width=1)

                cx, cy = w // 2, h // 2

                # Ceramic Coffee Cup & Golden Crema Latte Art Swirl
                draw.ellipse([cx - 240, cy - 240, cx + 240, cy + 240], fill=(245, 240, 230), outline=(215, 200, 180), width=12)
                draw.ellipse([cx - 210, cy - 210, cx + 210, cy + 210], fill=(101, 52, 23))

                # Rotating Latte Art Rosetta & Heart Swirl
                for petal in range(12):
                    p_angle = petal * (2 * math.pi / 12) + t * 0.4
                    pr = 60 + int(30 * math.sin(t * 3 + petal))
                    px = cx + int(pr * math.cos(p_angle))
                    py = cy + int(pr * math.sin(p_angle))
                    draw.ellipse([px - 28, py - 28, px + 28, py + 28], fill=(255, 253, 245, 210))

                # Coffee Steam Rising
                for si in range(5):
                    sx = cx - 80 + si * 40
                    sy = cy - 260 - int((t * 60 + si * 40) % 200)
                    draw.arc([sx - 30, sy - 50, sx + 30, sy + 50], start=0, end=180, fill=(255, 255, 255, 120), width=3)

                # HUD Label
                draw.rectangle([80, 60, 560, 160], fill=(20, 14, 10, 235), outline=(217, 119, 6), width=2)
                draw.text((100, 75), "☕ CAFE & SPECIALTY COFFEE BREWING", fill=(245, 158, 11))
                draw.text((100, 105), "Espresso Crema Extraction | Arabica & Robusta Blend", fill=(255, 255, 255))
                draw.text((100, 130), f"Brew Pressure: 9.2 Bar | Temp: 93.5°C | t={t:.2f}s", fill=(214, 211, 209))

                frame_path = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_path, "PNG")

            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_food_footage(self, output_mp4: Path, duration_sec: int = 12, fps: int = 30) -> bool:
        """Render Food & Culinary 1080p footage: Gourmet Pan Sizzle, Fresh Ingredients & Plating."""
        w, h = 1920, 1080
        total_frames = duration_sec * fps
        temp_dir = Path(tempfile.mkdtemp(prefix="food_frames_"))

        try:
            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (18, 14, 14, 255))
                draw = ImageDraw.Draw(img)

                # Kitchen Grill & Dark Slate Board
                for gy in range(0, h, 70):
                    draw.line([(0, gy), (w, gy)], fill=(35, 25, 25, 70), width=1)

                cx, cy = w // 2, h // 2

                # Gourmet Round Plating
                draw.ellipse([cx - 260, cy - 260, cx + 260, cy + 260], fill=(28, 25, 23), outline=(68, 64, 60), width=4)
                
                # Sizzling Gourmet Dish with Fresh Garnishes
                dish_r = 160
                draw.ellipse([cx - dish_r, cy - dish_r, cx + dish_r, cy + dish_r], fill=(120, 53, 15))
                
                # Fresh herbs and simmering golden sauce particles
                for gi in range(8):
                    gx = cx + int(90 * math.cos(gi * 0.8 + t * 0.5))
                    gy = cy + int(90 * math.sin(gi * 0.8 + t * 0.5))
                    draw.ellipse([gx - 12, gy - 12, gx + 12, gy + 12], fill=(34, 197, 94))
                    # Steam sizzle
                    s_r = int(6 + 4 * math.sin(t * 8 + gi))
                    draw.ellipse([gx - s_r, gy - 20 - s_r, gx + s_r, gy - 20 + s_r], fill=(254, 240, 138, 180))

                # HUD Label
                draw.rectangle([80, 60, 560, 160], fill=(28, 25, 23, 235), outline=(239, 68, 68), width=2)
                draw.text((100, 75), "🍳 GOURMET CULINARY & FOOD ARTISTRY", fill=(239, 68, 68))
                draw.text((100, 105), "Artisanal Cuisine Preparation & Fresh Ingredients", fill=(255, 255, 255))
                draw.text((100, 130), f"Wok Temperature: 220°C | Sizzle Dynamics: Active | t={t:.2f}s", fill=(214, 211, 209))

                frame_path = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_path, "PNG")

            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_logistics_footage(self, output_mp4: Path, duration_sec: int = 12, fps: int = 30) -> bool:
        """Render Logistics 1080p footage: Automated AGV Warehouse, Supply Chain Network & Freight Containers."""
        w, h = 1920, 1080
        total_frames = duration_sec * fps
        temp_dir = Path(tempfile.mkdtemp(prefix="logistics_frames_"))

        try:
            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (10, 16, 26, 255))
                draw = ImageDraw.Draw(img)

                # Smart Warehouse Conveyor Lines
                for gx in range(0, w, 100):
                    draw.line([(gx, 0), (gx, h)], fill=(20, 35, 55, 80), width=1)
                for gy in range(0, h, 100):
                    draw.line([(0, gy), (w, gy)], fill=(20, 35, 55, 80), width=1)

                cx, cy = w // 2, h // 2

                # Moving Automated AGV Robots & Cargo Containers
                num_agv = 5
                for agv_i in range(num_agv):
                    agv_x = int((w * (agv_i / num_agv) + t * 120) % (w - 200) + 100)
                    agv_y = cy - 100 + (agv_i % 3) * 120
                    # AGV Chassis
                    draw.rectangle([agv_x - 70, agv_y - 40, agv_x + 70, agv_y + 40], fill=(30, 58, 138), outline=(96, 165, 250), width=2)
                    # Cargo Pallet
                    draw.rectangle([agv_x - 50, agv_y - 25, agv_x + 50, agv_y + 25], fill=(202, 138, 4))
                    # Lidar Laser Scan
                    draw.line([(agv_x, agv_y), (agv_x + 90, agv_y - 30)], fill=(239, 68, 68, 200), width=2)

                # Global Supply Chain Transit Routes
                for route_i in range(4):
                    ry = int(cy + 220 + 20 * math.sin(t * 2 + route_i))
                    draw.line([(100, ry), (w - 100, ry)], fill=(56, 189, 248, 140), width=2)

                # HUD Label
                draw.rectangle([80, 60, 580, 160], fill=(15, 23, 42, 235), outline=(59, 130, 246), width=2)
                draw.text((100, 75), "📦 SMART LOGISTICS & AUTOMATED SUPPLY CHAIN", fill=(59, 130, 246))
                draw.text((100, 105), "Automated AGV Fleets | High-Bay Warehouse Routing", fill=(255, 255, 255))
                draw.text((100, 130), f"Throughput: 4,800 Units/Hr | Lidar Tracking: Active | t={t:.2f}s", fill=(148, 163, 184))

                frame_path = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_path, "PNG")

            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def harvest_all_disciplines(self) -> Dict[str, Any]:
        """Harvest and ingest footage for all disciplines (including Cafe, Food, Logistics)."""
        temp_dir = Path(tempfile.mkdtemp(prefix="harvest_master_"))
        summary = {"total_clips_added": 0, "disciplines": {}}

        try:
            tasks = [
                ("mathematics", "Fractal Geometry & Torus Matrix Topology", ["math", "fractal", "calculus", "geometry", "topology"], self.generate_mathematics_footage),
                ("chemistry", "Molecular Orbital Resonance & Crystal Lattice", ["chemistry", "molecule", "reaction", "crystal", "organic"], self.generate_chemistry_footage),
                ("biology", "DNA Double Helix & Synaptic Replication", ["biology", "dna", "genetics", "neuron", "protein", "crispr"], self.generate_biology_footage),
                ("occupational-safety", "Industrial PPE Compliance & Hazard Prevention", ["hse", "safety", "ppe", "ghs", "fire-safety", "ergonomics"], self.generate_safety_footage),
                ("cafe", "Specialty Coffee Brewing & Espresso Latte Art", ["cafe", "coffee", "espresso", "latte-art", "barista", "brewing"], self.generate_cafe_footage),
                ("food", "Gourmet Culinary Artistry & Sizzling Ingredients", ["food", "culinary", "cooking", "gourmet", "restaurant", "chef"], self.generate_food_footage),
                ("logistics", "Automated AGV Warehousing & Global Supply Chain", ["logistics", "warehouse", "supply-chain", "agv", "freight", "cargo"], self.generate_logistics_footage)
            ]

            for discipline, title, tags, gen_fn in tasks:
                print(f"\n[*] Processing Discipline: {discipline.upper()}...")
                raw_mp4 = temp_dir / f"master_{discipline}.mp4"
                ok = gen_fn(raw_mp4, duration_sec=12, fps=30)
                if ok and raw_mp4.exists():
                    print(f"  • Ingesting & Segmenting into S3 Vault ({raw_mp4.stat().st_size // 1024} KB)...")
                    clips = self.vault.segment_and_ingest_video(
                        video_file=raw_mp4,
                        base_title=title,
                        category=discipline,
                        tags=tags,
                        clip_duration=6
                    )
                    summary["disciplines"][discipline] = len(clips)
                    summary["total_clips_added"] += len(clips)
                    print(f"  [✓] {len(clips)} B-Roll clips added for {discipline}.")

            return summary
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Multi-Discipline Footage Harvester")
    parser.add_argument("--harvest-all", action="store_true", help="Harvest footage for all 5 disciplines")
    args = parser.parse_args()

    harvester = DisciplineFootageHarvester()
    print("[*] Starting Multi-Discipline Footage Harvester (500GB P15 S3 Vault)...")
    res = harvester.harvest_all_disciplines()
    print(f"\n[✓] Harvesting Completed: Added {res['total_clips_added']} B-Roll clips into S3 Vault.")


if __name__ == "__main__":
    main()
