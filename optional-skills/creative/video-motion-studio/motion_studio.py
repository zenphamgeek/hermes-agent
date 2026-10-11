#!/usr/bin/env python3
"""
Video Motion Studio — High-Tech Infographics, SVG Vector Animation & Motion Compositing Engine.
Generates dynamic visual assets, architectural diagrams, vector animations, and camera motion effects.
"""

import os
import sys
import math
import json
import time
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image, ImageDraw, ImageFont

# Dimensions
WIDTH_16_9 = 1920
HEIGHT_16_9 = 1080
WIDTH_9_16 = 1080
HEIGHT_9_16 = 1920


class VideoMotionStudio:
    """Core Graphics & High-Quality Vector Animation Engine."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (Path.home() / "workspace" / "output" / "factory")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Tech Infographic Generator ────────────────────────────────────

    def generate_tech_infographic(
        self,
        title: str,
        subtitle: str,
        nodes: List[Dict[str, str]],
        output_path: Path,
        aspect: str = "16:9",
        theme: str = "cyberpunk"
    ) -> bool:
        """
        Generate a futuristic, high-tech infographic diagram with glassmorphism cards and connected nodes.
        """
        w = WIDTH_16_9 if aspect == "16:9" else WIDTH_9_16
        h = HEIGHT_16_9 if aspect == "16:9" else HEIGHT_9_16

        img = Image.new("RGBA", (w, h), (11, 15, 25, 255))
        draw = ImageDraw.Draw(img)

        # Draw deep-tech subtle grid lines
        grid_color = (30, 41, 59, 120)
        grid_spacing = 60
        for x in range(0, w, grid_spacing):
            draw.line([(x, 0), (x, h)], fill=grid_color, width=1)
        for y in range(0, h, grid_spacing):
            draw.line([(0, y), (w, y)], fill=grid_color, width=1)

        # Outer cybernetic border
        draw.rectangle([40, 40, w - 40, h - 40], outline=(56, 189, 248, 80), width=2)
        draw.rectangle([50, 50, w - 50, h - 50], outline=(147, 197, 253, 40), width=1)

        # Corner tech brackets
        bracket_len = 30
        draw.line([(40, 40), (40 + bracket_len, 40)], fill=(0, 240, 255), width=4)
        draw.line([(40, 40), (40, 40 + bracket_len)], fill=(0, 240, 255), width=4)
        draw.line([(w - 40, 40), (w - 40 - bracket_len, 40)], fill=(0, 240, 255), width=4)
        draw.line([(w - 40, 40), (w - 40, 40 + bracket_len)], fill=(0, 240, 255), width=4)
        draw.line([(40, h - 40), (40 + bracket_len, h - 40)], fill=(0, 240, 255), width=4)
        draw.line([(40, h - 40), (40, h - 40 - bracket_len)], fill=(0, 240, 255), width=4)
        draw.line([(w - 40, h - 40), (w - 40 - bracket_len, h - 40)], fill=(0, 240, 255), width=4)
        draw.line([(w - 40, h - 40), (w - 40, h - 40 - bracket_len)], fill=(0, 240, 255), width=4)

        # Header Badge
        badge_w, badge_h = 360, 45
        draw.rectangle([80, 80, 80 + badge_w, 80 + badge_h], fill=(37, 99, 235, 220), outline=(96, 165, 250), width=1)
        draw.text((100, 92), "⚡ SYSTEM ARCHITECTURE & TELEMETRY", fill=(255, 255, 255))

        # Main Title & Subtitle
        draw.text((80, 150), title.upper(), fill=(255, 255, 255))
        draw.text((80, 210), subtitle, fill=(56, 189, 248))

        # Render Nodes
        if not nodes:
            nodes = [
                {"title": "Core Agent", "desc": "Autonomous execution & task graph", "badge": "ACTIVE"},
                {"title": "Secret Vault", "desc": "Zero-trust token & API key isolation", "badge": "SECURE"},
                {"title": "Mission Control", "desc": "Real-time Telegram & IDE bridge", "badge": "SYNCED"},
                {"title": "Local GPU Cluster", "desc": "Sovereign inference on ThinkPad P15", "badge": "ON-PREM"},
            ]

        num_nodes = min(len(nodes), 4)
        card_margin = 80
        available_w = w - (card_margin * 2)
        card_w = (available_w - (30 * (num_nodes - 1))) // num_nodes
        card_h = 420
        card_y = 320

        # Connected bus line
        bus_y = card_y + 60
        draw.line([(card_margin, bus_y), (w - card_margin, bus_y)], fill=(59, 130, 246, 180), width=3)

        for i, node in enumerate(nodes[:4]):
            cx = card_margin + i * (card_w + 30)
            # Node connection dot
            draw.ellipse([cx + card_w // 2 - 8, bus_y - 8, cx + card_w // 2 + 8, bus_y + 8], fill=(0, 240, 255), outline=(255, 255, 255), width=2)
            # Card background
            draw.rectangle([cx, card_y, cx + card_w, card_y + card_h], fill=(15, 23, 42, 230), outline=(56, 189, 248, 120), width=2)
            draw.line([(cx, card_y + 50), (cx + card_w, card_y + 50)], fill=(56, 189, 248, 80), width=1)

            # Badge
            badge_text = node.get("badge", f"NODE 0{i+1}")
            draw.rectangle([cx + 15, card_y + 12, cx + 130, card_y + 38], fill=(30, 58, 138, 200), outline=(96, 165, 250), width=1)
            draw.text((cx + 25, card_y + 18), badge_text, fill=(147, 197, 253))

            # Node Title & Description
            draw.text((cx + 20, card_y + 80), node.get("title", f"Module {i+1}"), fill=(255, 255, 255))
            desc = node.get("desc", "High efficiency autonomous service.")
            draw.text((cx + 20, card_y + 140), desc[:35], fill=(203, 213, 225))
            if len(desc) > 35:
                draw.text((cx + 20, card_y + 180), desc[35:70], fill=(148, 163, 184))

            # Telemetry progress bar
            bar_y = card_y + card_h - 60
            draw.rectangle([cx + 20, bar_y, cx + card_w - 20, bar_y + 12], fill=(30, 41, 59), outline=(71, 85, 105), width=1)
            pct = 75 + (i * 7) % 25
            draw.rectangle([cx + 20, bar_y, cx + 20 + int((card_w - 40) * (pct / 100)), bar_y + 12], fill=(0, 240, 255))
            draw.text((cx + 20, bar_y - 25), f"OPTIMIZATION: {pct}%", fill=(56, 189, 248))

        # Footer telemetry
        draw.text((80, h - 100), "🔒 SOVEREIGN ZERO-TRUST • 100% AIR-GAPPED HARDWARE ENCRYPTION", fill=(148, 163, 184))
        draw.text((w - 450, h - 100), "STATUS: OPTIMAL • LATENCY: 0.8ms", fill=(52, 211, 153))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path.exists()

    # ── 2. High-Quality Multi-Layered SVG Animation Engine ────────────────

    def generate_svg_animation(
        self,
        animation_type: str,
        duration_sec: int,
        output_mp4: Path,
        fps: int = 30,
        title: Optional[str] = None
    ) -> bool:
        """
        Generate high-fidelity vector animation frames and compile into broadcast-grade MP4.
        Supported animation_type:
          1. 'architecture-flow' : Data packets flowing through components
          2. 'security-shield'   : Concentric zero-trust rings & cryptographic laser sweep
          3. 'cyber-hud'         : Holographic dials, audio waveforms & telemetry HUD
          4. 'neural-network'    : Pulsing synapses and deep learning signal propagation
          5. 'vibe-coding'       : Live code typing simulation, execution logs & commit pulses
          6. 'pulsing-network'   : Central AI core with dynamic radar scan
        """
        total_frames = int(duration_sec * fps)
        temp_dir = Path(tempfile.mkdtemp(prefix="svg_anim_hq_"))

        try:
            w, h = WIDTH_16_9, HEIGHT_16_9
            for f in range(total_frames):
                t = f / fps
                progress = f / total_frames

                img = Image.new("RGBA", (w, h), (8, 12, 22, 255))
                draw = ImageDraw.Draw(img)

                # Draw Ambient Cyber Grid
                for gx in range(0, w, 80):
                    draw.line([(gx, 0), (gx, h)], fill=(20, 30, 48, 80), width=1)
                for gy in range(0, h, 80):
                    draw.line([(0, gy), (w, gy)], fill=(20, 30, 48, 80), width=1)

                # Outer Cyberpunk Frame
                draw.rectangle([30, 30, w - 30, h - 30], outline=(38, 55, 85, 180), width=2)
                draw.line([(30, 30), (120, 30)], fill=(0, 240, 255), width=4)
                draw.line([(30, 30), (30, 120)], fill=(0, 240, 255), width=4)

                # ── SCENE 1: ARCHITECTURE FLOW ──
                if animation_type == "architecture-flow":
                    nodes = [
                        {"name": "TELEGRAM UI", "x": 250, "y": 540, "color": (56, 189, 248)},
                        {"name": "HERMES CORE", "x": 750, "y": 540, "color": (168, 85, 247)},
                        {"name": "SANDBOX LXD", "x": 1250, "y": 380, "color": (34, 197, 94)},
                        {"name": "POSTGRES & S3", "x": 1250, "y": 700, "color": (234, 179, 8)},
                        {"name": "TRAE IDE", "x": 1680, "y": 540, "color": (239, 68, 68)},
                    ]

                    # Draw pipelines
                    draw.line([(nodes[0]["x"], 540), (nodes[1]["x"], 540)], fill=(75, 85, 99), width=4)
                    draw.line([(nodes[1]["x"], 540), (nodes[2]["x"], 380)], fill=(75, 85, 99), width=4)
                    draw.line([(nodes[1]["x"], 540), (nodes[3]["x"], 700)], fill=(75, 85, 99), width=4)
                    draw.line([(nodes[2]["x"], 380), (nodes[4]["x"], 540)], fill=(75, 85, 99), width=4)
                    draw.line([(nodes[3]["x"], 700), (nodes[4]["x"], 540)], fill=(75, 85, 99), width=4)

                    # Flowing data packets (animated)
                    pkt_t = (t * 1.8) % 1.0
                    px1 = int(nodes[0]["x"] + (nodes[1]["x"] - nodes[0]["x"]) * pkt_t)
                    draw.ellipse([px1 - 8, 540 - 8, px1 + 8, 540 + 8], fill=(0, 240, 255))

                    px2 = int(nodes[1]["x"] + (nodes[2]["x"] - nodes[1]["x"]) * pkt_t)
                    py2 = int(540 + (380 - 540) * pkt_t)
                    draw.ellipse([px2 - 8, py2 - 8, px2 + 8, py2 + 8], fill=(34, 197, 94))

                    px3 = int(nodes[1]["x"] + (nodes[3]["x"] - nodes[1]["x"]) * pkt_t)
                    py3 = int(540 + (700 - 540) * pkt_t)
                    draw.ellipse([px3 - 8, py3 - 8, px3 + 8, py3 + 8], fill=(234, 179, 8))

                    # Render Node Cards
                    for n in nodes:
                        nx, ny = n["x"], n["y"]
                        # Pulse glow
                        pulse = int(10 * math.sin(t * 5 + nx))
                        draw.rectangle([nx - 110 - pulse, ny - 55 - pulse, nx + 110 + pulse, ny + 55 + pulse], outline=(*n["color"][:3], 100), width=1)
                        draw.rectangle([nx - 100, ny - 50, nx + 100, ny + 50], fill=(15, 23, 42, 240), outline=n["color"], width=2)
                        draw.text((nx - 60, ny - 10), n["name"], fill=(255, 255, 255))

                # ── SCENE 2: SECURITY SHIELD VAULT ──
                elif animation_type == "security-shield":
                    cx, cy = w // 2, h // 2
                    # Expanding cryptographic rings
                    for r_idx, base_r in enumerate([140, 220, 310, 420]):
                        rot_speed = (r_idx + 1) * 0.5 * (-1 if r_idx % 2 == 0 else 1)
                        ring_r = base_r + int(10 * math.sin(t * 3 + r_idx))
                        draw.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(56, 189, 248, 140), width=2)
                        # Hash markers along ring
                        for a_step in range(0, 360, 45):
                            rad = math.radians(a_step + math.degrees(t * rot_speed))
                            hx = int(cx + ring_r * math.cos(rad))
                            hy = int(cy + ring_r * math.sin(rad))
                            draw.rectangle([hx - 4, hy - 4, hx + 4, hy + 4], fill=(0, 240, 255))

                    # Central Zero-Trust Padlock Shield
                    shield_pulse = int(15 * math.sin(t * 4))
                    draw.ellipse([cx - 80 - shield_pulse, cy - 80 - shield_pulse, cx + 80 + shield_pulse, cy + 80 + shield_pulse], fill=(37, 99, 235, 180), outline=(255, 255, 255), width=3)
                    draw.text((cx - 50, cy - 10), "ZERO-TRUST", fill=(255, 255, 255))
                    draw.text((cx - 65, cy + 15), "HARDWARE VAULT", fill=(147, 197, 253))

                    # Scanning laser beam
                    laser_angle = math.radians((t * 90) % 360)
                    lx = int(cx + 450 * math.cos(laser_angle))
                    ly = int(cy + 450 * math.sin(laser_angle))
                    draw.line([(cx, cy), (lx, ly)], fill=(0, 240, 255, 220), width=3)

                # ── SCENE 3: CYBER HUD TELEMETRY ──
                elif animation_type == "cyber-hud":
                    cx, cy = w // 2, h // 2
                    # Animated Waveform Audio Spectrum
                    num_bars = 48
                    bar_w = 12
                    spectrum_w = num_bars * (bar_w + 6)
                    start_x = (w - spectrum_w) // 2
                    for b in range(num_bars):
                        bar_h = int(30 + 120 * abs(math.sin(t * 6 + b * 0.25)))
                        bx = start_x + b * (bar_w + 6)
                        by = cy + 220 - bar_h // 2
                        draw.rectangle([bx, by, bx + bar_w, by + bar_h], fill=(0, 240, 255))

                    # Rotating Holographic Dial
                    dial_r = 180
                    draw.ellipse([cx - dial_r, cy - 100 - dial_r, cx + dial_r, cy - 100 + dial_r], outline=(168, 85, 247), width=3)
                    for deg in range(0, 360, 30):
                        rad = math.radians(deg + math.degrees(t * 0.8))
                        dx = int(cx + dial_r * math.cos(rad))
                        dy = int(cy - 100 + dial_r * math.sin(rad))
                        draw.line([(dx, dy), (int(dx + 15 * math.cos(rad)), int(dy + 15 * math.sin(rad)))], fill=(216, 180, 254), width=2)

                    draw.text((cx - 70, cy - 110), f"INFERENCE: {98.4 + 1.2*math.sin(t):.1f}%", fill=(255, 255, 255))
                    draw.text((cx - 50, cy - 85), "GPU VRAM: 11.2 GB", fill=(52, 211, 153))

                # ── SCENE 4: NEURAL NETWORK SYNAPSE ──
                elif animation_type == "neural-network":
                    layers = [
                        [(350, y) for y in [300, 440, 580, 720]],
                        [(750, y) for y in [240, 380, 520, 660, 800]],
                        [(1150, y) for y in [240, 380, 520, 660, 800]],
                        [(1550, y) for y in [360, 520, 680]],
                    ]

                    # Draw Synapses
                    for l_idx in range(len(layers) - 1):
                        for p1 in layers[l_idx]:
                            for p2 in layers[l_idx + 1]:
                                alpha_syn = int(40 + 35 * math.sin(t * 4 + p1[1] + p2[1]))
                                draw.line([p1, p2], fill=(56, 189, 248, alpha_syn), width=1)

                    # Propagating fire pulses
                    fire_t = (t * 2.2) % 1.0
                    for p1 in layers[0]:
                        for p2 in layers[1][:2]:
                            fx = int(p1[0] + (p2[0] - p1[0]) * fire_t)
                            fy = int(p1[1] + (p2[1] - p1[1]) * fire_t)
                            draw.ellipse([fx - 5, fy - 5, fx + 5, fy + 5], fill=(0, 240, 255))

                    # Render Neuron Nodes
                    for l_idx, layer in enumerate(layers):
                        for nx, ny in layer:
                            glow = int(6 * math.sin(t * 5 + nx + ny))
                            draw.ellipse([nx - 16 - glow, ny - 16 - glow, nx + 16 + glow, ny + 16 + glow], fill=(37, 99, 235, 140))
                            draw.ellipse([nx - 12, ny - 12, nx + 12, ny + 12], fill=(0, 240, 255), outline=(255, 255, 255), width=2)

                # ── SCENE 5: VIBE CODING IDE TERMINAL ──
                elif animation_type == "vibe-coding":
                    # Terminal Window Frame
                    draw.rectangle([200, 160, w - 200, h - 160], fill=(15, 23, 42, 240), outline=(56, 189, 248, 160), width=2)
                    # Window Topbar
                    draw.rectangle([200, 160, w - 200, 220], fill=(30, 41, 59), outline=(56, 189, 248, 80), width=1)
                    # Window buttons
                    draw.ellipse([220, 182, 236, 198], fill=(239, 68, 68))
                    draw.ellipse([246, 182, 262, 198], fill=(234, 179, 8))
                    draw.ellipse([272, 182, 288, 198], fill=(34, 197, 94))
                    draw.text((320, 180), "antigravity — hermes-agent • Vibe Coding Session (Active)", fill=(203, 213, 225))

                    # Code Lines Typing Animation
                    code_samples = [
                        "> @trae: optimize multi-window CDP screenshot pipeline",
                        "> [INFO] Connecting to CDP port 9339 across 2 workspaces...",
                        "> [SUCCESS] Captured insilos_ee (1080p) & VerticalRisk (1080p)",
                        "> [AUTO-FIX] Zero-Trust telemetry verified • Test suite 100% green",
                        "> git commit -m 'feat: autonomous content factory and svg motion'",
                        "> [DEPLOY] Video published to YouTube & Telegram broadcast dispatched ✓"
                    ]
                    num_lines_shown = min(len(code_samples), int(t * 1.6) + 1)
                    for l_i in range(num_lines_shown):
                        line_y = 260 + l_i * 65
                        line_text = code_samples[l_i]
                        col = (52, 211, 153) if "SUCCESS" in line_text or "DEPLOY" in line_text else ((56, 189, 248) if "@trae" in line_text else (241, 245, 249))
                        draw.text((250, line_y), line_text, fill=col)

                    # Blinking cursor
                    if int(t * 3) % 2 == 0:
                        cur_y = 260 + (num_lines_shown - 1) * 65
                        draw.rectangle([250 + len(code_samples[num_lines_shown-1]) * 10, cur_y, 250 + len(code_samples[num_lines_shown-1]) * 10 + 12, cur_y + 24], fill=(0, 240, 255))

                # ── DEFAULT: PULSING NETWORK RADAR ──
                else:
                    core_x, core_y = w // 2, h // 2
                    pulse_r = int(120 + 30 * math.sin(t * 4))
                    for r_step in [100, 220, 360, 500]:
                        dyn_r = int(r_step + 20 * math.sin(t * 2 + r_step))
                        draw.ellipse([core_x - dyn_r, core_y - dyn_r, core_x + dyn_r, core_y + dyn_r], outline=(56, 189, 248, 120), width=2)

                    # Scanner beam
                    angle = (t * 1.5) % (2 * math.pi)
                    beam_x = core_x + int(550 * math.cos(angle))
                    beam_y = core_y + int(550 * math.sin(angle))
                    draw.line([(core_x, core_y), (beam_x, beam_y)], fill=(0, 240, 255, 200), width=3)

                    # Central core
                    draw.ellipse([core_x - pulse_r, core_y - pulse_r, core_x + pulse_r, core_y + pulse_r], fill=(37, 99, 235, 160), outline=(255, 255, 255), width=3)
                    draw.text((core_x - 70, core_y - 10), "AI AGENT CORE", fill=(255, 255, 255))

                # Global HUD Header Text
                header_title = title or f"⚡ VECTOR MOTION ENGINE • {animation_type.upper()}"
                draw.text((80, 80), header_title, fill=(56, 189, 248))
                draw.text((80, 120), f"FRAME: {f:04d}/{total_frames:04d} | TIME: {t:.2f}s | FPS: {fps}", fill=(148, 163, 184))

                frame_file = temp_dir / f"frame_{f:05d}.png"
                img.save(frame_file, "PNG")

            # Compile into MP4
            output_mp4.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%05d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                str(output_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_mp4.exists()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ── 3. Camera Motion & Ken Burns Compositor ───────────────────────────

    def apply_camera_motion_and_render(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
        effect: str = "zoom-in",
        duration: Optional[int] = None
    ) -> bool:
        """
        Apply smooth Ken Burns camera pan/zoom effect to an image and composite with audio voiceover.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dur = duration or 5
        if audio_path.exists():
            try:
                cmd_dur = ["ffmpeg", "-i", str(audio_path)]
                res_dur = subprocess.run(cmd_dur, capture_output=True, text=True, timeout=10)
                for line in res_dur.stderr.split("\n"):
                    if "Duration:" in line:
                        d_str = line.split("Duration:")[1].split(",")[0].strip()
                        h, m, s = d_str.split(":")
                        dur = max(2, int(float(h) * 3600 + float(m) * 60 + float(s)) + 1)
                        break
            except Exception:
                pass

        total_frames = dur * 25

        if effect == "zoom-in":
            vf = f"zoompan=z='min(zoom+0.0015,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={WIDTH_16_9}x{HEIGHT_16_9}:fps=25"
        elif effect == "zoom-out":
            vf = f"zoompan=z='if(lte(zoom,1.0),1.25,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={WIDTH_16_9}x{HEIGHT_16_9}:fps=25"
        elif effect == "pan-right":
            vf = f"zoompan=z='1.15':x='if(lte(on,1),0,x+1)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={WIDTH_16_9}x{HEIGHT_16_9}:fps=25"
        else:
            vf = f"scale={WIDTH_16_9}:{HEIGHT_16_9}"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-vf", vf,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-t", str(dur),
            str(output_path)
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return res.returncode == 0 and output_path.exists()

    # ── 4. Combined SVG Motion Scene with Audio ──────────────────────────

    def render_svg_scene_with_audio(
        self,
        animation_type: str,
        audio_path: Path,
        output_path: Path,
        title: Optional[str] = None
    ) -> bool:
        """Render a complete animated SVG motion video scene with synchronized voiceover audio."""
        dur = 5
        if audio_path.exists():
            try:
                cmd_dur = ["ffmpeg", "-i", str(audio_path)]
                res_dur = subprocess.run(cmd_dur, capture_output=True, text=True, timeout=10)
                for line in res_dur.stderr.split("\n"):
                    if "Duration:" in line:
                        d_str = line.split("Duration:")[1].split(",")[0].strip()
                        h, m, s = d_str.split(":")
                        dur = max(2, int(float(h) * 3600 + float(m) * 60 + float(s)) + 1)
                        break
            except Exception:
                pass

        temp_video = Path(tempfile.mktemp(suffix=".mp4"))
        try:
            ok_anim = self.generate_svg_animation(animation_type, dur, temp_video, fps=30, title=title)
            if not ok_anim or not temp_video.exists():
                return False

            cmd_mux = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
            res_mux = subprocess.run(cmd_mux, capture_output=True, text=True, timeout=60)
            return res_mux.returncode == 0 and output_path.exists()
        finally:
            if temp_video.exists():
                temp_video.unlink()

    # ── 5. Multi-Voice Debate Podcast Studio Compositor ───────────────────

    def render_debate_studio_scene(
        self,
        topic: str,
        speaker_name: str,
        speaker_role: str,
        speech_text: str,
        key_point: str,
        audio_path: Path,
        output_path: Path,
        fps: int = 30
    ) -> bool:
        """
        Render a high-production-value split-screen Debate Podcast scene.
        Highlights the active speaker with a neon glow border & animated sound waveform.
        """
        dur = 5
        if audio_path.exists():
            try:
                cmd_dur = ["ffmpeg", "-i", str(audio_path)]
                res_dur = subprocess.run(cmd_dur, capture_output=True, text=True, timeout=10)
                for line in res_dur.stderr.split("\n"):
                    if "Duration:" in line:
                        d_str = line.split("Duration:")[1].split(",")[0].strip()
                        h, m, s = d_str.split(":")
                        dur = max(2, int(float(h) * 3600 + float(m) * 60 + float(s)) + 1)
                        break
            except Exception:
                pass

        total_frames = int(dur * fps)
        temp_dir = Path(tempfile.mkdtemp(prefix="debate_frames_"))
        temp_video = Path(tempfile.mktemp(suffix=".mp4"))

        try:
            w, h = WIDTH_16_9, HEIGHT_16_9

            for f in range(total_frames):
                t = f / fps
                img = Image.new("RGBA", (w, h), (10, 14, 26, 255))
                draw = ImageDraw.Draw(img)

                # Ambient Studio Background Gradients & Grid
                for gx in range(0, w, 100):
                    draw.line([(gx, 0), (gx, h)], fill=(22, 32, 50, 70), width=1)
                for gy in range(0, h, 100):
                    draw.line([(0, gy), (w, gy)], fill=(22, 32, 50, 70), width=1)

                # Studio Top Header
                draw.rectangle([60, 40, w - 60, 120], fill=(15, 23, 42, 220), outline=(56, 189, 248, 120), width=2)
                draw.text((90, 52), f"🎙️ TECH DEBATE 2026 • PODCAST ĐỐI THOẠI ĐA GÓC NHÌN", fill=(56, 189, 248))
                draw.text((90, 85), f"CHỦ ĐỀ: {topic.upper()}", fill=(255, 255, 255))

                # Live Recording Badge
                draw.ellipse([w - 180, 68, w - 164, 84], fill=(239, 68, 68))
                draw.text((w - 150, 68), "ON AIR", fill=(239, 68, 68))

                # 3-Panel Studio Layout:
                # 1. Left: Tuấn Anh (Visionary)
                # 2. Right: Hoàng Đặng (Skeptic)
                # 3. Center Bottom: Huệ (Host)

                panel_y = 150
                panel_w = 540
                panel_h = 460

                # Left Speaker: Tuấn Anh
                is_tuan_active = "tuấn anh" in speaker_name.lower() or "visionary" in speaker_role.lower()
                left_x = 80
                left_border = (0, 240, 255) if is_tuan_active else (51, 65, 85)
                left_bg = (15, 23, 42, 250) if is_tuan_active else (15, 23, 42, 180)
                draw.rectangle([left_x, panel_y, left_x + panel_w, panel_y + panel_h], fill=left_bg, outline=left_border, width=3 if is_tuan_active else 1)
                draw.rectangle([left_x + 20, panel_y + 20, left_x + 200, panel_y + 55], fill=(30, 58, 138, 220))
                draw.text((left_x + 30, panel_y + 28), "PHE ỦNG HỘ • VISIONARY", fill=(147, 197, 253))
                draw.text((left_x + 30, panel_y + 80), "TUẤN ANH", fill=(255, 255, 255))
                draw.text((left_x + 30, panel_y + 120), "• Tự hành 100% qua Telegram / IDE\n• Đột phá năng suất Vibe Coding 10x\n• Tự động kiểm thử & DevOps 24/7", fill=(203, 213, 225))

                # Right Speaker: Hoàng Đặng
                is_hoang_active = "hoàng" in speaker_name.lower() or "skeptic" in speaker_role.lower()
                right_x = w - 80 - panel_w
                right_border = (244, 63, 94) if is_hoang_active else (51, 65, 85)
                right_bg = (15, 23, 42, 250) if is_hoang_active else (15, 23, 42, 180)
                draw.rectangle([right_x, panel_y, right_x + panel_w, panel_y + panel_h], fill=right_bg, outline=right_border, width=3 if is_hoang_active else 1)
                draw.rectangle([right_x + 20, panel_y + 20, right_x + 220, panel_y + 55], fill=(136, 19, 55, 220))
                draw.text((right_x + 30, panel_y + 28), "PHE BẢO MẬT • SKEPTIC", fill=(254, 205, 211))
                draw.text((right_x + 30, panel_y + 80), "HOÀNG ĐẶNG", fill=(255, 255, 255))
                draw.text((right_x + 30, panel_y + 120), "• Rủi ro rò rỉ Secret Vault & API\n• Lỗ hổng Prompt Injection tiềm ẩn\n• Bắt buộc cô lập Sovereign Sandbox", fill=(203, 213, 225))

                # Center Host Card: Huệ
                is_hue_active = "huệ" in speaker_name.lower() or "host" in speaker_role.lower()
                center_x = (w - 480) // 2
                center_y = panel_y + 20
                center_border = (168, 85, 247) if is_hue_active else (51, 65, 85)
                draw.rectangle([center_x, center_y, center_x + 480, center_y + 420], fill=(15, 23, 42, 230), outline=center_border, width=3 if is_hue_active else 1)
                draw.rectangle([center_x + 20, center_y + 20, center_x + 180, center_y + 55], fill=(88, 28, 135, 220))
                draw.text((center_x + 30, center_y + 28), "HOST • MODERATOR", fill=(233, 213, 255))
                draw.text((center_x + 30, center_y + 80), "HUỆ KỶ NGUYÊN", fill=(255, 255, 255))
                draw.text((center_x + 30, center_y + 120), "• Điều phối tranh luận\n• Phân tích góc nhìn đa chiều\n• Đúc kết chuẩn mực 2026", fill=(203, 213, 225))

                # Active Speaker Waveform Spectrum
                if is_tuan_active:
                    spec_x = left_x + 30
                    spec_y = panel_y + panel_h - 60
                    for bi in range(24):
                        bh = int(10 + 40 * abs(math.sin(t * 8 + bi * 0.4)))
                        draw.rectangle([spec_x + bi * 18, spec_y - bh, spec_x + bi * 18 + 10, spec_y], fill=(0, 240, 255))
                elif is_hoang_active:
                    spec_x = right_x + 30
                    spec_y = panel_y + panel_h - 60
                    for bi in range(24):
                        bh = int(10 + 40 * abs(math.sin(t * 8 + bi * 0.4)))
                        draw.rectangle([spec_x + bi * 18, spec_y - bh, spec_x + bi * 18 + 10, spec_y], fill=(244, 63, 94))
                elif is_hue_active:
                    spec_x = center_x + 30
                    spec_y = center_y + 420 - 60
                    for bi in range(20):
                        bh = int(10 + 40 * abs(math.sin(t * 8 + bi * 0.4)))
                        draw.rectangle([spec_x + bi * 18, spec_y - bh, spec_x + bi * 18 + 10, spec_y], fill=(168, 85, 247))

                # Bottom Dialogue & Key Point Box (Cinematic Glassmorphism Subtitle)
                sub_y = h - 390
                draw.rectangle([80, sub_y, w - 80, h - 60], fill=(8, 14, 28, 245), outline=(56, 189, 248, 180), width=2)
                
                # Active Speaker Tag
                speaker_badge_color = (0, 240, 255) if is_tuan_active else ((244, 63, 94) if is_hoang_active else (168, 85, 247))
                draw.rectangle([110, sub_y + 20, 340, sub_y + 60], fill=(15, 23, 42), outline=speaker_badge_color, width=2)
                draw.text((125, sub_y + 28), f"🗣️ {speaker_name.upper()} ({speaker_role})", fill=speaker_badge_color)

                # Key Point highlight
                draw.text((370, sub_y + 30), f"📌 Luận điểm: {key_point}", fill=(250, 204, 21))

                # Spoken Text Subtitle (wrapped)
                text_preview = speech_text
                draw.text((110, sub_y + 85), text_preview[:110], fill=(255, 255, 255))
                if len(text_preview) > 110:
                    draw.text((110, sub_y + 130), text_preview[110:220], fill=(241, 245, 249))
                if len(text_preview) > 220:
                    draw.text((110, sub_y + 175), text_preview[220:330], fill=(203, 213, 225))

                frame_file = temp_dir / f"debate_frame_{f:05d}.png"
                img.save(frame_file, "PNG")

            # 1. Compile video frames
            cmd_frames = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(temp_dir / "debate_frame_%05d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                str(temp_video)
            ]
            subprocess.run(cmd_frames, capture_output=True, check=True)

            # 2. Multiplex Audio Voiceover
            cmd_mux = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
            res_mux = subprocess.run(cmd_mux, capture_output=True, text=True)
            return res_mux.returncode == 0 and output_path.exists()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if temp_video.exists():
                temp_video.unlink()



