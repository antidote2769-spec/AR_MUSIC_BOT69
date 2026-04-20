import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL
from AxiomMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

ACCENT = (230, 200, 120)  # golden tone like your image


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    WIDTH, HEIGHT = 1280, 720
    base = Image.new("RGB", (WIDTH, HEIGHT), (15, 25, 30))

    font_title = ImageFont.truetype("AxiomMusic/assets/font2.ttf", 42)
    font_artist = ImageFont.truetype("AxiomMusic/assets/font.ttf", 28)

    # ─────────────
    # 🌌 BACKGROUND (REALISTIC)
    # ─────────────
    bg = Image.open(raw_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(35))

    # teal tone
    overlay = Image.new("RGB", (WIDTH, HEIGHT), (0, 60, 70))
    bg = Image.blend(bg, overlay, 0.4)

    # center light glow
    glow = Image.new("L", (WIDTH, HEIGHT), 0)
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((200, 100, 1100, 650), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(200))

    light = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    bg = Image.composite(light, bg, glow)

    bg = ImageEnhance.Brightness(bg).enhance(0.7)

    base.paste(bg, (0, 0))
    draw = ImageDraw.Draw(base)

    # ─────────────
    # 🎬 THUMB WITH SHADOW
    # ─────────────
    thumb = Image.open(raw_path).resize((800, 400), Image.LANCZOS)
    thumb = ImageEnhance.Sharpness(thumb).enhance(1.3)

    thumb_x, thumb_y = 250, 120

    # shadow layer
    shadow = Image.new("RGBA", (820, 420), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((10, 10, 810, 410), 40, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    base.paste(shadow, (thumb_x-10, thumb_y-10), shadow)

    # rounded thumb
    mask = rounded_mask((800, 400), 40)
    base.paste(thumb, (thumb_x, thumb_y), mask)

    # ─────────────
    # 🔲 BORDER (GLOW STYLE)
    # ─────────────
    box = (thumb_x, thumb_y, thumb_x + 800, thumb_y + 400)

    # outer glow
    for i in range(6):
        draw.rounded_rectangle(
            (box[0]-i, box[1]-i, box[2]+i, box[3]+i),
            radius=40,
            outline=(ACCENT[0], ACCENT[1], ACCENT[2], 40),
            width=2
        )

    # main border
    draw.rounded_rectangle(box, radius=40, outline=ACCENT, width=3)

    # ─────────────
    # ⏱️ PROGRESS BAR
    # ─────────────
    try:
        parts = duration_text.split(":")
        total_sec = int(parts[0]) * 60 + int(parts[1])
    except:
        total_sec = 100

    current_sec = int(total_sec * 0.15)

    bar_x = 140
    top = 100
    bottom = 620

    draw.line((bar_x, top, bar_x, bottom), fill=(200, 200, 200, 120), width=4)

    progress_y = bottom - int((bottom - top) * (current_sec / total_sec))

    draw.line((bar_x, progress_y, bar_x, bottom), fill=ACCENT, width=4)

    # 🔴 DOT WITH SHADOW
    for i in range(3):
        draw.ellipse(
            (bar_x-8-i, progress_y-8-i, bar_x+8+i, progress_y+8+i),
            fill=(ACCENT[0], ACCENT[1], ACCENT[2], 40)
        )

    draw.ellipse((bar_x-6, progress_y-6, bar_x+6, progress_y+6), fill=ACCENT)

    # ─────────────
    # 🕒 TIME TEXT
    # ─────────────
    def fmt(sec):
        m = sec // 60
        s = sec % 60
        return f"{m:02}:{s:02}"

    draw.text((85, 60), fmt(current_sec), fill=ACCENT, font=font_artist)
    draw.text((85, 640), duration_text, fill=ACCENT, font=font_artist)

    # ─────────────
    # 📝 TEXT
    # ─────────────
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = current + " " + word if current else word
            bbox = draw.textbbox((0, 0), test, font=font)
            w = bbox[2] - bbox[0]

            if w <= max_width:
                current = test
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines[:2]

    title = re.sub(r"\W+", " ", title)

    text_x = 300
    text_y = 550

    lines = wrap_text(title, font_title, 700)

    for i, line in enumerate(lines):
        draw.text((text_x, text_y + i * 50), line, fill="white", font=font_title)

    draw.text(
        (text_x, text_y + len(lines) * 50 + 5),
        channel[:35],
        fill=(200, 200, 200),
        font=font_artist,
    )

    # 👇 DEV TEXT UPDATED
    draw.text((1050, 650), "Dev :- Maanav", fill=(220, 220, 220), font=font_artist)

    # ─────────────
    # FINAL
    # ─────────────
    base = ImageEnhance.Contrast(base).enhance(1.05)
    base.save(cache_path, quality=95)

    return cache_path
