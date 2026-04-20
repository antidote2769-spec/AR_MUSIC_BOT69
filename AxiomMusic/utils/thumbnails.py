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

ACCENT = (230, 200, 120)


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


# ─────────────────────────────
# 🎨 THUMB RENDER
# ─────────────────────────────
def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    WIDTH, HEIGHT = 1280, 720
    base = Image.new("RGB", (WIDTH, HEIGHT), (15, 25, 30))

    font_title = ImageFont.truetype("AxiomMusic/assets/font2.ttf", 42)
    font_artist = ImageFont.truetype("AxiomMusic/assets/font.ttf", 28)

    # 🌌 BACKGROUND
    bg = Image.open(raw_path).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(35))

    overlay = Image.new("RGB", (WIDTH, HEIGHT), (0, 60, 70))
    bg = Image.blend(bg, overlay, 0.4)

    glow = Image.new("L", (WIDTH, HEIGHT), 0)
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((200, 100, 1100, 650), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(200))

    light = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    bg = Image.composite(light, bg, glow)

    bg = ImageEnhance.Brightness(bg).enhance(0.7)
    base.paste(bg, (0, 0))

    draw = ImageDraw.Draw(base)

    # 🎬 THUMB
    thumb = Image.open(raw_path).resize((800, 400), Image.LANCZOS)
    thumb = ImageEnhance.Sharpness(thumb).enhance(1.3)

    thumb_x, thumb_y = 250, 120

    # shadow
    shadow = Image.new("RGBA", (820, 420), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((10, 10, 810, 410), 40, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    base.paste(shadow, (thumb_x-10, thumb_y-10), shadow)

    mask = rounded_mask((800, 400), 40)
    base.paste(thumb, (thumb_x, thumb_y), mask)

    # 🔲 BORDER
    box = (thumb_x, thumb_y, thumb_x + 800, thumb_y + 400)

    for i in range(6):
        draw.rounded_rectangle(
            (box[0]-i, box[1]-i, box[2]+i, box[3]+i),
            radius=40,
            outline=(ACCENT[0], ACCENT[1], ACCENT[2], 40),
            width=2
        )

    draw.rounded_rectangle(box, radius=40, outline=ACCENT, width=3)

    # ⏱️ PROGRESS BAR
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

    # dot shadow
    for i in range(3):
        draw.ellipse(
            (bar_x-8-i, progress_y-8-i, bar_x+8+i, progress_y+8+i),
            fill=(ACCENT[0], ACCENT[1], ACCENT[2], 40)
        )

    draw.ellipse((bar_x-6, progress_y-6, bar_x+6, progress_y+6), fill=ACCENT)

    # 🕒 TIME
    def fmt(sec):
        m = sec // 60
        s = sec % 60
        return f"{m:02}:{s:02}"

    draw.text((85, 60), fmt(current_sec), fill=ACCENT, font=font_artist)
    draw.text((85, 640), duration_text, fill=ACCENT, font=font_artist)

    # 📝 TEXT
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

    # DEV
    draw.text((1050, 650), "Dev :- Maanav", fill=(220, 220, 220), font=font_artist)

    base = ImageEnhance.Contrast(base).enhance(1.05)
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
