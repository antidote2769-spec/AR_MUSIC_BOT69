import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL
from AxiomMusic import app

# CACHE
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# FONT LOADER
def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

# ─────────────────────────────────────────────
# 🎨 SIMPLE CLEAN THUMB (stable)
# ─────────────────────────────────────────────
def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    W, H = 1280, 720

    REG  = "AxiomMusic/assets/font.ttf"
    BOLD = "AxiomMusic/assets/font2.ttf"

    f_title = _font(BOLD, 56)
    f_artist = _font(REG, 36)
    f_time = _font(REG, 28)

    # ───── BACKGROUND (GRADIENT + BLUR) ─────
    try:
        bg = Image.open(raw_path).convert("RGB").resize((W, H))
    except:
        bg = Image.new("RGB", (W, H), (30, 30, 30))

    bg = bg.filter(ImageFilter.GaussianBlur(40))

    overlay = Image.new("RGBA", (W, H), (10, 15, 25, 180))
    base = Image.alpha_composite(bg.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(base)

    # ───── GLASS CARD ─────
    cx, cy = 140, 140
    CW, CH = 1000, 440

    card = Image.new("RGBA", (CW, CH), (25, 30, 40, 230))
    mask = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,CW,CH), radius=50, fill=255)

    # shadow
    shadow = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (cx+15, cy+15, cx+CW+15, cy+CH+15),
        radius=50,
        fill=(0,0,0,120)
    )
    base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(25)))

    base.paste(card, (cx, cy), mask)

    draw = ImageDraw.Draw(base)

    # ───── ALBUM IMAGE ─────
    try:
        art = Image.open(raw_path).convert("RGB").resize((360, 360))
        m = Image.new("L", (360, 360), 0)
        ImageDraw.Draw(m).rounded_rectangle((0,0,360,360), radius=40, fill=255)
        base.paste(art, (cx+40, cy+40), m)
    except:
        pass

    # ───── TEXT ─────
    tx = cx + 440

    draw.text((tx, cy+80), _trim(title, f_title, 520), fill="white", font=f_title)
    draw.text((tx, cy+170), channel, fill=(200,200,200), font=f_artist)

    # ───── PROGRESS BAR ─────
    px1, px2 = tx, tx + 420
    py = cy + 260

    draw.line((px1, py, px2, py), fill=(120,120,120), width=6)
    draw.line((px1, py, px1+200, py), fill=(255,255,255), width=6)
    draw.ellipse((px1+200-8, py-8, px1+200+8, py+8), fill="white")

    draw.text((px1, py+20), "0:00", font=f_time, fill=(180,180,180))
    draw.text((px2-60, py+20), duration_text, font=f_time, fill=(180,180,180))

    # ───── CONTROLS ─────
    cy2 = cy + 330

    # prev
    draw.polygon([(tx+40, cy2), (tx+60, cy2-12), (tx+60, cy2+12)], fill="white")
    draw.rectangle((tx+30, cy2-12, tx+35, cy2+12), fill="white")

    # play/pause
    draw.ellipse((tx+100, cy2-20, tx+140, cy2+20), fill=(255,255,255))
    draw.rectangle((tx+115, cy2-10, tx+120, cy2+10), fill=(0,0,0))
    draw.rectangle((tx+125, cy2-10, tx+130, cy2+10), fill=(0,0,0))

    # next
    draw.polygon([(tx+180, cy2), (tx+160, cy2-12), (tx+160, cy2+12)], fill="white")
    draw.rectangle((tx+185, cy2-12, tx+190, cy2+12), fill="white")

    # ───── BRAND ─────
    draw.text((W-260, H-60), "@AxiomMusic", fill=(160,160,160), font=f_time)

    # ───── SAVE ─────
    base.convert("RGB").save(cache_path, "PNG")
    return cache_path
