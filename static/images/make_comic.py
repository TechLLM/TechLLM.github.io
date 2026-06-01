#!/usr/bin/env python3
"""Make a 4-cut comic panel image for Threads (PIL-based, not AI-generated)."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = "/Users/noah/.openclaw/workspace-techllm/static/images/neuro-growth-threads-comic.png"
W, H = 1024, 1536
BG = "#0B1020"
PANEL_BG = "#111827"
BORDER = "#38BDF8"
ACCENT = "#A78BFA"
TEXT_COLOR = "#F9FAFB"
PANEL_H = H // 4 - 16
PAD = 20

font_paths = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
]
def font(size):
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

panel_data = [
    ("2025 신경과학", "어디로?"),
    ("AI + 계산신경과학", "부상"),
    ("시스템 신경과학", "확장"),
    ("신경면역학", "뇌-면역 접점"),
]

for i, (title, sub) in enumerate(panel_data):
    y = i * (PANEL_H + PAD) + PAD
    # Panel background
    draw.rounded_rectangle([PAD, y, W-PAD, y+PANEL_H], radius=20, fill=PANEL_BG)
    # Border
    draw.rounded_rectangle([PAD, y, W-PAD, y+PANEL_H], radius=20, outline=BORDER, width=3)
    # Panel number circle
    cx, cy = PAD+60, y+PANEL_H//2
    draw.ellipse([cx-30, cy-30, cx+30, cy+30], fill=ACCENT)
    draw.text((cx, cy), str(i+1), font=font(36), fill="#FFFFFF", anchor="mm")
    # Title
    draw.text((PAD+110, y+PANEL_H//2-50), title, font=font(44), fill=TEXT_COLOR)
    # Subtitle
    draw.text((PAD+110, y+PANEL_H//2+10), sub, font=font(32), fill=BORDER)
    # Simple brain/network icon (circles)
    bx, by = W-150, y+PANEL_H//2
    for dx, dy in [(-40,0),(40,0),(0,-35),(0,35),(-25,-25)]:
        draw.ellipse([bx+dx-12, by+dy-12, bx+dx+12, by+dy+12], fill=ACCENT)
    draw.ellipse([bx-18, by-18, bx+18, by+18], fill=BORDER)

# Footer
draw.text((W//2, H-30), "#신경과학 #AI #계산신경과학 #신경면역학 #시스템신경과학",
          font=font(22), fill="#94A3B8", anchor="mm")

img.save(OUT, "PNG")
print(f"Saved: {OUT}")
