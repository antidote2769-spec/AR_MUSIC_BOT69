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

    W, H = 1280, 720

    base = Image.new("RGB", (W, H), (30, 35, 45))
    draw = ImageDraw.Draw(base)

    REG  = "AxiomMusic/assets/font.ttf"
    BOLD = "AxiomMusic/assets/font2.ttf"

    f_title = _font(BOLD, 60)
    f_artist = _font(REG, 40)
    f_time = _font(REG, 28)

    # ─── ALBUM ───
    try:
        art = Image.open(raw_path).convert("RGB").resize((400, 400))
        mask = Image.new("L", (400, 400), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 400, 400), radius=40, fill=255)
        base.paste(art, (100, 160), mask)
    except:
        pass

    # ─── TEXT ───
    draw.text((550, 220), title, fill="white", font=f_title)
    draw.text((550, 300), channel, fill=(200, 200, 200), font=f_artist)

    # ─── DURATION ───
    draw.text((550, 380), f"Duration: {duration_text}", fill=(180, 180, 180), font=f_time)

    base.save(cache_path)
    return cache_path

# ─────────────────────────────────────────────
# 🚀 MAIN FUNCTION (ASYNC FIXED)
# ─────────────────────────────────────────────
async def get_thumb(videoid: str, player_username: str = None):

    if player_username is None:
        player_username = app.username

    cache_path = os.path.join(CACHE_DIR, f"{videoid}.png")
    if os.path.exists(cache_path):
        return cache_path

    # ─── FETCH DATA ───
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        search = await results.next()

        data = search.get("result", [])[0]

        title = re.sub(r"\W+", " ", data.get("title", "Unknown")).strip().title()
        thumb_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        channel = data.get("channel", {}).get("name", "YouTube")

    except Exception:
        title, thumb_url, duration, channel = "Unknown", YOUTUBE_IMG_URL, None, "YouTube"

    duration_text = duration if duration else "LIVE"

    # ─── DOWNLOAD THUMB ───
    raw_path = os.path.join(CACHE_DIR, f"raw_{videoid}.jpg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(raw_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except:
        return YOUTUBE_IMG_URL

    # ─── GENERATE ───
    try:
        result = _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path)
    except:
        result = YOUTUBE_IMG_URL

    # cleanup
    try:
        os.remove(raw_path)
    except:
        pass

    return result
