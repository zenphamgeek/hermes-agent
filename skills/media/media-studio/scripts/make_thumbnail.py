#!/usr/bin/env python3
"""make_thumbnail.py — Generate branded thumbnails from AI-generated images.

Overlays headline text and ZENPHAM brand watermark onto hero images,
then exports resized versions for each platform.

Usage:
    python make_thumbnail.py \
        --image hero.png \
        --headline "Vibe Coding là gì?" \
        --output-dir /tmp/media-studio/ \
        [--brand ZENPHAM]

Output files:
    thumb_yt.jpg  — 1280x720 (YouTube)
    thumb_fb.jpg  — 1200x630 (Facebook)
    thumb_x.jpg   — 1600x900 (X/Twitter)
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print(json.dumps({
        "status": "error",
        "error": "Pillow not installed. Run: uv pip install Pillow"
    }))
    sys.exit(1)


# Platform dimensions
PLATFORMS = {
    "yt": (1280, 720),
    "fb": (1200, 630),
    "x": (1600, 900),
}

# Brand colors
BRAND_COLORS = {
    "ZENPHAM": {
        "text": "#FFFFFF",
        "shadow": "#000000",
        "accent": "#00D4FF",
        "watermark": "#FFFFFF",
    },
    "Inteligent Silos": {
        "text": "#FFFFFF",
        "shadow": "#000000",
        "accent": "#7C3AED",
        "watermark": "#FFFFFF",
    },
}


def _find_font(size: int):
    """Find a suitable font, falling back to default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    # Fallback to default
    try:
        return ImageFont.truetype("DejaVuSans-Bold", size)
    except Exception:
        return ImageFont.load_default()


def _draw_text_with_shadow(draw, position, text, font, fill, shadow_color, shadow_offset=3):
    """Draw text with drop shadow for readability."""
    x, y = position
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def _wrap_text(text: str, font, max_width: int, draw) -> list:
    """Word-wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def create_thumbnail(image_path: str, headline: str, output_dir: str, brand: str = "ZENPHAM"):
    """Create branded thumbnails for all platforms."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load source image
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Cannot open image: {e}"}))
        sys.exit(1)

    colors = BRAND_COLORS.get(brand, BRAND_COLORS["ZENPHAM"])
    results = {}

    for platform, (w, h) in PLATFORMS.items():
        # Resize and crop to target dimensions
        thumb = img.copy()

        # Calculate crop to match aspect ratio
        src_ratio = thumb.width / thumb.height
        dst_ratio = w / h

        if src_ratio > dst_ratio:
            # Source is wider — crop sides
            new_w = int(thumb.height * dst_ratio)
            left = (thumb.width - new_w) // 2
            thumb = thumb.crop((left, 0, left + new_w, thumb.height))
        else:
            # Source is taller — crop top/bottom
            new_h = int(thumb.width / dst_ratio)
            top = (thumb.height - new_h) // 2
            thumb = thumb.crop((0, top, thumb.width, top + new_h))

        thumb = thumb.resize((w, h), Image.LANCZOS)

        # Add gradient overlay at bottom for text readability
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        # Bottom gradient (dark)
        gradient_height = h // 3
        for i in range(gradient_height):
            alpha = int(200 * (i / gradient_height))
            y = h - gradient_height + i
            draw_overlay.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

        # Top gradient (subtle)
        for i in range(h // 6):
            alpha = int(100 * (1 - i / (h // 6)))
            draw_overlay.line([(0, i), (w, i)], fill=(0, 0, 0, alpha))

        thumb_rgba = thumb.convert("RGBA")
        thumb_rgba = Image.alpha_composite(thumb_rgba, overlay)
        thumb = thumb_rgba.convert("RGB")

        draw = ImageDraw.Draw(thumb)

        # Draw headline text
        font_size = int(h * 0.08)  # ~8% of height
        font = _find_font(font_size)
        max_text_width = int(w * 0.85)

        lines = _wrap_text(headline, font, max_text_width, draw)

        # Position text at bottom-left
        line_height = font_size + 8
        total_text_height = len(lines) * line_height
        text_y = h - total_text_height - int(h * 0.08)
        text_x = int(w * 0.05)

        for line in lines:
            _draw_text_with_shadow(
                draw, (text_x, text_y), line, font,
                fill=colors["text"], shadow_color=colors["shadow"], shadow_offset=3
            )
            text_y += line_height

        # Draw brand watermark (bottom-right)
        wm_font_size = int(h * 0.04)
        wm_font = _find_font(wm_font_size)
        wm_text = brand
        wm_bbox = draw.textbbox((0, 0), wm_text, font=wm_font)
        wm_w = wm_bbox[2] - wm_bbox[0]
        wm_x = w - wm_w - int(w * 0.03)
        wm_y = h - int(h * 0.06)
        draw.text((wm_x, wm_y), wm_text, font=wm_font, fill=colors["watermark"])

        # Draw accent bar
        accent_y = h - int(h * 0.015)
        draw.rectangle([(0, accent_y), (w, h)], fill=colors["accent"])

        # Save
        output_path = output_dir / f"thumb_{platform}.jpg"
        thumb.save(str(output_path), "JPEG", quality=95)
        results[platform] = str(output_path)

    print(json.dumps({"status": "ok", "thumbnails": results}))
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate branded thumbnails")
    parser.add_argument("--image", required=True, help="Path to hero image")
    parser.add_argument("--headline", required=True, help="Headline text to overlay")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--brand", default="ZENPHAM", help="Brand name")
    args = parser.parse_args()

    create_thumbnail(args.image, args.headline, args.output_dir, args.brand)


if __name__ == "__main__":
    main()
