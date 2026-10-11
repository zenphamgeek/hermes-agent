# Video Motion Studio — Animation & Graphic Specifications

## 1. Canvas Dimensions & Aspect Ratios
- **Landscape (YouTube Long-form / Desktop)**: 1920x1080 (16:9), 24/30/60 fps.
- **Portrait (Shorts / Reels / TikTok)**: 1080x1920 (9:16), 30/60 fps.
- **Square (Social Feeds)**: 1080x1080 (1:1), 30 fps.

## 2. Cyberpunk & Deep-Tech Color Palette
- **Deep Backgrounds**: Dark Slate `#0F172A`, Obsidian Navy `#0A0F1D`, Deep Cyber `#030712`.
- **Primary Accents**: Electric Cyan `#00F0FF`, Neon Blue `#38BDF8`, Cyber Purple `#A855F7`.
- **Warning / Highlight**: Neon Amber `#FACC15`, Neon Coral `#F43F5E`, Emerald Glow `#10B981`.
- **Text & Typography**: Pure White `#FFFFFF`, Ice White `#F8FAFC`, Steel Muted `#94A3B8`.

## 3. Motion Curves & Easing Functions
- **Standard Smooth**: `cubic-bezier(0.4, 0.0, 0.2, 1.0)` (Ease-in-out standard)
- **Deceleration (Entrances)**: `cubic-bezier(0.0, 0.0, 0.2, 1.0)` (Smooth deceleration)
- **Acceleration (Exits)**: `cubic-bezier(0.4, 0.0, 1.0, 1.0)`
- **Dynamic Bounce**: `cubic-bezier(0.34, 1.56, 0.64, 1.0)`

## 4. Key Motion Patterns
1. **Ken Burns Zoom & Pan**:
   - Zoom Range: 1.0x to 1.15x over scene duration.
   - Smooth interpolation using FFmpeg `zoompan` filter.
2. **Pulsing Neural Link / SVG Circuit**:
   - Sine-wave opacity modulation from 0.4 to 1.0 at 1.5 Hz.
   - Flowing energy particle pulses along SVG bezier paths.
3. **Glassmorphism Infographic Cards**:
   - Semi-transparent background `rgba(15, 23, 42, 0.75)`.
   - Subtle glowing border `1px solid rgba(56, 189, 248, 0.4)`.
   - Backdrop blur simulation for deep contrast.
