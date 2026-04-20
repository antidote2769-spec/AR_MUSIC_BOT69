import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL
from AxiomMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

TEMPLATE_PATH = "AxiomMusic/assets/template.png"

# 🎯 COLOR (same as template – adjust if needed)
ACCENT = (180, 180, 180)


# ─────────────────────────────
# 🎨 THUMB RENDER (TEMPLATE BASED)
# ─────────────────────────────
def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    WIDTH, HEIGHT = 1280, 720

    base = Image.open(TEMPLATE_PATH).convert("RGB").resize((WIDTH, HEIGHT))
    draw = ImageDraw.Draw(base)

    font_title = ImageFont.truetype("AxiomMusic/assets/font2.ttf", 40)
    font_artist = ImageFont.truetype("AxiomMusic/assets/font.ttf", 26)

    # ─────────────
    # 🎬 THUMB (INSIDE TEMPLATE BOX)
    # ─────────────
    thumb = Image.open(raw_path).resize((760, 380))

    # 👇 adjust if needed (perfect match template)
    thumb_x, thumb_y = 260, 130

    base.paste(thumb, (thumb_x, thumb_y))

    # ─────────────
    # ⏱️ PROGRESS BAR
    # ─────────────
    try:
        m, s = map(int, duration_text.split(":"))
        total_sec = m * 60 + s
    except:
        total_sec = 100

    current_sec = int(total_sec * 0.15)

    bar_x = 110
    top = 120
    bottom = 600

    draw.line((bar_x, top, bar_x, bottom), fill=(180, 180, 180), width=4)

    py = bottom - int((bottom - top) * (current_sec / total_sec))

    draw.line((bar_x, py, bar_x, bottom), fill=ACCENT, width=4)

    draw.ellipse((bar_x-7, py-7, bar_x+7, py+7), fill=ACCENT)

    # ─────────────
    # 🕒 TIME
    # ─────────────
    def fmt(sec):
        return f"{sec//60:02}:{sec%60:02}"

    draw.text((60, 70), fmt(current_sec), fill=ACCENT, font=font_artist)
    draw.text((60, 640), duration_text, fill=ACCENT, font=font_artist)

    # ─────────────
    # 📝 TEXT
    # ─────────────
    def wrap(text, max_width=750):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = cur + " " + w if cur else w
            if draw.textlength(test, font=font_title) <= max_width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines[:2]

    title = re.sub(r"\W+", " ", title)

    text_x = 300
    text_y = 560

    for i, line in enumerate(wrap(title)):
        draw.text((text_x, text_y + i*45), line, fill="white", font=font_title)

    draw.text(
        (text_x, text_y + 95),
        channel[:35],
        fill=ACCENT,
        font=font_artist,
    )

    # ─────────────
    # 💧 WATERMARK
    # ─────────────
    draw.text(
        (1000, 650),
        "Dev :- Maanav",
        fill=(220, 220, 220),
        font=font_artist,
    )

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
