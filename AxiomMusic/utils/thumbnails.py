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

ACCENT = (170, 150, 255)  # purple tone


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    WIDTH, HEIGHT = 1280, 720

    # 📌 TEMPLATE LOAD (your uploaded one)
    base = Image.open("AxiomMusic/assets/template.png").convert("RGB")
    base = base.resize((WIDTH, HEIGHT))

    draw = ImageDraw.Draw(base)

    font_title = ImageFont.truetype("AxiomMusic/assets/font2.ttf", 38)
    font_artist = ImageFont.truetype("AxiomMusic/assets/font.ttf", 32)

    # ─────────────
    # 🎬 THUMB (FIT + LESS RADIUS)
    # ─────────────
    thumb = Image.open(raw_path).resize((760, 360), Image.LANCZOS)

    # 📌 position tuned to your template
    thumb_x, thumb_y = 260, 135

    # ❗ radius reduced (50 → 30)
    radius = 30

    # shadow (same rounded)
    shadow = Image.new("RGBA", (780, 380), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((10, 10, 770, 370), radius, fill=(0, 0, 0, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))

    base.paste(shadow, (thumb_x - 10, thumb_y - 10), shadow)

    # thumb paste
    mask = rounded_mask((760, 360), radius)
    base.paste(thumb, (thumb_x, thumb_y), mask)

    # ─────────────
    # ⏱️ TIME TEXT (BIGGER + TEMPLATE COLOR)
    # ─────────────
    def fmt(sec):
        return f"{sec//60:02}:{sec%60:02}"

    try:
        parts = duration_text.split(":")
        total_sec = int(parts[0]) * 60 + int(parts[1])
    except:
        total_sec = 100

    current_sec = int(total_sec * 0.15)

    # 📌 positions adjusted to template
    draw.text((70, 70), fmt(current_sec), fill=ACCENT, font=font_artist)
    draw.text((70, 640), duration_text, fill=ACCENT, font=font_artist)

    # ─────────────
    # 📝 TITLE
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

    text_x, text_y = 300, 560  # 👈 thoda niche

    for i, line in enumerate(wrap(title)):
        draw.text((text_x, text_y + i * 48), line, fill="white", font=font_title)

    draw.text(
        (text_x, text_y + 100),
        channel[:35],
        fill=(200, 200, 200),
        font=font_artist,
    )

    # ─────────────
    # 🏷️ DEV TEXT
    # ─────────────
    draw.text((1020, 650), "Dev :- Maanav", fill=(200, 200, 200), font=font_artist)

    base.save(cache_path, quality=95)
    return cache_path


# ─────────────────────────────
# 🚀 MAIN FUNCTION
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
