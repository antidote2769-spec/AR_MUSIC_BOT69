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

# 🎯 PURPLE UI (same as your sample)
ACCENT = (160, 140, 255)


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
    # 🌌 CINEMATIC BACKGROUND (EXACT STYLE)
    # ─────────────
    bg = Image.open(raw_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)

    bg = bg.filter(ImageFilter.GaussianBlur(40))

    overlay = Image.new("RGB", (WIDTH, HEIGHT), (0, 50, 65))
    bg = Image.blend(bg, overlay, 0.45)

    # center glow
    glow = Image.new("L", (WIDTH, HEIGHT), 0)
    g = ImageDraw.Draw(glow)
    g.ellipse((200, 100, 1100, 650), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(220))

    light = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    bg = Image.composite(light, bg, glow)

    bg = ImageEnhance.Brightness(bg).enhance(0.7)

    base.paste(bg, (0, 0))
    draw = ImageDraw.Draw(base)

    # ─────────────
    # 🧊 GLASS CARD
    # ─────────────
    card = bg.crop((200, 80, 1080, 620)).filter(ImageFilter.GaussianBlur(25))

    glass = Image.new("RGBA", card.size, (255, 255, 255, 25))
    card = Image.alpha_composite(card.convert("RGBA"), glass)

    # shadow
    shadow = Image.new("RGBA", (card.size[0]+40, card.size[1]+40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((20, 20, card.size[0]+20, card.size[1]+20),
                         50, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))

    base.paste(shadow, (180, 60), shadow)

    mask = rounded_mask(card.size, 50)
    base.paste(card, (200, 80), mask)

    draw = ImageDraw.Draw(base)

    # ─────────────
    # 🎬 THUMB (RADIUS = 50 🔥)
    # ─────────────
    thumb = Image.open(raw_path).resize((760, 380), Image.LANCZOS)
    thumb = ImageEnhance.Sharpness(thumb).enhance(1.3)

    tx, ty = 240, 120

    # shadow
    tshadow = Image.new("RGBA", (780, 400), (0, 0, 0, 0))
    sd = ImageDraw.Draw(tshadow)
    sd.rounded_rectangle((10, 10, 770, 390),
                         50, fill=(0, 0, 0, 150))
    tshadow = tshadow.filter(ImageFilter.GaussianBlur(25))

    base.paste(tshadow, (tx-10, ty-10), tshadow)

    tmask = rounded_mask((760, 380), 50)  # 👈 RADIUS 50
    base.paste(thumb, (tx, ty), tmask)

    # ─────────────
    # 🔮 PURPLE GLOW BORDER
    # ─────────────
    for i in range(8):
        draw.rounded_rectangle(
            (tx-i, ty-i, tx+760+i, ty+380+i),
            radius=50,
            outline=(ACCENT[0], ACCENT[1], ACCENT[2], 30),
            width=2
        )

    draw.rounded_rectangle(
        (tx, ty, tx+760, ty+380),
        radius=50,
        outline=ACCENT,
        width=3
    )

    # ─────────────
    # ⏱️ PROGRESS BAR (WITH GLOW DOT)
    # ─────────────
    try:
        parts = duration_text.split(":")
        total_sec = int(parts[0]) * 60 + int(parts[1])
    except:
        total_sec = 100

    current_sec = int(total_sec * 0.15)

    bar_x = 130
    top, bottom = 110, 610

    draw.line((bar_x, top, bar_x, bottom),
              fill=(200, 200, 200, 100), width=4)

    py = bottom - int((bottom-top) * (current_sec/total_sec))

    draw.line((bar_x, py, bar_x, bottom),
              fill=ACCENT, width=4)

    # glow dot
    for i in range(4):
        draw.ellipse(
            (bar_x-8-i, py-8-i, bar_x+8+i, py+8+i),
            fill=(ACCENT[0], ACCENT[1], ACCENT[2], 40)
        )

    draw.ellipse((bar_x-6, py-6, bar_x+6, py+6), fill=ACCENT)

    # ─────────────
    # 🕒 TIME
    # ─────────────
    def fmt(sec):
        return f"{sec//60:02}:{sec%60:02}"

    draw.text((80, 60), fmt(current_sec), fill=ACCENT, font=font_artist)
    draw.text((80, 640), duration_text, fill=ACCENT, font=font_artist)

    # ─────────────
    # 📝 TEXT
    # ─────────────
    def wrap(text):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = cur + " " + w if cur else w
            if draw.textlength(test, font=font_title) < 700:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines[:2]

    title = re.sub(r"\W+", " ", title)

    tx2, ty2 = 300, 540

    for i, line in enumerate(wrap(title)):
        draw.text((tx2, ty2 + i*50), line,
                  fill="white", font=font_title)

    draw.text((tx2, ty2 + 110),
              channel[:35],
              fill=(200, 200, 200),
              font=font_artist)

    # DEV TEXT
    draw.text((1020, 650),
              "Dev :- Maanav",
              fill=(220, 220, 220),
              font=font_artist)

    base = ImageEnhance.Contrast(base).enhance(1.08)
    base.save(cache_path, quality=95)

    return cache_path


# ─────────────────────────────
# 🚀 MAIN FUNCTION (FIXED)
# ─────────────────────────────
async def get_thumb(videoid: str, player_username: str = None):

    if player_username is None:
        player_username = app.username

    cache_path = os.path.join(CACHE_DIR, f"{videoid}.png")
    if os.path.exists(cache_path):
        return cache_path

    try:
        results = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        search = await results.next()
        data = search["result"][0]

        title = data["title"]
        channel = data["channel"]["name"]
        duration = data.get("duration", "0:00")
        thumb_url = data["thumbnails"][0]["url"]

    except Exception as e:
        print("SEARCH ERROR:", e)
        return YOUTUBE_IMG_URL

    raw_path = os.path.join(CACHE_DIR, f"{videoid}.jpg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(raw_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        return YOUTUBE_IMG_URL

    try:
        result = _make_thumb(
            raw_path, title, channel, duration, player_username, cache_path
        )
    except Exception as e:
        print("THUMB ERROR:", e)
        return YOUTUBE_IMG_URL

    if os.path.exists(raw_path):
        os.remove(raw_path)

    return result
