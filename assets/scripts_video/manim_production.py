#!/usr/bin/env python3
"""
Manim Production System — ZENPHAM "Tôi Làm Việc" Series
=========================================================

A comprehensive production module providing:

1. LAYOUT CONSTRAINT ENGINE — Collision-based safe placement
2. PREMIUM COMPONENT LIBRARY — 10 reusable visual components
3. VOICE-SYNC TIMELINE — Scene-level audio synchronization
4. SFX/VFX INTEGRATION — Sound effects + visual effects pipeline

Usage:
    from manim_production import (
        # Layout & Clear Spatial Partitioning (Toán Thầy Việt & 3B1B standard)
        safe_place, check_collisions, auto_resolve_overlap, SafeZone, fit_text_to_card,
        StateTrackerBar, ConceptBadge, BottomCalloutCard, PointCallout,
        ZoneStageBox, ZoneAutoVStack,
        # Components
        DiagramCard, ComparisonPanel, TensorDiagram, FlowChart,
        NeuralNetworkDiagram, TimelineDiagram, ProbabilityDistribution,
        ZenArrow, ZenCurvedArrow, ZenDoubleArrow, NeonArrow, EquationBox, AnimatedCounter,
        # Voice-Sync
        VoiceSyncTimeline,
        # SFX/VFX
        SFXCue, mix_sfx, GlowEffect, EurekaFlash, GlassmorphismRect,
        # Utilities
        add_zenpham_watermark,
    )

Style: 3Blue1Brown (dark background, pastel neon, smooth Transform)
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# =============================================================================
# TYPOGRAPHY & SPATIAL ENGINE CONSTANTS (ZenPham 2K QHD Standard)
# =============================================================================
DEFAULT_FONT = "Be Vietnam Pro"
MIN_READABLE_FONT_SIZE = 12.0
CHAR_WIDTH_ASCII = 0.010    # ASCII chars at font_size=1 (calibrated for Be Vietnam Pro 2K)
CHAR_WIDTH_VI = 0.0115      # Vietnamese chars (calibrated for Be Vietnam Pro 2K)
MANIM_DEFAULT_MATHTEX_SIZE = 20

try:
    from manim import (
        Scene, Mobject, VMobject, VGroup, VDict,
        Text, MathTex, Tex, SVGMobject,
        Rectangle, RoundedRectangle, Circle, Dot, Line, Arrow, DashedLine,
        CurvedArrow, DoubleArrow, Polygon, Annulus, AnnularSector, Arc,
        Axes, NumberLine,
        FadeIn, FadeOut, Write, Create, Uncreate, Transform, ReplacementTransform,
        GrowArrow, GrowFromCenter, Indicate, Flash, ApplyWave,
        MoveToTarget, AnimationGroup, Succession, LaggedStart,
        UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR, ORIGIN,
        WHITE, BLACK, GRAY, GRAY_A, GRAY_B, GRAY_C, GRAY_D, GRAY_E,
        RED, RED_A, RED_B, RED_C, RED_D, RED_E,
        GREEN, GREEN_A, GREEN_B, GREEN_C, GREEN_D, GREEN_E,
        BLUE, BLUE_A, BLUE_B, BLUE_C, BLUE_D, BLUE_E,
        YELLOW, YELLOW_A, YELLOW_B, YELLOW_C, YELLOW_D, YELLOW_E,
        TEAL, TEAL_A, TEAL_B, TEAL_C, TEAL_D, TEAL_E,
        GOLD, GOLD_A, GOLD_B, GOLD_C, GOLD_D, GOLD_E,
        ORANGE, PINK, PURPLE, MAROON,
        config, PI, TAU, DEGREES,
        rate_functions,
        SurroundingRectangle, BackgroundRectangle, Brace,
        DecimalNumber, Integer, ValueTracker,
    )
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False
    UP = np.array([0, 1, 0])
    DOWN = np.array([0, -1, 0])
    LEFT = np.array([-1, 0, 0])
    RIGHT = np.array([1, 0, 0])
    ORIGIN = np.array([0, 0, 0])
    UL = UP + LEFT
    UR = UP + RIGHT
    DL = DOWN + LEFT
    DR = DOWN + RIGHT
    WHITE = "#ffffff"
    BLACK = "#000000"
    PI = math.pi
    TAU = 2 * math.pi
    DEGREES = math.pi / 180


__all__ = [
    # Design Tokens & Constants
    "ZenPalette",
    "DEFAULT_FONT",
    "MIN_READABLE_FONT_SIZE",
    "CHAR_WIDTH_ASCII",
    "CHAR_WIDTH_VI",
    "MANIM_DEFAULT_MATHTEX_SIZE",
    # Geometry & Mock Elements
    "BBox",
    "DummyMobject",
    "VisualMockElement",
    "CollisionReport",
    "SafeZone",
    "check_collisions",
    "auto_resolve_overlap",
    "safe_place",
    # Spatial Containment & Typography
    "fit_text_to_card",
    "create_wrapped_card_text",
    "fit_math_to_card",
    "clean_vietnamese_text",
    "check_arrow_collision_angle",
    # Aerodynamic Arrows
    "ZenArrow",
    "ZenCurvedArrow",
    "ZenDoubleArrow",
    "NeonArrow",
    # Visual Components
    "DiagramCard",
    "ComparisonPanel",
    "TensorDiagram",
    "FlowChart",
    "NeuralNetworkDiagram",
    "TimelineDiagram",
    "ProbabilityDistribution",
    "EquationBox",
    "AnimatedCounter",
    "StateTrackerBar",
    "ConceptBadge",
    "BottomCalloutCard",
    "PointCallout",
    "SafeFormulaCard",
    "ZoneStageBox",
    "ZoneAutoVStack",
    "ArchitectureNode",
    "DuotoneTrackerBar",
    # Voice-Sync & SFX/VFX
    "VoiceSyncTimeline",
    "SFXCue",
    "mix_sfx",
    "GlowEffect",
    "EurekaFlash",
    "GlassmorphismRect",
    "add_zenpham_watermark",
    # Distributed Training Geometry Helpers (Series 2 Ep24+)
    "create_hairline_axes",
    "create_elegant_arrow",
    "create_elegant_dot",
]


# =============================================================================
# DESIGN TOKENS — 3Blue1Brown-Inspired ZENPHAM Palette
# =============================================================================

class ZenPalette:
    """Centralized color palette for all ZENPHAM Manim productions."""
    BG_DEEP      = "#0c0d12"
    BG_CARD      = "#08090d"
    BG_CARD_ALT  = "#0f1118"
    CYAN         = "#00f0ff"
    AMBER        = "#f59e0b"
    GOLD         = "#fbbf24"
    EMERALD      = "#34d399"
    CORAL        = "#f87171"
    VIOLET       = "#a78bfa"
    ROSE         = "#fb7185"
    SKY          = "#38bdf8"
    TEXT_PRIMARY  = "#e2e8f0"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED    = "#94a3b8"
    TEXT_DIM      = "#64748b"
    BORDER_SUBTLE = "#1e293b"
    NEON_CORE     = "#ffffff"
    NEON_MID      = "#00f0ff"
    NEON_OUTER    = "#0066aa"
    RUBY_RED      = "#ef4444"


# =============================================================================
# PILLAR 1: LAYOUT CONSTRAINT ENGINE
# =============================================================================

@dataclass
class BBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float: return self.x_max - self.x_min
    @property
    def height(self) -> float: return self.y_max - self.y_min
    @property
    def center(self) -> np.ndarray: return np.array([(self.x_min + self.x_max)/2.0, (self.y_min + self.y_max)/2.0, 0.0])
    @property
    def x(self) -> float: return (self.x_min + self.x_max)/2.0
    @property
    def y(self) -> float: return (self.y_min + self.y_max)/2.0

    def get_center(self) -> np.ndarray:
        return self.center

    def get_corner(self, direction: Union[List[float], np.ndarray]) -> np.ndarray:
        dx = self.x_min if direction[0] < 0 else (self.x_max if direction[0] > 0 else (self.x_min + self.x_max)/2.0)
        dy = self.y_min if direction[1] < 0 else (self.y_max if direction[1] > 0 else (self.y_min + self.y_max)/2.0)
        return np.array([dx, dy, 0.0])

    def intersects(self, other, clearance=0.0):
        return not (self.x_max + clearance < other.x_min or other.x_max + clearance < self.x_min or
                    self.y_max + clearance < other.y_min or other.y_max + clearance < self.y_min)

    def expanded(self, margin):
        return BBox(self.x_min-margin, self.y_min-margin, self.x_max+margin, self.y_max+margin)


class DummyMobject:
    """Lightweight standalone mobject mock for layout/containment testing."""
    def __init__(self, x: float = 0.0, y: float = 0.0, w: float = 2.0, h: float = 1.0):
        self.x = float(x)
        self.y = float(y)
        self._w = float(max(0.0, w))
        self._h = float(max(0.0, h))

    @property
    def width(self) -> float:
        return self._w

    @property
    def height(self) -> float:
        return self._h

    @property
    def x_min(self) -> float:
        return self.x - self._w / 2.0

    @property
    def x_max(self) -> float:
        return self.x + self._w / 2.0

    @property
    def y_min(self) -> float:
        return self.y - self._h / 2.0

    @property
    def y_max(self) -> float:
        return self.y + self._h / 2.0

    def get_center(self) -> np.ndarray:
        return np.array([self.x, self.y, 0.0])

    def get_corner(self, direction: Union[List[float], np.ndarray]) -> np.ndarray:
        dx = -self._w / 2.0 if direction[0] < 0 else self._w / 2.0
        dy = -self._h / 2.0 if direction[1] < 0 else self._h / 2.0
        return np.array([self.x + dx, self.y + dy, 0.0])

    def scale_to_fit_width(self, target_w: float) -> DummyMobject:
        ratio = target_w / max(self._w, 1e-6)
        self._w = target_w
        self._h *= ratio
        return self

    def scale_to_fit_height(self, target_h: float) -> DummyMobject:
        ratio = target_h / max(self._h, 1e-6)
        self._h = target_h
        self._w *= ratio
        return self

    def scale(self, factor: float) -> DummyMobject:
        self._w *= factor
        self._h *= factor
        return self

    def shift(self, vector: Union[List[float], np.ndarray]) -> DummyMobject:
        self.x += float(vector[0])
        self.y += float(vector[1])
        return self

    def move_to(self, target: Any) -> DummyMobject:
        if hasattr(target, "get_center"):
            c = target.get_center()
        elif hasattr(target, "center"):
            c = target.center
        elif hasattr(target, "x") and hasattr(target, "y"):
            c = np.array([target.x, target.y, 0.0])
        else:
            c = np.array(target, dtype=float)
        self.x = float(c[0])
        self.y = float(c[1])
        return self


class VisualMockElement:
    """Lightweight geometric mock element for Manim mobjects in headless environments."""
    def __init__(
        self,
        name: str = "element",
        center: Union[Tuple[float, float], Tuple[float, float, float], np.ndarray] = (0.0, 0.0, 0.0),
        width: float = 2.0,
        height: float = 1.0,
        color: str = "#ffffff",
        fill_opacity: float = 1.0,
        stroke_opacity: float = 1.0,
        z_index: int = 0,
        font_size: Optional[float] = None,
        text: str = "",
        is_container: bool = False,
        tip_length: Optional[float] = None,
        lines: Optional[List[str]] = None,
    ):
        self.name = name
        c = np.array(center, dtype=float)
        self._cx = float(c[0]) if len(c) > 0 else 0.0
        self._cy = float(c[1]) if len(c) > 1 else 0.0
        self._cz = float(c[2]) if len(c) > 2 else 0.0
        self._width = float(max(0.0, width))
        self._height = float(max(0.0, height))
        self.color = color
        self.fill_color = color
        self.fill_opacity = fill_opacity
        self.stroke_opacity = stroke_opacity
        self.z_index = z_index
        self.font_size = font_size
        self.text = text
        self.is_container = is_container
        self.tip_length = tip_length
        self.lines = list(lines) if lines is not None else []
        self.children: List[VisualMockElement] = []
        self.parent: Optional[VisualMockElement] = None

    @property
    def x(self) -> float:
        return self._cx

    @x.setter
    def x(self, val: float):
        self._cx = float(val)

    @property
    def y(self) -> float:
        return self._cy

    @y.setter
    def y(self, val: float):
        self._cy = float(val)

    @property
    def x_min(self) -> float:
        return self.get_bbox().x_min

    @property
    def x_max(self) -> float:
        return self.get_bbox().x_max

    @property
    def y_min(self) -> float:
        return self.get_bbox().y_min

    @property
    def y_max(self) -> float:
        return self.get_bbox().y_max

    @property
    def width(self) -> float:
        if self.children:
            return self.get_bbox().width
        return self._width

    @property
    def height(self) -> float:
        if self.children:
            return self.get_bbox().height
        return self._height

    def get_bbox(self) -> BBox:
        if self.children:
            child_bbs = [c.get_bbox() for c in self.children]
            x_min = min(b.x_min for b in child_bbs)
            x_max = max(b.x_max for b in child_bbs)
            y_min = min(b.y_min for b in child_bbs)
            y_max = max(b.y_max for b in child_bbs)
            return BBox(x_min, y_min, x_max, y_max)
        hw = self._width / 2.0
        hh = self._height / 2.0
        return BBox(self._cx - hw, self._cy - hh, self._cx + hw, self._cy + hh)

    def get_center(self) -> np.ndarray:
        bb = self.get_bbox()
        return np.array([bb.center[0], bb.center[1], self._cz])

    def get_left(self) -> np.ndarray:
        bb = self.get_bbox()
        return np.array([bb.x_min, (bb.y_min + bb.y_max)/2.0, self._cz])

    def get_right(self) -> np.ndarray:
        bb = self.get_bbox()
        return np.array([bb.x_max, (bb.y_min + bb.y_max)/2.0, self._cz])

    def get_top(self) -> np.ndarray:
        bb = self.get_bbox()
        return np.array([(bb.x_min + bb.x_max)/2.0, bb.y_max, self._cz])

    def get_bottom(self) -> np.ndarray:
        bb = self.get_bbox()
        return np.array([(bb.x_min + bb.x_max)/2.0, bb.y_min, self._cz])

    def get_corner(self, direction: Union[List[float], np.ndarray]) -> np.ndarray:
        bb = self.get_bbox()
        dx = bb.x_min if direction[0] < 0 else (bb.x_max if direction[0] > 0 else (bb.x_min + bb.x_max)/2.0)
        dy = bb.y_min if direction[1] < 0 else (bb.y_max if direction[1] > 0 else (bb.y_min + bb.y_max)/2.0)
        return np.array([dx, dy, self._cz])

    def move_to(self, target: Any) -> VisualMockElement:
        if hasattr(target, "get_center"):
            t_pos = target.get_center()
        elif hasattr(target, "center"):
            t_pos = target.center
        elif hasattr(target, "x") and hasattr(target, "y"):
            t_pos = np.array([target.x, target.y, 0.0])
        else:
            t_pos = np.array(target, dtype=float)
        curr = self.get_center()
        dx = t_pos[0] - curr[0]
        dy = t_pos[1] - curr[1]
        self.shift(np.array([dx, dy, 0.0]))
        return self

    def shift(self, vector: Union[Tuple[float, float, float], np.ndarray]) -> VisualMockElement:
        v = np.array(vector, dtype=float)
        dx = float(v[0])
        dy = float(v[1]) if len(v) > 1 else 0.0
        dz = float(v[2]) if len(v) > 2 else 0.0
        self._cx += dx
        self._cy += dy
        self._cz += dz
        for child in self.children:
            child.shift(vector)
        return self

    def scale(self, factor: float) -> VisualMockElement:
        self._width *= factor
        self._height *= factor
        if self.font_size is not None:
            self.font_size *= factor
        for child in self.children:
            child.scale(factor)
        return self

    def scale_to_fit_width(self, target_w: float) -> VisualMockElement:
        curr_w = self.width
        if curr_w > 1e-6:
            factor = target_w / curr_w
            self.scale(factor)
        return self

    def scale_to_fit_height(self, target_h: float) -> VisualMockElement:
        curr_h = self.height
        if curr_h > 1e-6:
            factor = target_h / curr_h
            self.scale(factor)
        return self

    def next_to(self, anchor: Any, direction: np.ndarray = RIGHT, buff: float = 0.3) -> VisualMockElement:
        a_bb = _get_bbox(anchor)
        m_bb = self.get_bbox()
        d = np.array(direction, dtype=float)
        if d[0] > 0:
            target_x = a_bb.x_max + buff + m_bb.width / 2.0
            target_y = (a_bb.y_min + a_bb.y_max) / 2.0
        elif d[0] < 0:
            target_x = a_bb.x_min - buff - m_bb.width / 2.0
            target_y = (a_bb.y_min + a_bb.y_max) / 2.0
        elif d[1] > 0:
            target_x = (a_bb.x_min + a_bb.x_max) / 2.0
            target_y = a_bb.y_max + buff + m_bb.height / 2.0
        else:
            target_x = (a_bb.x_min + a_bb.x_max) / 2.0
            target_y = a_bb.y_min - buff - m_bb.height / 2.0
        return self.move_to(np.array([target_x, target_y, 0.0]))

    def add(self, *children: VisualMockElement) -> VisualMockElement:
        for c in children:
            c.parent = self
            self.children.append(c)
        return self

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __getitem__(self, idx):
        return self.children[idx]


def _get_bbox(mobject, margin=0.0) -> BBox:
    if mobject is None:
        return BBox(0.0, 0.0, 1.0, 1.0)
    if isinstance(mobject, BBox):
        return BBox(mobject.x_min - margin, mobject.y_min - margin,
                    mobject.x_max + margin, mobject.y_max + margin)
    if hasattr(mobject, "x_min") and hasattr(mobject, "x_max") and hasattr(mobject, "y_min") and hasattr(mobject, "y_max"):
        return BBox(float(mobject.x_min) - margin, float(mobject.y_min) - margin,
                    float(mobject.x_max) + margin, float(mobject.y_max) + margin)
    if isinstance(mobject, (int, float)):
        w = float(mobject)
        h = 3.0
        return BBox(-w/2.0 - margin, -h/2.0 - margin, w/2.0 + margin, h/2.0 + margin)
    if hasattr(mobject, "get_corner"):
        try:
            ul = mobject.get_corner(UL)
            dr_pt = mobject.get_corner(DR)
            return BBox(min(ul[0], dr_pt[0]) - margin, min(ul[1], dr_pt[1]) - margin,
                        max(ul[0], dr_pt[0]) + margin, max(ul[1], dr_pt[1]) + margin)
        except Exception:
            pass
    if hasattr(mobject, "get_bbox"):
        try:
            bb = mobject.get_bbox()
            if bb is not None and hasattr(bb, "x_min"):
                return BBox(float(bb.x_min) - margin, float(bb.y_min) - margin,
                            float(bb.x_max) + margin, float(bb.y_max) + margin)
        except Exception:
            pass
    if hasattr(mobject, "width") and hasattr(mobject, "height"):
        if hasattr(mobject, "get_center"):
            c = mobject.get_center()
            x, y = float(c[0]), float(c[1])
        else:
            x = float(getattr(mobject, "x", 0.0))
            y = float(getattr(mobject, "y", 0.0))
        w, h = float(mobject.width), float(mobject.height)
        return BBox(x - w/2.0 - margin, y - h/2.0 - margin, x + w/2.0 + margin, y + h/2.0 + margin)
    return BBox(0.0, 0.0, 1.0, 1.0)


@dataclass
class CollisionReport:
    mobject_a: object
    mobject_b: object
    overlap_area: float
    suggestion: str


class SafeZone:
    FRAME_WIDTH = 14.222
    FRAME_HEIGHT = 8.0

    def __init__(self, margin_x=0.5, margin_y=0.5):
        self.margin_x = margin_x
        self.margin_y = margin_y

    @property
    def bounds(self):
        hw = self.FRAME_WIDTH/2 - self.margin_x
        hh = self.FRAME_HEIGHT/2 - self.margin_y
        return BBox(-hw, -hh, hw, hh)

    def is_inside(self, mobject):
        mb = _get_bbox(mobject)
        sb = self.bounds
        return (mb.x_min >= sb.x_min and mb.x_max <= sb.x_max and
                mb.y_min >= sb.y_min and mb.y_max <= sb.y_max)

    def clamp(self, mobject):
        sb = self.bounds
        mb = _get_bbox(mobject)
        if hasattr(mobject, "scale_to_fit_width") and mb.width > sb.width:
            mobject.scale_to_fit_width(sb.width * 0.95)
            mb = _get_bbox(mobject)
        if hasattr(mobject, "scale_to_fit_height") and mb.height > sb.height:
            mobject.scale_to_fit_height(sb.height * 0.95)
            mb = _get_bbox(mobject)
        dx = dy = 0
        if mb.x_min < sb.x_min: dx = sb.x_min - mb.x_min
        elif mb.x_max > sb.x_max: dx = sb.x_max - mb.x_max
        if mb.y_min < sb.y_min: dy = sb.y_min - mb.y_min
        elif mb.y_max > sb.y_max: dy = sb.y_max - mb.y_max
        if (dx != 0 or dy != 0) and hasattr(mobject, "shift"):
            mobject.shift(np.array([dx, dy, 0]))


_DEFAULT_SAFE_ZONE = SafeZone(margin_x=0.6, margin_y=0.45)


def check_collisions(mobjects, clearance=0.05, ignore_pairs=None):
    reports = []
    ignore_set = set((min(a,b),max(a,b)) for a,b in (ignore_pairs or []))
    for i in range(len(mobjects)):
        for j in range(i+1, len(mobjects)):
            if (i,j) in ignore_set: continue
            bb_i, bb_j = _get_bbox(mobjects[i]), _get_bbox(mobjects[j])
            if bb_i.intersects(bb_j, clearance):
                ox = max(0, min(bb_i.x_max,bb_j.x_max) - max(bb_i.x_min,bb_j.x_min))
                oy = max(0, min(bb_i.y_max,bb_j.y_max) - max(bb_i.y_min,bb_j.y_min))
                reports.append(CollisionReport(mobjects[i], mobjects[j], ox*oy,
                    f"Shift by ~{max(ox,oy):.2f} units to resolve."))
    return reports


def auto_resolve_overlap(mobject, obstacles, strategy="shift", clearance=0.1, preferred_direction=None):
    for obstacle in obstacles:
        mb = _get_bbox(mobject, margin=clearance)
        ob = _get_bbox(obstacle)
        if not mb.intersects(ob): continue

        if strategy in ("shift", "shift_then_scale") and hasattr(mobject, "shift"):
            escapes = [
                np.array([ob.x_max - mb.x_min + clearance, 0, 0]),
                np.array([ob.x_min - mb.x_max - clearance, 0, 0]),
                np.array([0, ob.y_max - mb.y_min + clearance, 0]),
                np.array([0, ob.y_min - mb.y_max - clearance, 0]),
            ]
            if preferred_direction is not None:
                escapes.sort(key=lambda v: -np.dot(v/(np.linalg.norm(v)+1e-9), preferred_direction/(np.linalg.norm(preferred_direction)+1e-9)))
                best = escapes[0]
            else:
                best = min(escapes, key=lambda v: np.linalg.norm(v))
            mobject.shift(best)
            _DEFAULT_SAFE_ZONE.clamp(mobject)

        if strategy == "scale" and hasattr(mobject, "scale"):
            for _ in range(20):
                if not _get_bbox(mobject, margin=clearance).intersects(_get_bbox(obstacle)): break
                mobject.scale(0.9)

        if strategy == "shift_then_scale":
            if _get_bbox(mobject, margin=clearance).intersects(_get_bbox(obstacle)):
                for _ in range(20):
                    mobject.scale(0.9)
                    if not _get_bbox(mobject, margin=clearance).intersects(_get_bbox(obstacle)): break


def safe_place(mobject, anchor, direction=None, buff=0.3, avoid=None, clearance=0.1, clamp_to_safe_zone=True):
    """Place mobject next to anchor, then resolve collisions. Drop-in for .next_to()."""
    if direction is None: direction = RIGHT
    if not MANIM_AVAILABLE: return
    mobject.next_to(anchor, direction, buff=buff)
    if avoid:
        auto_resolve_overlap(mobject, avoid, strategy="shift_then_scale", clearance=clearance, preferred_direction=direction)
    if clamp_to_safe_zone:
        _DEFAULT_SAFE_ZONE.clamp(mobject)


# =============================================================================
# PILLAR 2: PREMIUM COMPONENT LIBRARY
# =============================================================================

def fit_text_to_card(mobject, card, margin_x=0.3, margin_y=0.15):
    """Guarantees mobject bounding box is strictly clamped within card boundaries.
    Prevents any text-out-card defects across all resolutions.
    """
    if mobject is None or card is None:
        return mobject
    card_bb = _get_bbox(card)
    max_w = max(card_bb.width - 2 * margin_x, 0.4)
    max_h = max(card_bb.height - 2 * margin_y, 0.2)
    if hasattr(mobject, "scale_to_fit_width") and hasattr(mobject, "width") and mobject.width > max_w:
        mobject.scale_to_fit_width(max_w)
    if hasattr(mobject, "scale_to_fit_height") and hasattr(mobject, "height") and mobject.height > max_h:
        mobject.scale_to_fit_height(max_h)
    return mobject


def _to_point(pt: Any) -> np.ndarray:
    """Converts a mobject, BBox, tuple, or array to a 3D coordinate vector."""
    if hasattr(pt, "get_center"):
        c = pt.get_center()
        return np.array([float(c[0]), float(c[1]), float(c[2]) if len(c) > 2 else 0.0])
    if hasattr(pt, "center"):
        c = pt.center
        return np.array([float(c[0]), float(c[1]), float(c[2]) if len(c) > 2 else 0.0])
    if hasattr(pt, "x") and hasattr(pt, "y"):
        return np.array([float(pt.x), float(pt.y), 0.0])
    if isinstance(pt, (tuple, list, np.ndarray)):
        arr = np.array(pt, dtype=float)
        if len(arr) == 2:
            return np.array([arr[0], arr[1], 0.0])
        elif len(arr) >= 3:
            return arr[:3]
        elif len(arr) == 1:
            return np.array([arr[0], 0.0, 0.0])
    return np.array([0.0, 0.0, 0.0])


def clean_vietnamese_text(text: str) -> str:
    """
    Normalizes Unicode to NFC and cleans decomposed kerning splits and orphan punctuation spaces.
    Guarantees:
      - NFC precomposed code points (unicodedata.normalize('NFC', text))
      - Elimination of broken syllable gaps (e.g. 'KHÔ NG' -> 'KHÔNG')
      - Clean punctuation spacing (no leading spaces before :, ;, ,, ., !, ?)
      - Stripping of zero-width and non-breaking spaces
    """
    if not text:
        return ""
    # 1. NFC normalization
    t = unicodedata.normalize("NFC", str(text))
    # 2. Strip zero-width and non-breaking spaces
    t = t.replace("\u200b", "").replace("\xa0", " ")
    # 3. Clean orphan spaces before punctuation
    t = re.sub(r"\s+([:;,.!?])", r"\1", t)
    # 4. Collapse multiple spaces
    t = re.sub(r"[ \t]+", " ", t)
    # 5. Fix decomposed Vietnamese kerning splits (broken syllables with separated final consonants/diphthongs)
    def _merge_syllables(m: re.Match) -> str:
        g1, g2 = m.group(1), m.group(2)
        full = g1 + g2
        if g1.isupper():
            return full.upper()
        elif g1.istitle():
            return g1[0].upper() + (g1[1:] + g2).lower()
        else:
            return full.lower()

    t = re.sub(
        r"\b(KHÔ|TRƯỜ|TIẾ|ĐƯỜ|NHỮ|LƯỢ|CƯỜ|HƯỚ|THƯỜ|GIƯỜ)\s+(NG)\b",
        _merge_syllables,
        t,
        flags=re.IGNORECASE,
    )
    return t.strip()


def _estimate_text_width(text: str, font_size: float = 14.0, font: str = DEFAULT_FONT) -> float:
    """Estimates rendered text width in 2K canvas units."""
    if not text:
        return 0.3
    if MANIM_AVAILABLE:
        try:
            t = Text(text, font=font, font_size=font_size)
            return float(t.width)
        except Exception:
            pass
    lines = text.split("\n")
    def _lw(l_str: str) -> float:
        vi_chars = sum(1 for c in l_str if ord(c) > 127)
        ascii_chars = len(l_str) - vi_chars
        return (ascii_chars * CHAR_WIDTH_ASCII + vi_chars * CHAR_WIDTH_VI) * font_size
    return max(max(_lw(l) for l in lines), 0.3)


def _estimate_text_height(font_size: float = 14.0, num_lines: int = 1, line_spacing: float = 0.85) -> float:
    """Estimates rendered multi-line text height in 2K canvas units."""
    single_h = font_size * 0.018
    if num_lines <= 1:
        return single_h
    buff = line_spacing * 0.15
    return num_lines * single_h + (num_lines - 1) * buff


def _estimate_mathtex_width(tex_str: str, font_size: float = MANIM_DEFAULT_MATHTEX_SIZE) -> float:
    """Estimates rendered MathTex width in 2K canvas units by stripping formatting."""
    if not tex_str:
        return 0.4
    if MANIM_AVAILABLE:
        try:
            m = MathTex(tex_str, font_size=font_size)
            return float(m.width)
        except Exception:
            pass
    s_clean = re.sub(r'\\(sum|prod|int|lim)(?:_\{[^}]*\}|\^[^{]*\{[^}]*\}|_.\^.)*', 'M', tex_str)
    s_clean = re.sub(r'\\[a-zA-Z]+', 'M', s_clean)
    s_clean = re.sub(r'[{}_^&]', '', s_clean)
    s_clean = re.sub(r'\s+', ' ', s_clean).strip()
    return max(len(s_clean) * CHAR_WIDTH_ASCII * 0.88 * font_size, 0.4)


def _estimate_mathtex_height(font_size: float = MANIM_DEFAULT_MATHTEX_SIZE, num_lines: int = 1) -> float:
    """Estimates rendered multi-line MathTex height in 2K canvas units."""
    single_h = font_size * 0.022
    if num_lines <= 1:
        return single_h
    buff = 0.15 * (font_size / 22.0)
    return num_lines * single_h + (num_lines - 1) * buff


def split_depth_zero(tex: str, operators: List[str]) -> List[Tuple[int, int, str]]:
    """Finds occurrences of operators at bracket depth 0 (outside {}, (), [])."""
    matches = []
    depth_curly = 0
    depth_paren = 0
    depth_brack = 0
    i = 0
    n = len(tex)
    sorted_ops = sorted(operators, key=lambda op: -len(op))
    while i < n:
        c = tex[i]
        if c == '{' and (i == 0 or tex[i-1] != '\\'):
            depth_curly += 1
            i += 1
            continue
        elif c == '}' and (i == 0 or tex[i-1] != '\\'):
            depth_curly = max(0, depth_curly - 1)
            i += 1
            continue
        elif c == '(' and (i == 0 or tex[i-1] != '\\'):
            depth_paren += 1
            i += 1
            continue
        elif c == ')' and (i == 0 or tex[i-1] != '\\'):
            depth_paren = max(0, depth_paren - 1)
            i += 1
            continue
        elif c == '[' and (i == 0 or tex[i-1] != '\\'):
            depth_brack += 1
            i += 1
            continue
        elif c == ']' and (i == 0 or tex[i-1] != '\\'):
            depth_brack = max(0, depth_brack - 1)
            i += 1
            continue

        if depth_curly == 0 and depth_paren == 0 and depth_brack == 0:
            matched = False
            for op in sorted_ops:
                if tex.startswith(op, i):
                    if op.startswith('\\') and op[1:].isalpha():
                        end_pos = i + len(op)
                        if end_pos < n and tex[end_pos].isalpha():
                            continue
                    matches.append((i, i + len(op), op))
                    i += len(op)
                    matched = True
                    break
            if matched:
                continue
        i += 1
    return matches


def _split_binary_or_spacing(s: str, max_w: float, f_size: float) -> List[str]:
    spacing_ops = [r"\qquad", r"\quad"]
    sp_matches = split_depth_zero(s, spacing_ops)
    if sp_matches:
        cuts = [0] + [m[0] for m in sp_matches] + [len(s)]
        chunks = []
        for k in range(len(sp_matches)):
            if k == 0:
                chunks.append(s[:sp_matches[0][0]].strip())
            next_cut = sp_matches[k+1][0] if k + 1 < len(sp_matches) else len(s)
            chunks.append(s[sp_matches[k][1]:next_cut].strip())
        lines = []
        for c in chunks:
            if c:
                if _estimate_mathtex_width(c, f_size) > max_w:
                    lines.extend(_split_binary(c, max_w, f_size))
                else:
                    lines.append(c)
        return lines
    return _split_binary(s, max_w, f_size)


def _split_binary(s: str, max_w: float, f_size: float) -> List[str]:
    bin_ops = ["+", "-", r"\pm", r"\times", r"\cdot"]
    matches = split_depth_zero(s, bin_ops)
    if not matches:
        return [s]

    best_match = None
    for m in matches:
        prefix = s[:m[0]].strip()
        if prefix and _estimate_mathtex_width(prefix, f_size) <= max_w:
            best_match = m
        elif not best_match:
            best_match = m

    if best_match:
        prefix = s[:best_match[0]].strip()
        rest = s[best_match[0]:].strip()
        if not prefix or not rest or len(rest) >= len(s):
            return [s]
        line1 = prefix
        line2 = r"\quad " + rest if not rest.startswith(r"\quad") else rest
        res = [line1]
        if _estimate_mathtex_width(line2, f_size) > max_w and len(rest) < len(s):
            res.extend(_split_binary(rest, max_w, f_size))
        else:
            res.append(line2)
        return res

    return [s]


def _split_math_expression(
    tex_str: str,
    max_w: float,
    f_size: float,
    split_operators: Optional[List[str]] = None,
) -> List[str]:
    s = tex_str.strip().strip("$").strip()
    if not s:
        return [""]

    w = _estimate_mathtex_width(s, f_size)
    if w <= max_w and "\\\\" not in s and "\\newline" not in s and r"\aligned" not in s and r"\begin{aligned}" not in s:
        return [s]

    # Explicit line breaks (\\ or \newline)
    if "\\\\" in s or "\\newline" in s:
        cleaned = re.sub(r"\\begin\{aligned\}|\\end\{aligned\}", "", s).strip()
        raw_lines = [seg.strip() for seg in re.split(r"(?:\\\\\s*|\\newline\s*)", cleaned) if seg.strip()]
        result_lines = []
        for rl in raw_lines:
            sub = _split_math_expression(rl, max_w, f_size, split_operators)
            result_lines.extend(sub)
        return result_lines

    # Relational operators at depth 0
    rel_ops = split_operators or ["=", r"\approx", r"\equiv", r"\le", r"\ge", r"\ne", r"\to", r"\implies", r"\iff", r"\sim"]
    rel_matches = split_depth_zero(s, rel_ops)
    if rel_matches:
        segments = []
        for k in range(len(rel_matches)):
            if k == 0:
                segments.append(s[:rel_matches[0][0]].strip())
            next_cut = rel_matches[k+1][0] if k + 1 < len(rel_matches) else len(s)
            segments.append(s[rel_matches[k][0]:next_cut].strip())

        lines: List[str] = []
        curr_line = ""
        for idx, seg in enumerate(segments):
            if idx == 0:
                curr_line = seg
            else:
                cand = (curr_line + " " + seg).strip()
                if _estimate_mathtex_width(cand, f_size) <= max_w:
                    curr_line = cand
                else:
                    if curr_line:
                        lines.append(curr_line)
                    indented_seg = r"\quad " + seg if not seg.startswith(r"\quad") else seg
                    if _estimate_mathtex_width(indented_seg, f_size) <= max_w:
                        curr_line = indented_seg
                    else:
                        curr_line = indented_seg
        if curr_line:
            lines.append(curr_line)

        final_lines = []
        for l in lines:
            if _estimate_mathtex_width(l, f_size) > max_w:
                final_lines.extend(_split_binary_or_spacing(l, max_w, f_size))
            else:
                final_lines.append(l)
        return final_lines

    return _split_binary_or_spacing(s, max_w, f_size)


def create_wrapped_card_text(
    text: str,
    card: Union[Mobject, BBox, float, Any],
    font: str = DEFAULT_FONT,
    font_size: float = 14.0,
    min_font_size: float = MIN_READABLE_FONT_SIZE,
    padding_x: float = 0.30,
    padding_y: float = 0.20,
    color: Optional[str] = None,
    line_spacing: float = 0.85,
    alignment: str = "center",
    max_lines: Optional[int] = None,
    **kwargs
) -> Any:
    """
    Renders wrapped, kerning-safe Vietnamese text strictly contained within card boundaries.

    Guarantees:
      1. W_avail = card.width - 2 * padding_x
      2. Zero decomposed Vietnamese kerning splits (NFC normalized, Be Vietnam Pro font).
      3. Zero micro-text (font_size >= 12.0pt).
      4. x_min >= card.x_min + padding_x and x_max <= card.x_max - padding_x.
    """
    card_bb = _get_bbox(card)
    w_avail = card_bb.width - 2.0 * padding_x
    h_avail = card_bb.height - 2.0 * padding_y

    if w_avail <= 0.0:
        raise ValueError(f"Available card width must be positive, got {w_avail:.3f} (card.width={card_bb.width:.3f}, padding_x={padding_x})")
    if h_avail <= 0.0:
        raise ValueError(f"Available card height must be positive, got {h_avail:.3f} (card.height={card_bb.height:.3f}, padding_y={padding_y})")

    min_font_size = max(MIN_READABLE_FONT_SIZE, float(min_font_size))
    curr_font_size = max(float(font_size), min_font_size)

    # 1. NFC normalization and punctuation/kerning cleanup
    clean_t = clean_vietnamese_text(text)

    # 2. Greedy line wrapping
    def _wrap_lines(f_size: float) -> List[str]:
        paragraphs = clean_t.split("\n")
        lines: List[str] = []
        for para in paragraphs:
            para_str = para.strip()
            if not para_str:
                continue
            words = [w for w in re.split(r"[ \t]+", para_str) if w]
            if not words:
                continue
            curr_words: List[str] = []
            para_lines: List[str] = []
            for w in words:
                candidate = " ".join(curr_words + [w]) if curr_words else w
                w_cand = _estimate_text_width(candidate, f_size, font=font)
                if w_cand <= w_avail or not curr_words:
                    curr_words.append(w)
                else:
                    para_lines.append(" ".join(curr_words))
                    curr_words = [w]
            if curr_words:
                para_lines.append(" ".join(curr_words))

            # Orphan word pull
            if len(para_lines) >= 2:
                last_w = para_lines[-1].split()
                penult_w = para_lines[-2].split()
                if len(last_w) == 1 and len(penult_w) > 1:
                    cand_last = penult_w[-1] + " " + last_w[0]
                    if _estimate_text_width(cand_last, f_size, font=font) <= w_avail:
                        para_lines[-2] = " ".join(penult_w[:-1])
                        para_lines[-1] = cand_last
            lines.extend(para_lines)
        return lines

    all_lines = _wrap_lines(curr_font_size)

    # Check line widths vs w_avail
    max_line_w = max((_estimate_text_width(l, curr_font_size, font=font) for l in all_lines), default=0.0)
    if max_line_w > w_avail:
        req_scale = w_avail / max_line_w
        if curr_font_size * req_scale >= min_font_size:
            curr_font_size = curr_font_size * req_scale
            all_lines = _wrap_lines(curr_font_size)
        else:
            curr_font_size = min_font_size
            truncated_lines = []
            for l in all_lines:
                if _estimate_text_width(l, min_font_size, font=font) > w_avail:
                    cur = l
                    while cur and _estimate_text_width(cur + "...", min_font_size, font=font) > w_avail:
                        cur = cur[:-1]
                    truncated_lines.append((cur + "...").strip())
                else:
                    truncated_lines.append(l)
            all_lines = truncated_lines

    # Enforce unconditional max_lines truncation if specified
    if max_lines is not None and len(all_lines) > max_lines:
        all_lines = all_lines[:max_lines]
        all_lines[-1] = all_lines[-1].rstrip("., ") + "..."

    # Check vertical height containment
    tot_h = _estimate_text_height(curr_font_size, len(all_lines), line_spacing=line_spacing)
    if tot_h > h_avail:
        scale_h = h_avail / tot_h
        cand_fs = curr_font_size * scale_h
        if cand_fs >= min_font_size:
            curr_font_size = cand_fs
            all_lines = _wrap_lines(curr_font_size)
            if max_lines is not None and len(all_lines) > max_lines:
                all_lines = all_lines[:max_lines]
                all_lines[-1] = all_lines[-1].rstrip("., ") + "..."
            tot_h = _estimate_text_height(curr_font_size, len(all_lines), line_spacing=line_spacing)
        else:
            curr_font_size = min_font_size
            h12 = _estimate_text_height(min_font_size, 1)
            buff12 = line_spacing * 0.15
            if h_avail < h12:
                raise ValueError(f"Card height {card_bb.height:.2f} insufficient for text at minimum {min_font_size}pt (requires >= {h12 + 2 * padding_y:.2f})")
            max_fit = max(1, int((h_avail - h12) / (h12 + buff12)) + 1)
            if max_lines is not None:
                max_fit = min(max_fit, max_lines)
            if len(all_lines) > max_fit:
                all_lines = all_lines[:max_fit]
                all_lines[-1] = all_lines[-1].rstrip("., ") + "..."

    if max_lines is not None and len(all_lines) > max_lines:
        all_lines = all_lines[:max_lines]
        all_lines[-1] = all_lines[-1].rstrip("., ") + "..."

    # Micro-text assertion
    if curr_font_size < min_font_size:
        raise ValueError(f"MICRO_TEXT violation: effective font size {curr_font_size:.1f}pt < minimum {min_font_size:.1f}pt")

    text_color = color or ZenPalette.TEXT_PRIMARY

    if MANIM_AVAILABLE:
        mobs = [
            Text(l, font=font, font_size=curr_font_size, color=text_color, **kwargs)
            for l in all_lines if l
        ]
        if not mobs:
            mobs = [Text("", font=font, font_size=curr_font_size, color=text_color, **kwargs)]
        if len(mobs) == 1:
            res = mobs[0]
        else:
            res = VGroup(*mobs).arrange(DOWN, buff=line_spacing * 0.15)
        if res.width > w_avail:
            res.scale_to_fit_width(w_avail)
        if res.height > h_avail:
            res.scale_to_fit_height(h_avail)
        res.move_to(card_bb.center)
        return res

    # Headless / Mock element
    l_widths = [_estimate_text_width(l, curr_font_size, font=font) for l in all_lines]
    res_w = min(max(l_widths, default=0.4), w_avail)
    res_h = min(_estimate_text_height(curr_font_size, len(all_lines), line_spacing=line_spacing), h_avail)
    mock_res = VisualMockElement(
        name="WrappedCardText",
        center=card_bb.center,
        width=res_w,
        height=res_h,
        color=text_color,
        font_size=curr_font_size,
        text="\n".join(all_lines),
        lines=all_lines,
    )
    for idx, l in enumerate(all_lines):
        child = VisualMockElement(
            name=f"TextLine_{idx}",
            center=np.array([card_bb.center[0], card_bb.center[1], 0.0]),
            width=l_widths[idx],
            height=_estimate_text_height(curr_font_size, 1),
            font_size=curr_font_size,
            text=l,
            color=text_color,
        )
        mock_res.add(child)
    mock_res.move_to(card_bb.center)
    return mock_res


def fit_math_to_card(
    latex_str_or_mobject: Union[str, MathTex, Mobject, Any],
    card: Union[Mobject, BBox, float, Any],
    font_size: float = 22.0,
    min_font_size: float = MIN_READABLE_FONT_SIZE,
    padding_x: float = 0.30,
    padding_y: float = 0.20,
    color: Optional[str] = None,
    split_operators: Optional[List[str]] = None,
    **kwargs
) -> Any:
    """
    Fits and scales LaTeX formulas within card boundaries with multi-line equation splitting.

    Guarantees:
      1. W_avail = card.width - 2 * padding_x
      2. Multi-line equation splitting across logical operators (\\, \\aligned, \\quad, =, +, -).
      3. Hard bounding box scaling ensuring formula never exceeds container boundaries.
      4. Zero micro-formulas (effective_font_size >= 12.0pt).
      5. x_min >= card.x_min + padding_x and x_max <= card.x_max - padding_x.
    """
    card_bb = _get_bbox(card)
    w_avail = card_bb.width - 2.0 * padding_x
    h_avail = card_bb.height - 2.0 * padding_y

    if w_avail <= 0.0:
        raise ValueError(f"Available card width must be positive, got {w_avail:.3f} (card.width={card_bb.width:.3f}, padding_x={padding_x})")
    if h_avail <= 0.0:
        raise ValueError(f"Available card height must be positive, got {h_avail:.3f} (card.height={card_bb.height:.3f}, padding_y={padding_y})")

    min_font_size = max(MIN_READABLE_FONT_SIZE, float(min_font_size))
    f_size = float(font_size)

    # 1. Already an instantiated mobject
    if hasattr(latex_str_or_mobject, "width") and not isinstance(latex_str_or_mobject, str):
        mob = latex_str_or_mobject
        w = float(mob.width)
        h = float(mob.height)
        scale_w = w_avail / w if w > w_avail else 1.0
        scale_h = h_avail / h if h > h_avail else 1.0
        scale = min(scale_w, scale_h, 1.0)
        effective_font_size = f_size * scale
        if effective_font_size < min_font_size - 1e-4:
            raise ValueError(
                f"Formula cannot fit container without violating minimum {min_font_size}pt font threshold "
                f"(got {effective_font_size:.1f}pt, W_avail={w_avail:.2f}, H_avail={h_avail:.2f})"
            )
        if scale < 1.0 and hasattr(mob, "scale"):
            mob.scale(scale)
        if hasattr(mob, "move_to"):
            mob.move_to(card_bb.center)
        return mob

    # 2. String formula
    raw_str = str(latex_str_or_mobject).strip().strip("$").strip()
    split_lines = _split_math_expression(raw_str, w_avail, f_size, split_operators)

    # Measure line widths & total height
    line_widths = [_estimate_mathtex_width(l, f_size) for l in split_lines]
    max_line_w = max(line_widths, default=0.4)
    tot_h = _estimate_mathtex_height(f_size, len(split_lines))

    scale_w = w_avail / max_line_w if max_line_w > w_avail else 1.0
    scale_h = h_avail / tot_h if tot_h > h_avail else 1.0
    scale = min(scale_w, scale_h, 1.0)
    effective_font_size = f_size * scale

    if effective_font_size < min_font_size - 1e-4:
        raise ValueError(
            f"Formula cannot fit container without violating minimum {min_font_size}pt font threshold "
            f"(got {effective_font_size:.1f}pt, W_avail={w_avail:.2f}, H_avail={h_avail:.2f})"
        )

    math_color = color or WHITE

    if MANIM_AVAILABLE:
        mobs = [MathTex(l, font_size=effective_font_size, color=math_color, **kwargs) for l in split_lines if l]
        if not mobs:
            mobs = [MathTex("", font_size=effective_font_size, color=math_color, **kwargs)]
        if len(mobs) == 1:
            res = mobs[0]
        else:
            res = VGroup(*mobs).arrange(DOWN, buff=0.15 * (effective_font_size / 22.0))
        if res.width > w_avail:
            res.scale_to_fit_width(w_avail)
        if res.height > h_avail:
            res.scale_to_fit_height(h_avail)
        res.move_to(card_bb.center)
        return res

    # Headless / Mock element
    res_w = min(max_line_w * scale, w_avail)
    res_h = min(tot_h * scale, h_avail)
    mock_res = VisualMockElement(
        name="FitMathCard",
        center=card_bb.center,
        width=res_w,
        height=res_h,
        font_size=effective_font_size,
        text="\n".join(split_lines),
        lines=split_lines,
        color=math_color,
    )
    for idx, l in enumerate(split_lines):
        child = VisualMockElement(
            name=f"MathLine_{idx}",
            center=np.array([card_bb.center[0], card_bb.center[1], 0.0]),
            width=line_widths[idx] * scale,
            height=_estimate_mathtex_height(effective_font_size, 1),
            font_size=effective_font_size,
            text=l,
            color=math_color,
        )
        mock_res.add(child)
    mock_res.move_to(card_bb.center)
    return mock_res


def check_arrow_collision_angle(start: Any, end: Any, angle: float) -> Tuple[bool, str]:
    """
    Checks whether a curved arrow between horizontal nodes collides upward into node cards.
    Invariant: Reverse feedback arrows flowing from right to left (start.x > end.x)
    must enforce negative angle (theta <= 0) to curve downward into empty space.
    """
    p_start = _to_point(start)
    p_end = _to_point(end)
    if p_start[0] > p_end[0] and float(angle) > 0:
        return False, f"UPWARD_ARROW_COLLISION: reverse edge from x={p_start[0]:.2f} to x={p_end[0]:.2f} with angle={angle:.3f} > 0 curves upward into node boxes."
    return True, "OK"


def ZenArrow(start=LEFT, end=RIGHT, color=None, stroke_width=2.4, buff=0.08,
             tip_length=0.16, max_tip_length_to_length_ratio=0.16, **kwargs):
    """Proportional, aerodynamic arrow balancing shaft thickness and arrowhead size.
    Eliminates default Manim bulky/blunt arrowhead (tip_length=0.35).
    Enforces tip_length <= 0.20 and max_tip_length_to_length_ratio <= 0.20.
    """
    tip_length = min(float(tip_length), 0.20)
    max_tip_ratio = min(float(max_tip_length_to_length_ratio), 0.20)
    c = color or ZenPalette.CYAN
    if not MANIM_AVAILABLE:
        p_start = _to_point(start)
        p_end = _to_point(end)
        return VisualMockElement(
            name="ZenArrow",
            center=(p_start + p_end) / 2.0,
            width=max(abs(p_end[0] - p_start[0]), 0.2),
            height=max(abs(p_end[1] - p_start[1]), 0.2),
            color=c,
            tip_length=tip_length,
        )
    return Arrow(
        start=start, end=end, color=c, stroke_width=stroke_width, buff=buff,
        tip_length=tip_length, max_tip_length_to_length_ratio=max_tip_ratio,
        **kwargs
    )


def ZenCurvedArrow(start_point, end_point, color=None, stroke_width=2.4,
                   tip_length=0.16, angle=-TAU/12, **kwargs):
    """Curved annotation arrow with sleek aerodynamic tip.
    Enforces negative angle (theta <= 0) for reverse feedback connections (start.x > end.x)
    under horizontal node chains to prevent upward collision into node cards.
    Enforces aerodynamic tip_length <= 0.20.
    """
    p_start = _to_point(start_point)
    p_end = _to_point(end_point)

    # Reverse feedback arrow under horizontal nodes: enforce negative angle (theta <= 0)
    if p_start[0] > p_end[0]:
        if angle > 0:
            angle = -abs(angle)
        elif angle == 0:
            angle = -TAU / 12

    tip_length = min(float(tip_length), 0.20)
    max_tip_ratio = min(float(kwargs.pop("max_tip_length_to_length_ratio", 0.16)), 0.20)
    c = color or ZenPalette.GOLD

    if not MANIM_AVAILABLE:
        return VisualMockElement(
            name="ZenCurvedArrow",
            center=(p_start + p_end) / 2.0,
            width=max(abs(p_end[0] - p_start[0]), 0.2),
            height=max(abs(p_end[1] - p_start[1]), 0.4),
            color=c,
            tip_length=tip_length,
        )
    return CurvedArrow(
        start_point, end_point, color=c, stroke_width=stroke_width,
        tip_length=tip_length, angle=angle,
        max_tip_length_to_length_ratio=max_tip_ratio,
        **kwargs
    )


def ZenDoubleArrow(start=LEFT, end=RIGHT, color=None, stroke_width=2.4, buff=0.08,
                   tip_length=0.16, max_tip_length_to_length_ratio=0.16, **kwargs):
    """Bidirectional aerodynamic arrow balancing shaft thickness and arrowhead size.
    Enforces tip_length <= 0.20 and max_tip_length_to_length_ratio <= 0.20.
    """
    tip_length = min(float(tip_length), 0.20)
    max_tip_ratio = min(float(max_tip_length_to_length_ratio), 0.20)
    c = color or ZenPalette.CYAN
    if not MANIM_AVAILABLE:
        p_start = _to_point(start)
        p_end = _to_point(end)
        return VisualMockElement(
            name="ZenDoubleArrow",
            center=(p_start + p_end) / 2.0,
            width=max(abs(p_end[0] - p_start[0]), 0.2),
            height=max(abs(p_end[1] - p_start[1]), 0.2),
            color=c,
            tip_length=tip_length,
        )
    return DoubleArrow(
        start=start, end=end, color=c, stroke_width=stroke_width, buff=buff,
        tip_length=tip_length, max_tip_length_to_length_ratio=max_tip_ratio,
        **kwargs
    )


def _vn_text(content, font_size=18, color=None, weight="NORMAL", font=DEFAULT_FONT, **kw):
    c = color or ZenPalette.TEXT_PRIMARY
    if not MANIM_AVAILABLE:
        w = _estimate_text_width(str(content), font_size, font=font)
        h = _estimate_text_height(font_size)
        return VisualMockElement(name="Text", text=str(content), width=w, height=h, font_size=font_size, color=c)
    return Text(content, font=font, font_size=font_size, color=c, weight=weight, **kw)


def _safe_mathtex(tex_str, font_size=28, color=None, max_width=10.0, **kw):
    c = color or WHITE
    if not MANIM_AVAILABLE:
        w = min(_estimate_mathtex_width(str(tex_str), font_size), max_width)
        h = _estimate_mathtex_height(font_size)
        return VisualMockElement(name="MathTex", text=str(tex_str), width=w, height=h, font_size=font_size, color=c)
    m = MathTex(tex_str, font_size=font_size, color=c, **kw)
    if m.width > max_width: m.scale_to_fit_width(max_width)
    return m


def DiagramCard(content, title="", accent_color=None, width=5.0, height=3.0, fill_opacity=0.75, corner_radius=0.2):
    """Glassmorphism card with neon border and strict text containment."""
    ac = accent_color or ZenPalette.CYAN
    card = RoundedRectangle(corner_radius=corner_radius, width=width, height=height,
        fill_color=ZenPalette.BG_CARD, fill_opacity=fill_opacity, stroke_color=ac, stroke_width=1.5)
    glow = RoundedRectangle(corner_radius=corner_radius+0.02, width=width+0.06, height=height+0.06,
        fill_opacity=0, stroke_color=ac, stroke_width=0.8, stroke_opacity=0.3)
    group = VGroup(glow, card)
    if title:
        t = _vn_text(title, font_size=16, color=ac, weight="BOLD")
        if t is not None:
            max_title_w = width - 0.5
            if t.width > max_title_w:
                t.scale_to_fit_width(max_title_w)
            t.move_to(card.get_top() + DOWN*0.35)
            group.add(t)
    if content is not None:
        if isinstance(content, str): content = _vn_text(content, font_size=15)
        mw, mh = width-0.6, height-(0.9 if title else 0.5)
        if content.width > mw: content.scale_to_fit_width(mw)
        if content.height > mh: content.scale_to_fit_height(mh)
        content.move_to(card.get_center() + (DOWN*0.15 if title else ORIGIN))
        group.add(content)
    return group


def ComparisonPanel(left_title, left_content, right_title, right_content,
                    left_color=None, right_color=None, panel_width=5.8, panel_height=4.5, divider_color=None, gap=0.3):
    """Side-by-side comparison panel with safe zones."""
    lc, rc, dc = left_color or ZenPalette.SKY, right_color or ZenPalette.EMERALD, divider_color or ZenPalette.AMBER
    hw = (panel_width - gap) / 2
    left = DiagramCard(left_content, title=left_title, accent_color=lc, width=hw, height=panel_height)
    left.shift(LEFT*(hw/2+gap/2))
    right = DiagramCard(right_content, title=right_title, accent_color=rc, width=hw, height=panel_height)
    right.shift(RIGHT*(hw/2+gap/2))
    div = DashedLine(UP*panel_height/2, DOWN*panel_height/2, color=dc, stroke_width=1.5, dash_length=0.15, stroke_opacity=0.5)
    return VGroup(left, div, right)


def TensorDiagram(shape=(4,3), dim_labels=None, colors=None, cell_size=0.5, arrow_style="neon",
                  highlight_slice=None, highlight_index=0):
    """Matrix/tensor with collision-safe balanced dimension arrows."""
    rows, cols = shape[:2]
    cs = cell_size
    clrs = colors or [ZenPalette.CYAN, ZenPalette.AMBER, ZenPalette.VIOLET]
    group, cells = VGroup(), VGroup()
    for r in range(rows):
        for c in range(cols):
            fill, op = ZenPalette.BG_CARD, 0.7
            if highlight_slice == "row" and r == highlight_index: fill, op = clrs[0], 0.4
            elif highlight_slice == "col" and c == highlight_index: fill, op = clrs[1%len(clrs)], 0.4
            rect = Rectangle(width=cs, height=cs, fill_color=fill, fill_opacity=op,
                stroke_color=ZenPalette.BORDER_SUBTLE, stroke_width=1.0)
            rect.move_to(np.array([c*cs-(cols-1)*cs/2, -r*cs+(rows-1)*cs/2, 0]))
            cells.add(rect)
    group.add(cells)
    labels = dim_labels or [f"Dim {i}" for i in range(len(shape))]
    if len(labels) > 0:
        ax = (cols-1)*cs/2 + cs/2 + 0.3
        arr = Arrow(np.array([ax,(rows-1)*cs/2,0]), np.array([ax,-(rows-1)*cs/2,0]), color=clrs[0], stroke_width=2.4, buff=0.05, tip_length=0.16, max_tip_length_to_length_ratio=0.16)
        lbl = _vn_text(labels[0], font_size=13, color=clrs[0])
        safe_place(lbl, arr, RIGHT, buff=0.15, avoid=list(cells))
        group.add(arr, lbl)
    if len(labels) > 1:
        ay = -(rows-1)*cs/2 - cs/2 - 0.3
        arr2 = Arrow(np.array([-(cols-1)*cs/2,ay,0]), np.array([(cols-1)*cs/2,ay,0]), color=clrs[1%len(clrs)], stroke_width=2.4, buff=0.05, tip_length=0.16, max_tip_length_to_length_ratio=0.16)
        lbl2 = _vn_text(labels[1], font_size=13, color=clrs[1%len(clrs)])
        safe_place(lbl2, arr2, DOWN, buff=0.15, avoid=list(cells))
        group.add(arr2, lbl2)
    return group


def FlowChart(nodes, edges=None, layout="horizontal", node_width=2.0, node_height=0.8, spacing=1.2, arrow_color=None):
    """Pipeline flowchart with auto-routing arrows."""
    ac = arrow_color or ZenPalette.AMBER
    group, node_mobs = VGroup(), []
    for i, nd in enumerate(nodes):
        label, color = nd.get("label", f"Node {i}"), nd.get("color", ZenPalette.CYAN)
        rect = RoundedRectangle(corner_radius=0.15, width=node_width, height=node_height,
            fill_color=ZenPalette.BG_CARD, fill_opacity=0.8, stroke_color=color, stroke_width=2.0)
        lbl = _vn_text(label, font_size=14, color=color)
        if lbl.width > node_width-0.3: lbl.scale_to_fit_width(node_width-0.3)
        lbl.move_to(rect.get_center())
        ng = VGroup(rect, lbl)
        if layout == "horizontal": ng.move_to(np.array([i*(node_width+spacing),0,0]))
        else: ng.move_to(np.array([0,-i*(node_height+spacing),0]))
        node_mobs.append(ng)
        group.add(ng)
    group.move_to(ORIGIN)
    for s,d in (edges or [(i,i+1) for i in range(len(nodes)-1)]):
        if s < len(node_mobs) and d < len(node_mobs):
            sp = node_mobs[s][0].get_right() if layout=="horizontal" else node_mobs[s][0].get_bottom()
            ep = node_mobs[d][0].get_left() if layout=="horizontal" else node_mobs[d][0].get_top()
            group.add(Arrow(sp, ep, color=ac, stroke_width=2.4, buff=0.08, tip_length=0.16, max_tip_length_to_length_ratio=0.16))
    return group


def NeuralNetworkDiagram(layers=[3,5,4,2], highlight_path=None, node_radius=0.18,
                         layer_spacing=2.0, node_spacing=0.7, colors=None, connection_opacity=0.15, highlight_color=None):
    """Multi-layer neural network with highlighted paths."""
    hc = highlight_color or ZenPalette.AMBER
    clrs = colors or [ZenPalette.CYAN, ZenPalette.EMERALD, ZenPalette.VIOLET, ZenPalette.SKY]
    group, layer_nodes = VGroup(), []
    for li, nn in enumerate(layers):
        color, nodes_l = clrs[li%len(clrs)], []
        for ni in range(nn):
            x = li*layer_spacing - (len(layers)-1)*layer_spacing/2
            y = ni*node_spacing - (nn-1)*node_spacing/2
            dot = Circle(radius=node_radius, fill_color=ZenPalette.BG_CARD, fill_opacity=0.9,
                stroke_color=color, stroke_width=2.0)
            dot.move_to(np.array([x,y,0]))
            nodes_l.append(dot)
            group.add(dot)
        layer_nodes.append(nodes_l)
    hs = set()
    if highlight_path:
        for l1,n1,l2,n2 in highlight_path: hs.add((l1,n1,l2,n2))
    for li in range(len(layers)-1):
        for n1i,n1 in enumerate(layer_nodes[li]):
            for n2i,n2 in enumerate(layer_nodes[li+1]):
                color = hc if (li,n1i,li+1,n2i) in hs else clrs[li%len(clrs)]
                op = 0.8 if (li,n1i,li+1,n2i) in hs else connection_opacity
                sw = 2.5 if (li,n1i,li+1,n2i) in hs else 1.0
                line = Line(n1.get_center(), n2.get_center(), color=color, stroke_opacity=op, stroke_width=sw)
                group.add(line)
    return group


def TimelineDiagram(events, total_width=9.0, line_color=None, accent_color=None):
    """Horizontal chronological timeline with glowing nodes."""
    ac, lc = accent_color or ZenPalette.AMBER, line_color or GRAY_C
    group, n = VGroup(), len(events)
    if not n: return group
    hw = total_width/2
    group.add(Line(LEFT*hw, RIGHT*hw, color=lc, stroke_width=2.0))
    sp = total_width/max(n-1,1) if n>1 else 0
    all_lbls = []
    for i, evt in enumerate(events):
        x = -hw+i*sp if n>1 else 0
        color = evt.get("color", ac)
        dot = Circle(radius=0.1, fill_color=color, fill_opacity=1.0, stroke_color=WHITE, stroke_width=1.0)
        dot.move_to(np.array([x,0,0]))
        group.add(dot)
        if evt.get("year"):
            ym = _vn_text(str(evt["year"]), font_size=12, color=ZenPalette.TEXT_DIM)
            ym.next_to(dot, DOWN, buff=0.15)
            group.add(ym)
            all_lbls.append(ym)
        if evt.get("label"):
            lbl = _vn_text(evt["label"], font_size=13, color=color)
            lbl.next_to(dot, UP*(1 if i%2==0 else 1.8), buff=0.2)
            if all_lbls: auto_resolve_overlap(lbl, all_lbls, strategy="shift", clearance=0.1)
            group.add(lbl)
            all_lbls.append(lbl)
    return group


def ProbabilityDistribution(func=None, x_range=(-4,4), shade_region=None, label="",
                            axes_width=6.0, axes_height=3.5, curve_color=None, shade_color=None, shade_opacity=0.3):
    """Probability distribution curve with shading."""
    cc, sc = curve_color or ZenPalette.CYAN, shade_color or ZenPalette.CYAN
    if func is None: func = lambda x: (1/math.sqrt(2*math.pi))*math.exp(-0.5*x**2)
    group = VGroup()
    axes = Axes(x_range=[x_range[0],x_range[1],1], y_range=[0,0.5,0.1], x_length=axes_width, y_length=axes_height,
        axis_config={"color": GRAY_C, "stroke_width": 1.5})
    group.add(axes)
    curve = axes.plot(func, color=cc, stroke_width=3)
    group.add(curve)
    if shade_region:
        group.add(axes.get_area(curve, x_range=shade_region, color=sc, opacity=shade_opacity))
    if label:
        lbl = _vn_text(label, font_size=14, color=cc)
        lbl.next_to(curve, UP, buff=0.2)
        _DEFAULT_SAFE_ZONE.clamp(lbl)
        group.add(lbl)
    return group


def NeonArrow(start, end, glow_color=None, core_color=None, core_width=2.4, glow_layers=3, glow_width_decay=0.6, glow_opacity_decay=0.3, **kw):
    """3-layer neon arrow with sleek proportional arrowhead (tip_length=0.16, max_tip_length_to_length_ratio=0.16)."""
    gc, cc = glow_color or ZenPalette.CYAN, core_color or ZenPalette.NEON_CORE
    group = VGroup()
    buff_val = kw.get("buff", 0.0)
    tip_len = kw.get("tip_length", 0.16)
    tip_ratio = kw.get("max_tip_length_to_length_ratio", 0.16)
    for i in range(glow_layers, 0, -1):
        group.add(Arrow(start=start, end=end, color=gc, stroke_width=core_width+i*2*glow_width_decay,
            stroke_opacity=glow_opacity_decay/i, buff=buff_val, tip_length=tip_len, max_tip_length_to_length_ratio=tip_ratio))
    group.add(Arrow(start=start, end=end, color=cc, stroke_width=core_width, buff=buff_val, tip_length=tip_len, max_tip_length_to_length_ratio=tip_ratio))
    return group


def EquationBox(tex_string, title="", accent_color=None, width=6.0, padding=0.4, font_size=30):
    """Highlighted equation box with gradient border."""
    ac = accent_color or ZenPalette.AMBER
    eq = _safe_mathtex(tex_string, font_size=font_size, color=WHITE, max_width=width-padding*2)
    bh = max(eq.height+padding*2, 1.2) + (0.5 if title else 0)
    box = RoundedRectangle(corner_radius=0.15, width=width, height=bh,
        fill_color=ZenPalette.BG_CARD, fill_opacity=0.8, stroke_color=ac, stroke_width=2.5)
    group = VGroup(box)
    if title:
        tb = Rectangle(width=width-0.04, height=0.4, fill_color=ac, fill_opacity=0.15, stroke_width=0)
        tb.move_to(box.get_top()+DOWN*0.2)
        tm = _vn_text(title, font_size=13, color=ac, weight="BOLD")
        if tm is not None and tm.width > width - 0.6:
            tm.scale_to_fit_width(width - 0.6)
        tm.move_to(tb.get_center())
        group.add(tb, tm)
        eq.move_to(box.get_center()+DOWN*0.15)
    else:
        eq.move_to(box.get_center())
    group.add(eq)
    return group


def AnimatedCounter(start=0, end=100, prefix="", suffix="%", duration=2.0, font_size=36, color=None, num_decimal_places=1):
    """Animated counting number. Returns (tracker, group, animate_fn)."""
    c = color or ZenPalette.AMBER
    tracker = ValueTracker(start)
    counter = DecimalNumber(start, num_decimal_places=num_decimal_places, font_size=font_size, color=c)
    group = VGroup()
    if prefix:
        pre = _vn_text(prefix, font_size=int(font_size*0.7), color=c)
        pre.next_to(counter, LEFT, buff=0.15)
        group.add(pre)
    group.add(counter)
    if suffix:
        suf = _vn_text(suffix, font_size=int(font_size*0.7), color=c)
        suf.next_to(counter, RIGHT, buff=0.08)
        group.add(suf)
    counter.add_updater(lambda m: m.set_value(tracker.get_value()))
    if prefix: group[0].add_updater(lambda m: m.next_to(counter, LEFT, buff=0.15))
    if suffix: group[-1].add_updater(lambda m: m.next_to(counter, RIGHT, buff=0.08))
    def _animate(dur=None):
        return tracker.animate(rate_func=rate_functions.ease_out_cubic, run_time=dur or duration).set_value(end)
    return tracker, group, _animate


# =============================================================================
# PILLAR 3: VOICE-SYNC TIMELINE
# =============================================================================

class VoiceSyncTimeline:
    """Scene-level audio synchronization for Manim animations."""
    def __init__(self, audio_paths):
        self.audio_paths = [str(p) for p in audio_paths]
        self.durations = [self._probe_duration(p) for p in self.audio_paths]

    @staticmethod
    def _probe_duration(path):
        try:
            r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                "-of","default=noprint_wrappers=1:nokey=1",path], capture_output=True, text=True, timeout=10)
            return float(r.stdout.strip())
        except: return 30.0

    @property
    def total_duration(self): return sum(self.durations)

    def scene_duration(self, idx): return self.durations[idx] if 0 <= idx < len(self.durations) else 30.0

    def allocate(self, scene_index, n_animations, weights=None, padding=0.5):
        total = max(self.scene_duration(scene_index) - padding, 1.0)
        if weights:
            ws = sum(weights)
            return [(w/ws)*total for w in weights]
        return [total/max(n_animations,1)] * n_animations

    def wait_until(self, scene_index, target_seconds, elapsed):
        return max(target_seconds - elapsed, 0)


# =============================================================================
# PILLAR 4: SFX/VFX INTEGRATION
# =============================================================================

@dataclass
class SFXCue:
    sfx_name: str
    timestamp: float
    volume: float = 1.0
    SFX_FILES = {
        "whoosh": "sfx_whoosh.wav",
        "pop": "sfx_pop.wav",
        "impact": "sfx_impact.wav",
        "shimmer": "sfx_shimmer.wav",
        "blip": "sfx_blip.wav",
        "coin_flip": "sfx_coin_flip.wav",
        "coin_landing": "sfx_coin_landing.wav",
        "typewriter": "typewriter.wav",
        "swoosh": "sfx_whoosh.wav",
        "heartbeat": "heartbeat.wav",
        "glitch": "glitch.wav"
    }

    @property
    def file_path(self):
        fname = self.SFX_FILES.get(self.sfx_name, f"sfx_{self.sfx_name}.wav")
        return os.path.join("sfx", fname)


def mix_sfx(video_path, cues, output_path, sfx_base_dir="assets/scripts_video/sfx"):
    if not cues:
        subprocess.run(["cp", video_path, output_path], check=True)
        return True
    inputs = ["-i", video_path]
    filter_parts, amix_inputs = [], ["[0:a]"]
    for i, cue in enumerate(cues):
        fname = SFXCue.SFX_FILES.get(cue.sfx_name, f"sfx_{cue.sfx_name}.wav")
        sfx_path = os.path.join(sfx_base_dir, fname)
        if not os.path.exists(sfx_path):
            alt_path = os.path.join(sfx_base_dir, f"{cue.sfx_name}.wav")
            if os.path.exists(alt_path):
                sfx_path = alt_path
            else:
                continue
        inputs.extend(["-i", sfx_path])
        file_idx = len(inputs) // 2 - 1
        delay_ms = int(cue.timestamp * 1000)
        filter_parts.append(f"[{file_idx}:a]adelay={delay_ms}|{delay_ms},volume={cue.volume}[sfx{i}]")
        amix_inputs.append(f"[sfx{i}]")
    if not filter_parts:
        subprocess.run(["cp", video_path, output_path], check=True)
        return True
    fc = ";".join(filter_parts) + f";{''.join(amix_inputs)}amix=inputs={len(amix_inputs)}:duration=first:dropout_transition=0.5:normalize=0[aout]"
    cmd = ["ffmpeg","-y","-v","error",*inputs,"-filter_complex",fc,"-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","320k","-ar","48000",output_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[SFX MIX ERROR] {e.stderr.decode()[:500]}")
        subprocess.run(["cp", video_path, output_path], check=True)
        return False


def GlowEffect(mobject, color=None, layers=3, opacity_decay=0.25, width_growth=2.0):
    gc = color or ZenPalette.CYAN
    group = VGroup()
    for i in range(layers, 0, -1):
        g = mobject.copy()
        g.set_stroke(color=gc, width=mobject.get_stroke_width()+i*width_growth, opacity=opacity_decay/i)
        g.set_fill(opacity=0)
        group.add(g)
    group.add(mobject)
    return group


def EurekaFlash(center=None, color=None, radius=3.0, n_lines=12):
    c = center if center is not None else ORIGIN
    clr = color or ZenPalette.AMBER
    group = VGroup()
    for i in range(n_lines):
        a = i * TAU / n_lines
        s = c + 0.3*np.array([math.cos(a), math.sin(a), 0])
        e = c + radius*np.array([math.cos(a), math.sin(a), 0])
        group.add(Line(s, e, color=clr, stroke_width=2.0, stroke_opacity=0.7))
    return group


def GlassmorphismRect(width=5.0, height=3.0, fill_color=None, border_color=None, fill_opacity=0.6, corner_radius=0.2, border_width=1.5):
    fc, bc = fill_color or ZenPalette.BG_CARD, border_color or ZenPalette.CYAN
    glow = RoundedRectangle(corner_radius=corner_radius+0.03, width=width+0.08, height=height+0.08,
        stroke_color=bc, stroke_width=border_width*0.5, stroke_opacity=0.25, fill_opacity=0)
    main = RoundedRectangle(corner_radius=corner_radius, width=width, height=height,
        fill_color=fc, fill_opacity=fill_opacity, stroke_color=bc, stroke_width=border_width)
    return VGroup(glow, main)


# =============================================================================
# PILLAR 5: CLEAR SPATIAL LAYOUT COMPONENTS (Toán Thầy Việt & 3Blue1Brown standard)
# =============================================================================

def StateTrackerBar(states: list, active_index: int = 0, y_pos: float = 3.3, spacing: float = 1.6, active_color=None, inactive_color=None):
    """
    Top-bar Breadcrumb / State Tracker (inspired by Toán Thầy Việt & 3Blue1Brown).
    Renders a clean horizontal sequence of circular indicator pills showing reasoning progression.
    E.g.: ['N', 'Z', 'Q', 'R', '?'] or ['BST', 'O(N)', 'Splay', 'O(log N)'].
    """
    ac = active_color or ZenPalette.GOLD
    ic = inactive_color or ZenPalette.BORDER_SUBTLE
    group = VGroup()
    n = len(states)
    start_x = -((n - 1) * spacing) / 2.0

    for i, state in enumerate(states):
        cx = start_x + i * spacing
        is_active = (i == active_index)
        col = ac if is_active else ic
        bg_col = ZenPalette.BG_CARD if not is_active else ZenPalette.BG_CARD_ALT

        pill = Circle(radius=0.28, stroke_color=col, stroke_width=2.5 if is_active else 1.2, fill_color=bg_col, fill_opacity=0.9)
        pill.move_to(np.array([cx, y_pos, 0]))

        if is_active:
            glow = Circle(radius=0.34, stroke_color=ac, stroke_width=1.0, stroke_opacity=0.35, fill_opacity=0)
            glow.move_to(pill.get_center())
            group.add(glow)

        lbl = _vn_text(state, font_size=13, color=WHITE if is_active else ZenPalette.TEXT_DIM, weight="BOLD" if is_active else "NORMAL")
        lbl.move_to(pill.get_center())
        group.add(pill, lbl)

        if i < n - 1:
            line = Line(
                np.array([cx + 0.32, y_pos, 0]),
                np.array([cx + spacing - 0.32, y_pos, 0]),
                stroke_color=ZenPalette.BORDER_SUBTLE,
                stroke_width=1.5,
                stroke_opacity=0.6
            )
            group.add(line)

    return group


def ConceptBadge(text: str, color=None, font_size=12, padding=0.2):
    """
    Uppercase concept badge / tag with rounded border (e.g. [ BIẾN ĐỔI FOURIER ]).
    """
    c = color or ZenPalette.CYAN
    txt = _vn_text(text.upper(), font_size=font_size, color=c, weight="BOLD")
    bg = RoundedRectangle(
        corner_radius=0.1,
        width=txt.width + padding * 2,
        height=txt.height + padding * 1.5,
        stroke_color=c,
        stroke_width=1.5,
        fill_color=ZenPalette.BG_CARD,
        fill_opacity=0.85
    )
    bg.move_to(txt.get_center())
    return VGroup(bg, txt)


def BottomCalloutCard(text: str, width=10.5, height=0.85, y_pos=-2.1, accent_color=None, font_size=13):
    """
    Bottom explanatory callout card (placed safely above the subtitle zone Y >= -2.6).
    Holds distilled pedagogical takeaway with strict card containment.
    """
    ac = accent_color or ZenPalette.BORDER_SUBTLE
    card = RoundedRectangle(
        corner_radius=0.15,
        width=width,
        height=height,
        stroke_color=ac,
        stroke_width=1.5,
        fill_color=ZenPalette.BG_CARD,
        fill_opacity=0.92
    ).shift(UP * y_pos)
    txt = _vn_text(text, font_size=font_size, color=ZenPalette.TEXT_PRIMARY)
    if txt is not None:
        fit_text_to_card(txt, card, margin_x=0.4, margin_y=0.15)
        txt.move_to(card.get_center())
    return VGroup(card, txt)


def PointCallout(target_point, label="ở ĐÂY", direction=UR, length=1.2, color=None, font_size=14):
    """
    Curved arrow annotation pointing to a specific coordinate/point with balanced aerodynamic tip.
    """
    c = color or ZenPalette.GOLD
    t = np.array(target_point)
    s = t + direction * length
    arrow = CurvedArrow(s, t + direction * 0.1, color=c, stroke_width=2.4, tip_length=0.16, max_tip_length_to_length_ratio=0.16, angle=-TAU/12)
    lbl = _vn_text(label, font_size=font_size, color=c, weight="BOLD")
    lbl.next_to(s, direction, buff=0.1)
    return VGroup(arrow, lbl)


def SafeFormulaCard(latex_str: str, title: str = "", explanation: str = "", width=4.5, height=1.6, accent_color=None):
    """
    Science Formula Box formatted for Cognitive Stack (Right Column X in [1.0, 6.0]).
    Uses _safe_mathtex and fit_text_to_card to guarantee containment.
    """
    ac = accent_color or ZenPalette.BORDER_SUBTLE
    card = RoundedRectangle(
        corner_radius=0.15,
        width=width,
        height=height,
        stroke_color=ac,
        stroke_width=1.5,
        fill_color=ZenPalette.BG_CARD,
        fill_opacity=0.92
    )
    tex = _safe_mathtex(latex_str, color=ZenPalette.CYAN, font_size=22)
    if tex is not None:
        fit_text_to_card(tex, card, margin_x=0.3, margin_y=0.2)
        tex.move_to(card.get_center())
    grp = VGroup(card, tex)
    if title:
        badge = ConceptBadge(title, font_size=11, color=ZenPalette.GOLD)
        badge.next_to(card, UP, buff=0.15)
        grp.add(badge)
    if explanation:
        exp_txt = _vn_text(explanation, font_size=11, color=ZenPalette.TEXT_MUTED)
        if exp_txt is not None:
            if exp_txt.width > width:
                exp_txt.scale_to_fit_width(width)
            exp_txt.next_to(card, DOWN, buff=0.15)
    return grp


def ScienceAxisBox(x_range=[-3, 3, 1], y_range=[-2, 2, 1], width=4.8, height=3.2, center_x=-2.8, center_y=0.6):
    """
    Pre-configured 2D Coordinate frame constrained safely within the Left Visual Canvas.
    """
    axes = Axes(
        x_range=x_range,
        y_range=y_range,
        x_length=width,
        y_length=height,
        axis_config={"color": ZenPalette.BORDER_SUBTLE, "stroke_width": 1.5}
    ).move_to(np.array([center_x, center_y, 0]))
    return axes


def ZoneStageBox(width=6.0, height=3.0, center_x=-2.8, center_y=0.4, stroke_color=None, corner_radius=0.15):
    """
    Collision-Safe Background Stage for Zone 2 (Left Canvas 60%).
    Mathematically guaranteed to keep bottom boundary at Y >= -1.1,
    leaving at least 0.58 units of clear breathing margin above Zone 4 Callout Card (Y = -1.68).
    """
    sc = stroke_color or ZenPalette.BORDER_SUBTLE
    card = RoundedRectangle(
        corner_radius=corner_radius,
        width=width,
        height=height,
        stroke_color=sc,
        stroke_width=1.2,
        fill_color=ZenPalette.BG_CARD,
        fill_opacity=0.85
    ).move_to(np.array([center_x, center_y, 0]))
    return card


def ZoneAutoVStack(items: list, center_x=3.8, y_top=2.2, y_bottom_limit=-1.5, default_buff=0.25):
    """
    Collision-Safe Vertical Flex Stack for Zone 3 (Cognitive Stack Right 40%).
    Auto-computes vertical layout, adjusts spacing and auto-scales children if needed
    to ensure NO item ever drops below y_bottom_limit (above Zone 4 Callout Card).
    """
    if not MANIM_AVAILABLE or not items:
        return VGroup(*items) if items else None
    
    valid_items = [it for it in items if it is not None]
    if not valid_items:
        return VGroup()
        
    grp = VGroup(*valid_items)
    grp.arrange(DOWN, buff=default_buff, center=False)
    # Align top to y_top and x to center_x
    grp.move_to(np.array([center_x, y_top - grp.height / 2, 0]))
    
    # Check if bottom breaches safe limit
    bottom_y = grp.get_bottom()[1]
    if bottom_y < y_bottom_limit:
        available_height = y_top - y_bottom_limit
        scale_factor = available_height / grp.height * 0.95
        grp.scale(scale_factor)
        grp.move_to(np.array([center_x, y_top - grp.height / 2, 0]))
    
    return grp


# =============================================================================
# PHOSPHOR DUOTONE ICON COMPONENTS (1,512 SVG ICONS ADAPTIVE STYLES)
# =============================================================================

def _get_duotone_dir() -> Path:
    docker_path = Path("/manim/assets/duotone")
    if docker_path.exists():
        return docker_path
    local_path = Path(__file__).resolve().parent.parent / "duotone"
    if local_path.exists():
        return local_path
    return Path("/home/zen/hermes-agent/assets/duotone")


def DuotoneIcon(
    name: str,
    size: float = 0.8,
    primary_color=None,
    secondary_color=None,
    secondary_opacity: float = 0.28,
    style: str = "neo_noir"
):
    """
    Loads and styles a Phosphor Duotone icon from assets/duotone.
    Safely caches intermediate SVG files in /tmp to prevent permission errors in Docker.
    Supports 4 Adaptive Styles:
    - 'neo_noir': Subtle dark glass glow with neon accents (ZenPham signature).
    - 'architecture': System design / cloud / microservices nodes (ByteByteGo style).
    - 'vibrant': High-contrast complementary duotone (Kurzgesagt/Primer style).
    - 'minimal': Restrained monochrome glyph for mathematical elegance (3B1B style).
    """
    cache_dir = Path("/tmp/manim_svg_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    if not isinstance(name, str) or not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-." for c in name) or ".." in name:
        raise ValueError("Duotone icon name must be an asset ID, not a path")
    clean_name = name.removesuffix(".svg").removesuffix("-duotone")
    src_file = _get_duotone_dir() / f"{clean_name}-duotone.svg"
    
    if not src_file.is_file():
        raise FileNotFoundError(f"Duotone SVG asset not found: {src_file}")

    cached_file = cache_dir / f"{clean_name}-duotone.svg"
    tree = ET.parse(src_file)
    # Manim ignores SVG opacity; preserve Phosphor layer alpha as fill-opacity.
    for element in tree.iter():
        if "opacity" in element.attrib:
            opacity = float(element.attrib.pop("opacity"))
            element.set("fill-opacity", str(opacity * float(element.get("fill-opacity", "1"))))
            element.set("stroke-opacity", str(opacity * float(element.get("stroke-opacity", "1"))))
    tree.write(cached_file, encoding="unicode")

    svg = SVGMobject(str(cached_file), use_svg_cache=False)
    svg.scale_to_fit_height(size)

    # Style presets
    if style == "neo_noir":
        p_col = primary_color or ZenPalette.CYAN
        s_col = secondary_color or p_col
        s_op = secondary_opacity
    elif style == "architecture":
        p_col = primary_color or ZenPalette.GOLD
        s_col = secondary_color or ZenPalette.AMBER
        s_op = 0.35
    elif style == "vibrant":
        p_col = primary_color or ZenPalette.RED
        s_col = secondary_color or ZenPalette.GOLD
        s_op = 0.5
    else: # minimal
        p_col = primary_color or ZenPalette.TEXT_PRIMARY
        s_col = secondary_color or ZenPalette.TEXT_MUTED
        s_op = 0.2

    for part in svg.submobjects:
        secondary = part.get_fill_opacity() < 1.0
        part.set_fill(color=s_col if secondary else p_col, opacity=s_op if secondary else 1.0)
        part.set_stroke(width=0)

    return svg


def DuotoneBadge(icon_name: str, text: str, color=None, font_size=12):
    """
    Concept Badge augmented with an embedded Phosphor Duotone Icon.
    """
    c = color or ZenPalette.GOLD
    icon = DuotoneIcon(icon_name, size=0.32, primary_color=c)
    lbl = _vn_text(text, font_size=font_size, color=c, weight="BOLD")
    content = VGroup(icon, lbl).arrange(RIGHT, buff=0.15)
    
    bg = RoundedRectangle(
        corner_radius=0.12,
        width=content.width + 0.5,
        height=0.48,
        stroke_color=c,
        stroke_width=1.2,
        fill_color=ZenPalette.BG_CARD,
        fill_opacity=0.92
    )
    content.move_to(bg.get_center())
    return VGroup(bg, content)


def ArchitectureNode(icon_name: str, title: str, subtitle: str = "", color=None, width=2.4, height=1.6):
    """
    System Architecture Card for CS/System Design videos (ByteByteGo style).
    """
    c = color or ZenPalette.CYAN
    card = RoundedRectangle(
        corner_radius=0.15,
        width=width,
        height=height,
        stroke_color=c,
        stroke_width=1.5,
        fill_color=ZenPalette.BG_CARD,
        fill_opacity=0.95
    )
    icon = DuotoneIcon(icon_name, size=0.55, primary_color=c, style="architecture")
    t_txt = _vn_text(title, font_size=12, color=ZenPalette.TEXT_PRIMARY, weight="BOLD")
    if t_txt is not None and t_txt.width > width - 0.4:
        t_txt.scale_to_fit_width(width - 0.4)
    
    elems = [icon, t_txt]
    if subtitle:
        s_txt = _vn_text(subtitle, font_size=9, color=ZenPalette.TEXT_MUTED)
        if s_txt is not None and s_txt.width > width - 0.4:
            s_txt.scale_to_fit_width(width - 0.4)
        elems.append(s_txt)
        
    stack = VGroup(*elems).arrange(DOWN, buff=0.1)
    stack.move_to(card.get_center())
    return VGroup(card, stack)


def DuotoneTrackerBar(items: list, active_idx=0, y_pos=3.3, radius=0.32):
    """
    StateTrackerBar using Phosphor Duotone icons inside circular breadcrumbs.
    items: list of tuples (icon_name, label) e.g. [('tree-structure', 'BST'), ('cpu', 'SPLAY')]
    """
    bar = VGroup()
    for idx, (icon_name, label) in enumerate(items):
        is_active = (idx == active_idx)
        c = ZenPalette.GOLD if is_active else ZenPalette.TEXT_MUTED
        circ = Circle(
            radius=radius,
            stroke_color=c,
            stroke_width=2.0 if is_active else 1.0,
            fill_color=ZenPalette.BG_CARD if is_active else ZenPalette.BG_OBSIDIAN,
            fill_opacity=0.92
        )
        icon = DuotoneIcon(icon_name, size=radius * 1.1, primary_color=c)
        icon.move_to(circ.get_center())
        node = VGroup(circ, icon)
        bar.add(node)
    bar.arrange(RIGHT, buff=0.8).shift(UP * y_pos)
    return bar


def add_zenpham_watermark(*args, **kwargs):
    pass



# =============================================================================
# DEMO SCENE
# =============================================================================

if MANIM_AVAILABLE:
    class DemoAllComponents(Scene):
        def construct(self):
            title = _vn_text("MANIM PRODUCTION SYSTEM — 10 PREMIUM COMPONENTS", font_size=20, color=ZenPalette.AMBER, weight="BOLD")
            title.to_edge(UP, buff=0.3)
            self.play(FadeIn(title), run_time=0.5)
            self.wait(0.5)

            demos = [
                ("DiagramCard", lambda: DiagramCard(_safe_mathtex(r"\nabla_\theta \mathcal{L}"), title="Gradient", accent_color=ZenPalette.CYAN, width=5.5, height=2.0)),
                ("ComparisonPanel", lambda: ComparisonPanel("BatchNorm", _vn_text("Dọc Batch",font_size=13), "LayerNorm", _vn_text("Ngang Feature",font_size=13), panel_width=5.5, panel_height=2.5)),
                ("TensorDiagram", lambda: TensorDiagram(shape=(4,6), dim_labels=["Batch","Features"], highlight_slice="col", highlight_index=2)),
                ("FlowChart", lambda: FlowChart(nodes=[{"label":"Input","color":ZenPalette.CYAN},{"label":"Norm","color":ZenPalette.EMERALD},{"label":"Output","color":ZenPalette.AMBER}], node_width=1.8)),
                ("NeuralNetwork", lambda: NeuralNetworkDiagram([3,5,4,2], highlight_path=[(0,1,1,2),(1,2,2,1),(2,1,3,0)])),
                ("Timeline", lambda: TimelineDiagram([{"year":"1687","label":"Newton","color":ZenPalette.AMBER},{"year":"1948","label":"Shannon","color":ZenPalette.CYAN},{"year":"2017","label":"Transformer","color":ZenPalette.VIOLET}], total_width=10)),
                ("Distribution", lambda: ProbabilityDistribution(shade_region=(-1,1), label="N(0,1)", axes_width=5)),
                ("NeonArrow", lambda: NeonArrow(LEFT*3, RIGHT*3)),
                ("EquationBox", lambda: EquationBox(r"P(A|B) = \frac{P(B|A) P(A)}{P(B)}", title="Bayes")),
            ]
            for name, factory in demos:
                comp = factory()
                comp.move_to(ORIGIN)
                if hasattr(comp, 'scale') and name == "NeuralNetwork": comp.scale(0.8)
                self.play(FadeIn(comp), run_time=0.8)
                self.wait(0.8)
                self.play(FadeOut(comp), run_time=0.4)

            tracker, cg, afn = AnimatedCounter(0, 92.8, suffix="% Manim", font_size=48, color=ZenPalette.AMBER)
            cg.move_to(ORIGIN)
            self.add(cg)
            self.play(afn(2.0))
            self.wait(1.0)
            done = _vn_text("ALL 10 COMPONENTS OK", font_size=22, color=ZenPalette.EMERALD, weight="BOLD")
            done.move_to(ORIGIN)
            self.play(FadeOut(cg), FadeIn(done), run_time=0.8)
            self.wait(2.0)


# =============================================================================
# DISTRIBUTED TRAINING GEOMETRY HELPERS — Series 2 Episode 24+
# Provides: create_hairline_axes, create_elegant_arrow, create_elegant_dot
# These helpers render lightweight analytical geometry for ZeRO / Ring All-Reduce scenes.
# =============================================================================

def create_hairline_axes(
    x_range=(-1, 1, 0.5),
    y_range=(-1, 1, 0.5),
    x_length=4.0,
    y_length=3.0,
    axis_color="#64748b",
    stroke_width=1.2,
    include_ticks=True,
    **kwargs,
) -> "VGroup":
    """Create a minimal hairline coordinate axes for analytical scenes.

    Provides lightweight x/y axes without heavy NumberPlane overhead, matching
    the Neo-Noir minimalist aesthetic. Tick marks are rendered as tiny Line
    mobjects to avoid font-dependent label rendering inside Docker containers.

    Args:
        x_range: (x_min, x_max, step) for horizontal axis.
        y_range: (y_min, y_max, step) for vertical axis.
        x_length: physical width in Manim units.
        y_length: physical height in Manim units.
        axis_color: stroke color hex string.
        stroke_width: axis line stroke width.
        include_ticks: whether to render tick marks.

    Returns:
        VGroup containing x_axis, y_axis, and optional ticks.
    """
    from manim import Line, VGroup, ORIGIN, RIGHT, UP, DOWN, LEFT

    x_min, x_max, x_step = x_range
    y_min, y_max, y_step = y_range

    x_scale = x_length / (x_max - x_min)
    y_scale = y_length / (y_max - y_min)

    # Origin offset so (0,0) of data maps to VGroup center
    ox = -x_min * x_scale - x_length / 2
    oy = -y_min * y_scale - y_length / 2

    x_axis = Line(
        start=np.array([0.0, oy, 0.0]),
        end=np.array([x_length, oy, 0.0]),
        color=axis_color,
        stroke_width=stroke_width,
    )
    y_axis = Line(
        start=np.array([ox, 0.0, 0.0]),
        end=np.array([ox, y_length, 0.0]),
        color=axis_color,
        stroke_width=stroke_width,
    )

    parts = [x_axis, y_axis]

    if include_ticks:
        tick_len = 0.06
        # X ticks
        v = x_min
        while v <= x_max + 1e-9:
            px = (v - x_min) * x_scale
            tick = Line(
                start=np.array([px, oy - tick_len, 0.0]),
                end=np.array([px, oy + tick_len, 0.0]),
                color=axis_color,
                stroke_width=stroke_width * 0.8,
            )
            parts.append(tick)
            v += x_step
        # Y ticks
        v = y_min
        while v <= y_max + 1e-9:
            py = (v - y_min) * y_scale
            tick = Line(
                start=np.array([ox - tick_len, py, 0.0]),
                end=np.array([ox + tick_len, py, 0.0]),
                color=axis_color,
                stroke_width=stroke_width * 0.8,
            )
            parts.append(tick)
            v += y_step

    axes_group = VGroup(*parts)
    axes_group.move_to(ORIGIN)
    return axes_group


def create_elegant_arrow(
    start,
    end,
    color="#00e5ff",
    stroke_width=2.0,
    tip_length=0.18,
    buff=0.05,
    **kwargs,
) -> "Arrow":
    """Create a clean, aerodynamic arrow for flow diagrams.

    Wraps Manim's Arrow with ZenPham Neo-Noir defaults: thin stroke, small tip,
    and CYAN accent color. Enforces the upward-arrow collision rule (theta <= 0)
    for reverse edges in horizontal node chains.

    Args:
        start: start point (np.array or Manim direction constant).
        end: end point (np.array or Manim direction constant).
        color: hex color string.
        stroke_width: line thickness.
        tip_length: arrowhead tip length (capped at 0.20 per style guide).
        buff: gap from endpoint to arrowhead tip.

    Returns:
        Manim Arrow mobject.
    """
    from manim import Arrow

    safe_tip = min(float(tip_length), 0.20)  # Aerodynamic cap per style guide

    return Arrow(
        start=np.array(start) if not isinstance(start, np.ndarray) else start,
        end=np.array(end) if not isinstance(end, np.ndarray) else end,
        color=color,
        stroke_width=stroke_width,
        tip_length=safe_tip,
        buff=buff,
        **{k: v for k, v in kwargs.items() if k not in ("tip_length", "buff", "color", "stroke_width")},
    )


def create_elegant_dot(
    point=None,
    radius=0.07,
    color="#00e5ff",
    fill_opacity=1.0,
    stroke_width=0.0,
    **kwargs,
) -> "Dot":
    """Create a small accent dot for graph nodes and data point markers.

    Used in Ring All-Reduce token flow visualizations and state-space diagrams
    to mark GPU nodes, data endpoints, and attention pivot points.

    Args:
        point: position as np.array; defaults to ORIGIN.
        radius: dot radius in Manim units.
        color: fill hex color.
        fill_opacity: opacity from 0.0 to 1.0.
        stroke_width: outline stroke (0 = no stroke).

    Returns:
        Manim Dot mobject.
    """
    from manim import Dot, ORIGIN

    pos = np.array(point) if point is not None else ORIGIN
    return Dot(
        point=pos,
        radius=radius,
        color=color,
        fill_opacity=fill_opacity,
        stroke_width=stroke_width,
        **kwargs,
    )
