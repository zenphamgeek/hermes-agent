# Master Pillar 3: Visual Geometry, Borderless Canvas & Manim Standards

> **Authority**: Kiến Trúc Sư Visual Không Biên Giới (Borderless Canvas & Geometric Layout Architect).  
> **Target**: All Manim Community Scripts (2K QHD 16:9 & 9:16 Vertical) across Content Factory.

---

## 1. Rule 29: Zero-Card-Box-Background & Borderless Canvas Invariant

All Manim scripts and visual pipelines across all Content Factory channels and series MUST COMPLETELY ELIMINATE colored card box background containers (no `RoundedRectangle` or `Rectangle` with `fill_color=COLOR_CARD_BG`, `fill_opacity > 0` behind text, tables, or telemetry HUDs).

### Architectural Rationale
- Because Manim lacks an automated flexbox / CSS bounding engine, static-sized card boxes inevitably cause element overflow, text collisions, border clipping, and visual amateurism.
- All text, tables, and mathematical formulas must float directly on the pristine **Neo-Noir Obsidian canvas** (`#080a0f` / `#0c0d12`), structured cleanly via:
  1. **Typography Hierarchy**: Hero Title in Cyan (`#38bdf8`), Core Proof in Gold (`#ffd700`), Secondary details in White (`#ffffff`) and Slate (`#94a3b8`).
  2. **Open Grid Coordinates**: Calculated coordinate anchors (`safe_place`, open column grids).
  3. **Delicate Hairlines & Whitespace**: Subtle lines (`StrokeWidth = 1.0`, opacity $0.3$) instead of clunky bounding cards.

---

## 2. Rule 27: Local Object Rotation & Fixed 2D Frame (No Camera Sway)

In all 3D scenes (such as `ThreeDScene` surface loss manifolds, saddle points, or multi-dimensional vector spaces):
- **Rock-Solid Canvas & HUD**: Canvas 2D, Header HUD, and Channel Logo MUST stand completely motionless like bedrock.
- **Mandatory Fixed Frame**: Every 2D element (titles, HUD telemetry, corner logos) must be registered with:
  ```python
  self.add_fixed_in_frame_mobjects(title, telemetry_hud, channel_logo)
  ```
- **Local Rotation Only**: Whole-canvas camera rotation (`begin_ambient_camera_rotation`) is **STRICTLY FORBIDDEN**. All 3D rotations must be executed locally on geometric mobjects:
  ```python
  self.play(Rotate(surface_group, angle=PI / 3, axis=OUT, run_time=6.0))
  ```

---

## 3. Continuous Motion Geometry (0 Anti-Slide-Deck Violations)

- **Zero Slide-Decks**: No scene may ever consist of a bulleted list of static text or cards.
- **Mathematical Dominance ($\ge 75\%$)**: Mathematical curves, vector arrows, manifolds, coordinate systems, or dynamic particle simulations must dominate $\ge 75\%$ of the screen at all times.
- **3-4 Staged Beats**: Every scene progresses through distinct visual stages in tight synchronization with spoken narration.
- **3 Visual Metaphors**: Every blueprint must specify 3 unique Visual Metaphors, each with:
  - *Part A*: Mathematical & Physical Foundations.
  - *Part B*: 4-Phase Continuous Motion Progression (Birth $\to$ Evolution $\to$ Climax $\to$ Transformation).

---

## 4. 2K QHD Safe Zones

### 16:9 Longform Cinema ($2560 \times 1440$ @ 60fps)
- **Top-Right Channel Logo**: $X \in [5.20, 6.80], Y \in [2.80, 3.80]$ reserved 100% for ZenPham logo mark.
- **Bottom Subtitle CC Corridor**: $Y \in [-4.00, -2.00]$ kept completely clear of telemetry, graphs, or formula annotations.
- **Left Hero Stage (58% Trái)**: $X \in [-6.20, +0.60]$ for primary geometric motion.
- **Right Telemetry Sidebar (42% Phải)**: $X \in [+0.90, +5.50]$ for borderless telemetry parameters.

### 9:16 Vertical Shorts ($1440 \times 2560$ @ 60fps)
- **3-Tier Vertical Architecture**:
  - *Zone 1 (Top, $Y \in [4.5, 6.5]$)*: Paradox Hook Title (displayed $\ge 2.5$s).
  - *Zone 2 (Center, $Y \in [-1.5, 4.0]$)*: Dynamic Mathematical Hero.
  - *Zone 3 (Bottom, $Y \in [-6.0, -2.0]$)*: Gold SRT Karaoke Subtitles.
- **Strict Safe Boundaries**:
  - Right Edge: $X \le 3.1$ (avoids YouTube vertical action buttons: Like, Comment, Share, Remix).
  - Bottom Edge: $Y \ge -6.2$ (avoids YouTube channel avatar, audio title, and control bar).

---

## 5. Manim Gold Standard: Voice-Sync Full-Duration Animation & Zero-Static-Hold Invariant

All Manim scenes across Masterclass and Shorts MUST strictly adhere to the **Manim Gold Standard**:
1. **Full-Duration Convergence**: Total animation runtime $T_{\text{anim}} = \sum (\text{run\_time} + \text{wait})$ of each scene must closely match the exact spoken voiceover duration $T_{\text{audio}}$:
   $$T_{\text{audio}} - T_{\text{anim}} \in [0.5\text{s}, 2.0\text{s}]$$
   The visual presentation must stay alive and kinetically active throughout the entire spoken segment, ending with only a gentle $0.5\text{s} - 1.5\text{s}$ pause before the scene transition.
2. **Zero-Static-Hold Invariant**: Generating short 5–10s animations and freezing the frame for 30–60s via video assembler padding (`tpad > 3.0s`) or long dead `self.wait(> 3.0s)` is **STRICTLY AND ABSOLUTELY FORBIDDEN**.
3. **Multi-Beat Kinetic Progression**: Each scene must be choreographed into 4 to 6 continuous staged narrative beats corresponding to the sentences in the spoken script:
   - *Phase 1 (Hook/Premise)*: Coordinate genesis, telemetry initialization, initial problem state.
   - *Phase 2 (Tension/Conflict)*: Emergence of anomaly, mathematical paradox, outlier shock, or baseline failure.
   - *Phase 3 (Mathematical Proof & Mechanism)*: Dynamic curve morphing, probe motion, calculus tangent sliding, formula transformation.
   - *Phase 4 (Climax/Synthesis)*: Geometric convergence, valley illumination, trade-off revelation.
   - *Phase 5 (Philosophical Bridge)*: Telemetry seal, insight crystallization, preparation for the next cognitive step.

