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


# ─────────────────────────────
# 🎨 THUMBNAIL RENDER
# ─────────────────────────────
def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    base = Image.open("AxiomMusic/assets/template.png").convert("RGBA")
    WIDTH, HEIGHT = base.size
    draw = ImageDraw.Draw(base)

    # Fonts
    font_title = ImageFont.truetype("AxiomMusic/assets/font2.ttf", 44)
    font_artist = ImageFont.truetype("AxiomMusic/assets/font.ttf", 28)

    # ─────────────
    # 🎨 BACKGROUND BLUR (🔥 UPDATED)
    # ─────────────
    try:
        bg = Image.open(raw_path).convert("RGBA").resize((WIDTH, HEIGHT))

        # 🔥 Strong blur
        bg = bg.filter(ImageFilter.GaussianBlur(45))

        # 🎨 Color boost (song colors highlight)
        bg = ImageEnhance.Color(bg).enhance(1.8)

        # 🌑 Dark overlay (glass effect)
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 140))
        bg = Image.alpha_composite(bg, overlay)

        # Merge with template
        base = Image.alpha_composite(bg, base)

    except Exception as e:
        print("BG ERROR:", e)

    draw = ImageDraw.Draw(base)

    # ─────────────
    # 🎵 ALBUM ART
    # ─────────────
    try:
        ART_SIZE = 230

        art = Image.open(raw_path).resize((ART_SIZE, ART_SIZE))

        mask = Image.new("L", (ART_SIZE, ART_SIZE), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, ART_SIZE, ART_SIZE), 45, fill=255
        )

        art_x = 155
        art_y = 405

        base.paste(art, (art_x, art_y), mask)

    except Exception as e:
        print("ART ERROR:", e)

    # ─────────────
    # 📝 TEXT WRAP
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

    text_x = 460
    text_y = 400
    max_width = 700

    lines = wrap_text(title, font_title, max_width)

    for i, line in enumerate(lines):
        draw.text((text_x, text_y + i * 50), line, fill="white", font=font_title)

    # channel name
    draw.text(
        (text_x, text_y + len(lines) * 48 + 8),
        channel[:35],
        fill=(200, 200, 200),
        font=font_artist,
    )

    # ─────────────
    # ✨ FINAL TOUCH
    # ─────────────
    base = ImageEnhance.Contrast(base).enhance(1.05)
    base = ImageEnhance.Sharpness(base).enhance(1.25)

    base.convert("RGB").save(cache_path)

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
