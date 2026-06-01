#!/usr/bin/env python3
"""Make Instagram cardnews slides (PIL-based)."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = "/Users/noah/.openclaw/workspace-techllm/static/images"
W, H = 1080, 1350
BG = "#0B1020"
CARD_BG = "#111827"
BORDER = "#1E293B"
ACCENT = "#38BDF8"
ACCENT2 = "#A78BFA"
TEXT = "#F9FAFB"
MUTED = "#94A3B8"

font_paths = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
]
def font(size):
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

slides = [
    {
        "eyebrow": "POINT 01",
        "title_lines": ["신경과학에서", "가장 빠르게", "커지는 분야들"],
        "body_lines": ["AI, 계산신경과학, 시스템신경과학,"],
        "body_lines2": ["신경면역학, 자연행동연구"],
        "type": "cover"
    },
    {
        "eyebrow": "AI + 계산신경과학",
        "title_lines": ["뇌를 시뮬레이션하는", "AI 연구자들"],
        "body_lines": ["AI가 신경망을 학습하면서", "뇌 구조를 역추적하는 분야"],
        "type": "point"
    },
    {
        "eyebrow": "시스템 신경과학",
        "title_lines": ["뇌를 단독이 아닌", "네트워크에서 연구"],
        "body_lines": ["신경망을 개별 뉴런이 아닌", "집합적 시스템으로 바라봄"],
        "type": "point"
    },
    {
        "eyebrow": "자연행동 연구",
        "title_lines": ["Cage 없는 환경에서", "뇌 활동을 관찰"],
        "body_lines": ["자연스러운 움직임 속", "진짜 뇌 신호를 포착"],
        "type": "point"
    },
    {
        "eyebrow": "신경면역학 + 결론",
        "title_lines": ["뇌-면역 접점,", "새로운 연구 fronteira"],
        "body_lines": ["면역과 뇌의 교차점에서", "새로운 치료 가능성 등장"],
        "url": "techllm.github.io/posts/fastest-growing-areas-in-neuroscience",
        "type": "cta"
    },
]

for idx, slide in enumerate(slides):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    pad = 60
    card = [pad, pad, W-pad, H-pad]

    draw.rounded_rectangle(card, radius=36, fill=CARD_BG)
    draw.ellipse([W-200, -50, W+100, 200], fill=ACCENT2+"30")
    draw.ellipse([-80, H-250, 180, H+50], fill=ACCENT+"25")
    draw.rounded_rectangle(card, radius=36, outline=BORDER, width=2)

    # Eyebrow
    draw.text((pad+50, pad+45), slide["eyebrow"].upper(), font=font(24), fill=ACCENT)
    brand = "TechLLM"
    bw = draw.textlength(brand, font=font(22))
    draw.text((W-pad-50-bw, pad+47), brand, font=font(22), fill=MUTED)

    # Title
    title_font_size = 58 if slide["type"] == "cover" else 46
    title_y = pad + 120
    for li, line in enumerate(slide["title_lines"]):
        ly = title_y + li * (title_font_size + 12)
        lw = draw.textlength(line, font=font(title_font_size))
        lx = (W - lw) // 2 if slide["type"] == "cover" else pad + 50
        draw.text((lx, ly), line, font=font(title_font_size), fill=TEXT)

    # Body
    body_y = title_y + len(slide["title_lines"]) * (title_font_size + 12) + 20
    for li, line in enumerate(slide["body_lines"]):
        draw.text((pad+50, body_y + li*38), line, font=font(28), fill=MUTED)
    if "body_lines2" in slide:
        for li, line in enumerate(slide["body_lines2"]):
            draw.text((pad+50, body_y + (len(slide["body_lines"])+li)*38), line, font=font(28), fill=MUTED)
    if "url" in slide:
        url_y = body_y + (len(slide["body_lines"])+len(slide.get("body_lines2",[]))+1)*38
        draw.text((pad+50, url_y), "▶ " + slide["url"], font=font(22), fill=ACCENT)

    # Bottom tag
    tag = "#신경과학 #AI #계산신경과학 #신경면역학 #시스템신경과학 #뇌과학"
    tw = draw.textlength(tag, font=font(20))
    draw.text(((W-tw)//2, H-pad-45), tag, font=font(20), fill=MUTED+"99")

    fname = f"{OUT_DIR}/neuro-growth-ig-slide{idx+1}.png"
    img.save(fname, "PNG")
    print(f"Saved: {fname}")
