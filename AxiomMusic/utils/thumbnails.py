import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL
from AxiomMusic import app

# ══════════════════════════════════════════════════════════════════
#  CACHE
# ══════════════════════════════════════════════════════════════════
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  CANVAS
# ══════════════════════════════════════════════════════════════════
W, H = 1280, 720

# ══════════════════════════════════════════════════════════════════
#  COLORS — pixel-scanned from reference image
# ══════════════════════════════════════════════════════════════════
BG_TOP         = ( 18,  27,  34)   # top-left background
BG_BOT         = ( 28,  37,  46)   # bottom background
TEXT_WHITE     = (254, 254, 254)   # song title color
ARTIST_GREY    = (212, 212, 212)   # artist name (slightly grey-white)
PLAYING_GREY   = (131, 138, 146)   # "Playing" label
DURATION_GREY  = (179, 180, 182)   # "Duration: …" text
BRAND_GREY     = (160, 165, 171)   # "Powered by …" text
CARD_BG        = (  0,   4,   6)   # card fill when no art

# ══════════════════════════════════════════════════════════════════
#  CARD GEOMETRY — pixel-scanned (1920x1080 source → 1280x720 output)
#  Source: left=180, right=828, top=220, bottom=898
#  Scale:  1280/1920 = 0.6667,  720/1080 = 0.6667
# ══════════════════════════════════════════════════════════════════
CARD_X   = 120   # 180  × 0.6667
CARD_Y   = 146   # 220  × 0.6667
CARD_R   = 552   # 828  × 0.6667
CARD_B   = 598   # 898  × 0.6667
CARD_RAD =  20   # rounded corner radius

# ══════════════════════════════════════════════════════════════════
#  TEXT POSITIONS — pixel-scanned from source, scaled to 1280x720
#  Playing: source y=347, x=905
#  Title:   source y=451, x=905
#  Artist:  source y=588, x=905
#  Duration:source y=667, x=905
#  Brand:   source y=971 / 1010, x=1626
# ══════════════════════════════════════════════════════════════════
TX        = 603   # 905 × 0.6667 — shared left x for all text
TY_LABEL  = 231   # "Playing" top
TY_TITLE  = 300   # Song title top
TY_ARTIST = 392   # Artist name top
TY_DUR    = 444   # Duration top
BRAND_Y1  = 647   # "Powered" line top
BRAND_Y2  = 673   # "by <name>" line top

# ══════════════════════════════════════════════════════════════════
#  FONT SIZES — derived from pixel heights in reference
#  Playing: rendered h=36px → ~32pt
#  Title:   rendered h=66px → ~62pt
#  Artist:  rendered h=24px → ~44pt (bold renders larger)
#  Duration:rendered h=24px → ~28pt
# ══════════════════════════════════════════════════════════════════
SZ_PLAYING  = 32
SZ_TITLE    = 62
SZ_ARTIST   = 44
SZ_DURATION = 28
SZ_BRAND    = 22

# ══════════════════════════════════════════════════════════════════
#  WAVE — bottom-right lighter bump
#  BG_BOT first appears at y=530 on right, y=556 on left
#  Large ellipse: bounding box tuned to match this curve
# ══════════════════════════════════════════════════════════════════
WAVE_ELLIPSE = (150, 420, 1380, 820)   # (x0,y0,x1,y1) bounding box


# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────
def _trim(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    try:
        if font.getlength(text) <= max_w:
            return text
        for i in range(len(text) - 1, 0, -1):
            t = text[:i] + "…"
            if font.getlength(t) <= max_w:
                return t
    except Exception:
        pass
    return text[:12] + "…"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════════
#  CORE RENDERER
# ═══════════════════════════════════════════════════════════════════
def _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path):

    from PIL import Image, ImageDraw, ImageFilter

    W, H = 1280, 720

    REG  = "AxiomMusic/assets/font.ttf"
    BOLD = "AxiomMusic/assets/font2.ttf"

    f_title = _font(BOLD, 44)
    f_artist = _font(REG, 26)
    f_time = _font(REG, 20)

    # ───── BACKGROUND ─────
    base = Image.new("RGBA", (W, H), (235, 235, 235))

    # ───── CARD POSITION ─────
    cx, cy = 320, 230
    CW, CH = 640, 260

    # ───── SHADOW ─────
    shadow = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (cx+12, cy+12, cx+CW+12, cy+CH+12),
        radius=45,
        fill=(0,0,0,100)
    )
    base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(25)))

    # ───── CARD (SMOOTH GRADIENT) ─────
    card = Image.new("RGBA", (CW, CH))
    cd = ImageDraw.Draw(card)

    for y in range(CH):
        shade = int(75 - (y/CH)*35)
        cd.line([(0,y),(CW,y)], fill=(shade,shade,shade))

    mask = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,CW,CH), radius=45, fill=255)
    base.paste(card, (cx, cy), mask)

    draw = ImageDraw.Draw(base)

    # ───── VINYL DISC (REALISTIC) ─────
    vcx, vcy = cx + CW//2, cy - 70

    for r in range(120, 20, -6):
        col = 20 + (r % 20)
        draw.ellipse((vcx-r, vcy-r, vcx+r, vcy+r), outline=(col,col,col), width=2)

    draw.ellipse((vcx-120, vcy-120, vcx+120, vcy+120), fill=(25,25,25))
    draw.ellipse((vcx-20, vcy-20, vcx+20, vcy+20), fill=(10,10,10))

    # ───── LEFT ALBUM ─────
    try:
        art = Image.open(raw_path).convert("RGB").resize((120,120))
        m = Image.new("L", (120,120), 0)
        ImageDraw.Draw(m).rounded_rectangle((0,0,120,120), radius=25, fill=255)
        base.paste(art, (cx-80, cy+60), m)
    except:
        pass

    # ───── RIGHT KNOB (REALISTIC) ─────
    kx, ky = cx + CW + 60, cy + CH//2

    knob = Image.new("RGBA", (160,160), (0,0,0,0))
    kd = ImageDraw.Draw(knob)

    kd.ellipse((0,0,160,160), fill=(40,40,40))
    kd.ellipse((20,20,140,140), fill=(220,220,220))
    kd.ellipse((50,50,110,110), fill=(180,180,180))

    knob = knob.filter(ImageFilter.GaussianBlur(1))
    base.paste(knob, (kx-80, ky-80), knob)

    draw = ImageDraw.Draw(base)

    # ───── TEXT ─────
    draw.text((cx+120, cy+40), "Pray For Me", fill=(255,255,255), font=f_title)
    draw.text((cx+120, cy+95), channel, fill=(200,200,200), font=f_artist)

    # ───── PROGRESS BAR ─────
    px1, px2 = cx+120, cx+520
    py = cy + 150

    draw.line((px1, py, px2, py), fill=(170,170,170), width=3)
    draw.ellipse((px1+200-7, py-7, px1+200+7, py+7), fill=(255,255,255))

    draw.text((px1, py-30), "2:26", font=f_time, fill=(220,220,220))
    draw.text((px2-45, py-30), duration_text, font=f_time, fill=(220,220,220))

    # ───── CONTROLS (REAL SHAPES) ─────
    cy2 = cy + 210

    # shuffle
    draw.line((cx+200, cy2, cx+220, cy2-10), fill="white", width=2)
    draw.line((cx+200, cy2, cx+220, cy2+10), fill="white", width=2)

    # prev
    draw.polygon([(cx+260, cy2), (cx+280, cy2-12), (cx+280, cy2+12)], fill="white")
    draw.rectangle((cx+245, cy2-12, cx+250, cy2+12), fill="white")

    # pause
    draw.rectangle((cx+310, cy2-12, cx+316, cy2+12), fill="white")
    draw.rectangle((cx+322, cy2-12, cx+328, cy2+12), fill="white")

    # next
    draw.polygon([(cx+380, cy2), (cx+360, cy2-12), (cx+360, cy2+12)], fill="white")
    draw.rectangle((cx+385, cy2-12, cx+390, cy2+12), fill="white")

    # repeat
    draw.arc((cx+430, cy2-15, cx+460, cy2+15), 0, 300, fill="white", width=2)

    # ───── GREEN CHECK ─────
    draw.ellipse((cx+520, cy+40, cx+560, cy+80), fill=(40,200,90))
    draw.text((cx+533, cy+45), "✓", fill="white", font=f_artist)

    # ───── SAVE ─────
    base.convert("RGB").save(cache_path, "PNG")
    return cache_path

    # Fetch YouTube metadata
    try:
        results   = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        search    = await results.next()
        data      = search.get("result", [])[0]
        title     = re.sub(r"\W+", " ", data.get("title", "Unknown")).strip().title()
        thumb_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration  = data.get("duration")
        channel   = data.get("channel", {}).get("name", "YouTube")
    except Exception:
        title, thumb_url, duration, channel = "Unknown", YOUTUBE_IMG_URL, None, "YouTube"

    is_live       = not duration or str(duration).lower() in {"live", "live now", ""}
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    # Download art
    raw_path = os.path.join(CACHE_DIR, f"raw_{videoid}.jpg")
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

    # Render
    try:
        result = _make_thumb(raw_path, title, channel, duration_text, player_username, cache_path)
    except Exception:
        result = YOUTUBE_IMG_URL

    try:
        os.remove(raw_path)
    except Exception:
        pass

    return result
