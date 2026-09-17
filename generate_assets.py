#!/usr/bin/env python3
"""
Generate PRISM Swiss-Archival Favicons, App Icons, and Open Graph Social Cards.
Uses Pillow with supersampled vector geometry for razor-sharp antialiasing.
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def render_prism_icon(target_size):
    """Render square icon with supersampling for crisp edges at any resolution."""
    scale = 4
    dim = target_size * scale
    img = Image.new('RGBA', (dim, dim), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = int(dim * 0.12)
    # Background squary rounded rect (Archival Burgundy #8B1A1A)
    draw.rounded_rectangle([0, 0, dim - 1, dim - 1], radius=radius, fill=(139, 26, 26, 255))

    # Inner subtle technical border
    border_offset = max(1, int(dim * 0.016))
    border_w = max(1, int(dim * 0.008))
    draw.rounded_rectangle(
        [border_offset, border_offset, dim - 1 - border_offset, dim - 1 - border_offset],
        radius=radius - border_offset,
        outline=(250, 246, 238, 65),
        width=border_w
    )

    # Prism Triangle Coordinates
    top = (dim * 0.50, dim * 0.22)
    left = (dim * 0.22, dim * 0.74)
    right = (dim * 0.78, dim * 0.74)

    # Triangular Glass Fill
    draw.polygon([top, left, right], fill=(250, 246, 238, 30))

    # Incident White Beam striking left facet
    beam_w = max(2, int(dim * 0.048))
    hit_y = dim * 0.52
    t = (hit_y - top[1]) / (left[1] - top[1])
    hit_x = top[0] + t * (left[0] - top[0])
    draw.line([(dim * 0.07, dim * 0.38), (hit_x, hit_y)], fill=(250, 246, 238, 255), width=beam_w)

    # 3 Spectral Refracted Beams (Coral, Amber, Cyan)
    colors = [
        (255, 123, 114, 255),  # Coral / Red #FF7B72
        (246, 193, 119, 255),  # Amber / Gold #F6C177
        (156, 207, 216, 255)   # Cyan / Teal #9CCFD8
    ]
    exit_ys = [dim * 0.47, dim * 0.53, dim * 0.59]
    end_ys = [dim * 0.37, dim * 0.53, dim * 0.69]

    for i, col in enumerate(colors):
        ey = exit_ys[i]
        et = (ey - top[1]) / (right[1] - top[1])
        ex = top[0] + et * (right[0] - top[0])
        # Internal dispersion path
        draw.line([(hit_x, hit_y), (ex, ey)], fill=(250, 246, 238, 110), width=max(1, int(beam_w * 0.55)))
        # Emerging spectral ray
        draw.line([(ex, ey), (dim * 0.94, end_ys[i])], fill=col, width=max(2, int(beam_w * 0.75)))

    # Prism Triangle Outline
    tri_stroke = max(2, int(dim * 0.045))
    draw.polygon([top, left, right], outline=(250, 246, 238, 255), width=tri_stroke)

    # Optical center guideline
    draw.line([top, (dim * 0.50, dim * 0.74)], fill=(250, 246, 238, 80), width=max(1, int(dim * 0.012)))

    # Downsample with Lanczos for super-smooth rendering
    return img.resize((target_size, target_size), Image.Resampling.LANCZOS)


def generate_og_image():
    """Generate 1200x630 Swiss-Archival social sharing card."""
    width, height = 1200, 630
    img = Image.new('RGB', (width, height), (232, 224, 208))  # #E8E0D0
    draw = ImageDraw.Draw(img)

    # Grid lines (archival blueprint)
    grid_col = (216, 207, 191)
    for x in range(0, width, 60):
        draw.line([(x, 0), (x, height)], fill=grid_col, width=1)
    for y in range(0, height, 60):
        draw.line([(0, y), (width, y)], fill=grid_col, width=1)

    # Left accent band (burgundy)
    draw.rectangle([0, 0, 14, height], fill=(139, 26, 26))

    # Outer border & Registration marks
    draw.rectangle([36, 36, width - 36, height - 36], outline=(191, 182, 166), width=2)
    for cx, cy in [(36, 36), (width - 36, 36), (36, height - 36), (width - 36, height - 36)]:
        draw.line([(cx - 12, cy), (cx + 12, cy)], fill=(139, 26, 26), width=2)
        draw.line([(cx, cy - 12), (cx, cy + 12)], fill=(139, 26, 26), width=2)

    # Load system TTF fonts
    font_mono = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf', 16)
    font_mono_small = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf', 13)
    font_title = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 108)
    font_sub = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 30)
    font_desc = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 20)

    # Top Header Metadata
    draw.text((72, 64), '[ ARCHIVE DISPATCH // REF: PRISM-SWISS-ARCHIVE-V2 ]', font=font_mono, fill=(122, 112, 104))
    draw.text((850, 64), 'STATUS: REAL-TIME ONLINE', font=font_mono, fill=(139, 26, 26))

    # Main Brand & Subtitle
    draw.text((72, 116), 'PRISM', font=font_title, fill=(42, 37, 32))
    draw.text((72, 238), 'DIGITAL ARCHIVE BULLETIN', font=font_sub, fill=(139, 26, 26))

    # Description
    desc1 = 'High-density chronological record of global intelligence signals'
    desc2 = 'synthesizing real-time feeds, independent journalism, and specialized telemetry.'
    draw.text((72, 296), desc1, font=font_desc, fill=(74, 66, 59))
    draw.text((72, 328), desc2, font=font_desc, fill=(74, 66, 59))

    # Bottom Information Ledger Box
    box_top, box_bottom = 412, 560
    draw.rectangle([72, box_top, width - 72, box_bottom], fill=(239, 233, 220), outline=(205, 196, 180), width=1)
    draw.rectangle([72, box_top, 80, box_bottom], fill=(139, 26, 26))

    draw.text((100, box_top + 16), 'INDEX COVERAGE', font=font_mono_small, fill=(122, 112, 104))
    draw.text((100, box_top + 38), 'TECH · EDAN · AI · POLITICS · DISASTER · SCIENCE · WORLD · BUSINESS · CULTURE', font=font_mono_small, fill=(42, 37, 32))

    draw.text((100, box_top + 80), 'SYSTEM SPECIFICATION', font=font_mono_small, fill=(122, 112, 104))
    draw.text((100, box_top + 102), 'FAST-CACHED REDIS + SQLITE DUAL-TIER // SWISS-ARCHIVAL UI // WP MRSS V2.0', font=font_mono_small, fill=(42, 37, 32))

    draw.text((820, box_top + 80), 'CANONICAL ACCESS', font=font_mono_small, fill=(122, 112, 104))
    draw.text((820, box_top + 102), 'PRISM.GLASSGALLERY.MY.ID', font=font_mono_small, fill=(139, 26, 26))

    # Large Vector Prism Graphic on the Right
    icon_512 = render_prism_icon(220)
    img.paste(icon_512, (width - 320, 110), icon_512)

    return img


def main():
    print("[AssetGen] Building PRISM Swiss-Archival icon suite...")

    # 1. Favicon sizes
    icon_512 = render_prism_icon(512)
    icon_512.save(os.path.join(BASE_DIR, 'android-chrome-512x512.png'))
    print(" -> android-chrome-512x512.png")

    icon_192 = render_prism_icon(192)
    icon_192.save(os.path.join(BASE_DIR, 'android-chrome-192x192.png'))
    print(" -> android-chrome-192x192.png")

    icon_180 = render_prism_icon(180)
    icon_180.save(os.path.join(BASE_DIR, 'apple-touch-icon.png'))
    print(" -> apple-touch-icon.png")

    icon_32 = render_prism_icon(32)
    icon_32.save(os.path.join(BASE_DIR, 'favicon-32x32.png'))
    print(" -> favicon-32x32.png")

    icon_16 = render_prism_icon(16)
    icon_16.save(os.path.join(BASE_DIR, 'favicon-16x16.png'))
    print(" -> favicon-16x16.png")

    # 2. Multi-resolution favicon.ico
    icon_512.save(
        os.path.join(BASE_DIR, 'favicon.ico'),
        format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48)]
    )
    print(" -> favicon.ico (16x16, 32x32, 48x48)")

    # 3. Open Graph Social Card
    og_card = generate_og_image()
    og_card.save(os.path.join(BASE_DIR, 'og-image.png'))
    print(" -> og-image.png (1200x630)")

    print("[AssetGen] Done! All visual assets compiled successfully.")


if __name__ == '__main__':
    main()
