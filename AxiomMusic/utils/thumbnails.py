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
# 🎨 THUMBNAIL RENDER (CENTERED POSITION)
# ─────────────────────────────
def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    from PIL import Image, ImageDraw, ImageFont, ImageEnhance

    # Template load karein
    base = Image.open("AxiomMusic/assets/template.png").convert("RGBA")
    draw = ImageDraw.Draw(base)

    # fonts
    font_title = ImageFont.truetype("AxiomMusic/assets/font2.ttf", 45)
    font_artist = ImageFont.truetype("AxiomMusic/assets/font.ttf", 30)
    font_time = ImageFont.truetype("AxiomMusic/assets/font.ttf", 22)

    # ─────────────
    # 🎵 ALBUM IMAGE (BOX KE BEECH MEIN)
    # ─────────────
    try:
        # Poster ka size box ke hisaab se 190x190 set kiya hai
        art = Image.open(raw_path).resize((190, 190))

        mask = Image.new("L", (190, 190), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 190, 190), 35, fill=255)

        # Poster coordinates: (138, 435) 
        # Yeh poster ko us side box ke bilkul center mein le aayega
        base.paste(art, (138, 435), mask)
    except Exception as e:
        print(f"Error drawing art: {e}")
        pass

    # ─────────────
    # 📝 TITLE & CHANNEL (NICHE SHIFT KIYA)
    # ─────────────
    title = re.sub(r"\W+", " ", title)
    # Title aur Channel ko bhi niche kiya hai taaki vinyl se na takraye
    draw.text((450, 420), title[:25], fill="white", font=font_title)
    draw.text((450, 480), channel[:30], fill=(200, 200, 200), font=font_artist)

    # ─────────────
    # ⏱️ TIME POSITION
    # ─────────────
    draw.text((450, 545), "0:00", fill=(180, 180, 180), font=font_time)
    draw.text((1080, 545), duration_text, fill=(180, 180, 180), font=font_time)

    # ─────────────
    # 🔊 VOLUME KNOB
    # ─────────────
    from PIL import ImageFilter
    vx, vy = 1115, 360 # Template ke hisaab se volume knob
    glow = Image.new("RGBA", base.size, (0,0,0,0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((vx-14, vy-14, vx+14, vy+14), fill=(255,255,255,100))
    base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(8)))
    draw = ImageDraw.Draw(base)
    draw.ellipse((vx-10, vy-10, vx+10, vy+10), fill=(200,200,200))

    # ─────────────
    # ✨ FINAL TOUCH & SAVE
    # ─────────────
    base = ImageEnhance.Sharpness(base).enhance(1.3)
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
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        search = await results.next()
        data = search["result"][0]
        title = data["title"]
        channel = data["channel"]["name"]
        duration = data.get("duration", "0:00")
        thumb_url = data["thumbnails"][0]["url"]
    except:
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
    except:
        return YOUTUBE_IMG_URL

    result = _make_thumb(raw_path, title, channel, duration, player_username, cache_path)
    if os.path.exists(raw_path):
        os.remove(raw_path)
    return result
