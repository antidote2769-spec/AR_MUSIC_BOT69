import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL
from AxiomMusic import app

# cache folder
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


# ─────────────────────────────
# 🎨 THUMBNAIL RENDER
# ─────────────────────────────
def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    from PIL import Image, ImageDraw, ImageFont, ImageEnhance

    base = Image.open("AxiomMusic/assets/template.png").convert("RGBA")
    draw = ImageDraw.Draw(base)

    # fonts
    font_title = ImageFont.truetype("AxiomMusic/assets/font2.ttf", 42)
    font_artist = ImageFont.truetype("AxiomMusic/assets/font.ttf", 26)
    font_time = ImageFont.truetype("AxiomMusic/assets/font.ttf", 20)

    # ─────────────
    # 🎵 ALBUM IMAGE (FIXED POSITION)
    # ─────────────
    try:
        art = Image.open(raw_path).resize((160, 160))

        mask = Image.new("L", (160, 160), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0,0,160,160), 28, fill=255)

        base.paste(art, (155, 300), mask)
    except:
        pass

    # ─────────────
    # 📝 TITLE (FIXED POSITION)
    # ─────────────
    title = re.sub(r"\W+", " ", title)
    draw.text((380, 260), title[:28], fill="white", font=font_title)

    # ─────────────
    # 👤 CHANNEL
    # ─────────────
    draw.text((380, 315), channel[:30], fill=(210,210,210), font=font_artist)

    # ─────────────
    # ⏱ TIME (ONLY ONE BAR)
    # ─────────────
    draw.text((380, 380), "0:00", fill=(180,180,180), font=font_time)
    draw.text((720, 380), duration_text, fill=(180,180,180), font=font_time)

    # ─────────────
    # 🔊 VOLUME KNOB (PERFECT)
    # ─────────────
    from PIL import ImageFilter

    vx = 1115
    vy = 360

    glow = Image.new("RGBA", base.size, (0,0,0,0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((vx-14, vy-14, vx+14, vy+14), fill=(255,255,255,100))
    base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(8)))

    draw = ImageDraw.Draw(base)
    draw.ellipse((vx-10, vy-10, vx+10, vy+10), fill=(200,200,200))
    draw.ellipse((vx-5, vy-5, vx+5, vy+5), fill=(255,255,255))

    # ─────────────
    # ✨ SHARPNESS
    # ─────────────
    base = ImageEnhance.Sharpness(base).enhance(1.5)

    base.convert("RGB").save(cache_path)
    return cache_path


# ─────────────────────────────
# 🚀 MAIN FUNCTION (IMPORTANT)
# ─────────────────────────────
async def get_thumb(videoid: str, player_username: str = None):

    if player_username is None:
        player_username = app.username

    cache_path = os.path.join(CACHE_DIR, f"{videoid}.png")

    if os.path.exists(cache_path):
        return cache_path

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        search = await results.next()

        data = search["result"][0]

        title = data["title"]
        channel = data["channel"]["name"]
        duration = data.get("duration", "0:00")

        thumb_url = data["thumbnails"][0]["url"]

    except Exception:
        return YOUTUBE_IMG_URL

    # download thumbnail
    raw_path = os.path.join(CACHE_DIR, f"{videoid}.jpg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(raw_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception:
        return YOUTUBE_IMG_URL

    # render image
    result = _make_thumb(raw_path, title, channel, duration, player_username, cache_path)

    try:
        os.remove(raw_path)
    except:
        pass

    return result