def main():
    parser = argparse.ArgumentParser(description="Video Motion Studio CLI")
    subparsers = parser.add_subparsers(dest="command", help="Studio commands")

    # Command: infographic
    p_info = subparsers.add_parser("infographic", help="Generate tech infographic image")
    p_info.add_argument("--title", default="Autonomous AI Agent Architecture", help="Infographic title")
    p_info.add_argument("--subtitle", default="Zero-Trust Sovereign Systems", help="Infographic subtitle")
    p_info.add_argument("--nodes", default="", help="Comma-separated node titles")
    p_info.add_argument("--output", required=True, help="Output PNG path")
    p_info.add_argument("--aspect", default="16:9", help="16:9 or 9:16")

    # Command: svg-anim
    p_svg = subparsers.add_parser("svg-anim", help="Generate SVG vector motion animation")
    p_svg.add_argument("--type", default="architecture-flow", help="architecture-flow, security-shield, cyber-hud, neural-network, vibe-coding, pulsing-network")
    p_svg.add_argument("--duration", type=int, default=5, help="Duration in seconds")
    p_svg.add_argument("--title", help="Optional title banner")
    p_svg.add_argument("--output", required=True, help="Output MP4 path")

    # Command: render-scene
    p_scene = subparsers.add_parser("render-scene", help="Render camera motion scene")
    p_scene.add_argument("--image", required=True, help="Input image file")
    p_scene.add_argument("--audio", required=True, help="Input audio voiceover file")
    p_scene.add_argument("--effect", default="zoom-in", help="zoom-in, zoom-out, pan-right, static")
    p_scene.add_argument("--output", required=True, help="Output MP4 file")

    args = parser.parse_args()
    studio = VideoMotionStudio()

    if args.command == "infographic":
        node_list = []
        if args.nodes:
            for item in args.nodes.split(","):
                node_list.append({"title": item.strip(), "desc": f"Optimized {item.strip()} subsystem", "badge": "ACTIVE"})
        ok = studio.generate_tech_infographic(args.title, args.subtitle, node_list, Path(args.output), aspect=args.aspect)
        print(f"[✓] Infographic generated: {args.output}" if ok else "[!] Infographic generation failed")

    elif args.command == "svg-anim":
        ok = studio.generate_svg_animation(args.type, args.duration, Path(args.output), title=args.title)
        print(f"[✓] SVG Animation generated: {args.output}" if ok else "[!] SVG Animation failed")

    elif args.command == "render-scene":
        ok = studio.apply_camera_motion_and_render(Path(args.image), Path(args.audio), Path(args.output), effect=args.effect)
        print(f"[✓] Scene rendered with motion: {args.output}" if ok else "[!] Scene rendering failed")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
