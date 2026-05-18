import os
import re
import random
import aiohttp
import aiofiles
import colorsys
from unidecode import unidecode
from functools import lru_cache
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter


BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS      = os.path.join(BASE_DIR, "..", "assets")
FONT_BOLD   = os.path.join(ASSETS, "f.ttf")
FONT_NORMAL = os.path.join(ASSETS, "cfont.ttf")

def clean_username(name: str) -> str:
    import unicodedata
    import re

    if not name:
        return "AxiomUser"

    # normalize
    name = unicodedata.normalize("NFKC", name)

    # fancy → normal
    decoded = unidecode(name)

    # 🔥 agar readable hai to use kar
    if re.match(r'^[A-Za-z0-9 _.-]{3,}$', decoded):
        return decoded.strip()

    # 🔥 warna soft clean
    cleaned = re.sub(r'[^A-Za-z0-9 ]+', ' ', decoded)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if len(cleaned) < 3:
        return "AxiomUser"

    return cleaned
    
# 🔥 fallback fonts (ONLY for username)
FONT_FALLBACKS = []

for file in os.listdir(ASSETS):
    if file.lower().endswith((".ttf", ".otf")):
        FONT_FALLBACKS.append(os.path.join(ASSETS, file))

# 🔥 emoji font sabse upar
emoji_font = os.path.join(ASSETS, "seguiemj.ttf")
if os.path.exists(emoji_font):
    FONT_FALLBACKS.insert(0, emoji_font)

# last fallback
FONT_FALLBACKS.append(FONT_NORMAL)

@lru_cache(maxsize=10)
def _get_fallback_fonts(size: int):
    fonts = []
    for path in FONT_FALLBACKS:
        try:
            fonts.append(ImageFont.truetype(path, size))
        except:
            continue

    if not fonts:
        fonts.append(ImageFont.load_default())

    return fonts

# ═══════════════════════════════════════════════════════════════════
# THUMBNAIL GENERATOR - VERSION 4.1 (Performance Edition)
# Fixes: removed unused numpy import, added in-memory cache guard
# ═══════════════════════════════════════════════════════════════════

W, H = 1280, 720
BG_COLOR   = (45,  60,  65)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY  = (175, 182, 188)
REQ_COLOR = (255, 215, 0)  

# In-memory set: tracks videoids already generated this session
# Prevents regenerating same thumb if cache/ file was wiped by Heroku
_thumb_memory: dict = {}  # videoid -> output_path


@lru_cache(maxsize=4)
def _get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _random_palette() -> Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]:
    # totally random hue
    h = random.random()

    # wider ranges = more variety
    s = random.uniform(0.45, 1.0)
    v = random.uniform(0.55, 1.0)

    # base main color
    base = tuple(
        int(x * 255)
        for x in colorsys.hsv_to_rgb(h, s, v)
    )

    # lighter neon-ish version
    light = tuple(
        int(x * 255)
        for x in colorsys.hsv_to_rgb(
            (h + random.uniform(0.03, 0.08)) % 1.0,
            max(0.25, s - random.uniform(0.15, 0.35)),
            min(1.0, v + random.uniform(0.12, 0.28))
        )
    )

    # darker rich shadow version
    dark = tuple(
        int(x * 255)
        for x in colorsys.hsv_to_rgb(
            (h - random.uniform(0.03, 0.08)) % 1.0,
            min(1.0, s + random.uniform(0.05, 0.18)),
            max(0.18, v - random.uniform(0.28, 0.45))
        )
    )

    return base, light, dark


def _make_bg_v4() -> Image.Image:
    base = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(base, "RGBA")
    for y in range(H):
        ratio = y / H
        draw.line([(0, y), (W, y)], fill=(0, 0, 0, int(45 * ratio)))
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for i in range(160, 0, -5):
        alpha = int(130 * (1 - i / 160))
        vd.rectangle([0, 0, W, H], outline=(0, 0, 0, alpha), width=i)
    base.paste(vignette.filter(ImageFilter.GaussianBlur(45)), (0, 0), vignette)
    return base


def _draw_card_border_v4(base: Image.Image, x1, y1, x2, y2, r=28, c_base=(202,215,221), c_light=(225,235,240), c_dark=(140,155,162)) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(38, 0, -1):
        alpha = int(95 * (1 - i / 38) ** 1.4)
        d.rounded_rectangle([x1 - i, y1 - i, x2 + i, y2 + i], radius=r + i, fill=(255, 255, 255, alpha))
    for i in range(18, 0, -1):
        d.rounded_rectangle(
            [x1 - i, y1 - i, x2 + i, y2 + i],
            radius=r + i,
            fill=(*c_base, int(75 * (1 - i / 18)))
        )
    d.rounded_rectangle([x1 + 10, y1 + 10, x2 - 10, y2 - 10], radius=max(r - 10, 4), fill=(18, 24, 26, 255))
    for offset, color, bw in [(0, (*c_dark, 255), 5), (2, (*c_base, 255), 3), (4, (255, 255, 255, 180), 2)]:
        d.rounded_rectangle([x1 + offset, y1 + offset, x2 - offset, y2 - offset], radius=max(r - offset, 4), outline=color, width=bw)
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def _draw_art_shadow(base: Image.Image, x, y, w, h, r=18, c_base=(202,215,221)) -> Image.Image:
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)

    off_x, off_y = 10, 14

    # deep black shadow
    for i in range(48, 0, -1):
        alpha = int(230 * (1 - i / 48) ** 1.3)
        sd.rounded_rectangle(
            [x+off_x-i, y+off_y-i, x+w+off_x+i, y+h+off_y+i],
            radius=r+i,
            fill=(0, 0, 0, alpha)
        )

    # outer glow
    for i in range(22, 0, -1):
        alpha = int(120 * (1 - i / 22) ** 1.6)
        sd.rounded_rectangle(
            [x-i, y-i, x+w+i, y+h+i],
            radius=r+i,
            fill=(*c_base, alpha)
        )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(22))
    return Image.alpha_composite(base.convert("RGBA"), shadow_layer).convert("RGB")


def _paste_rounded(base: Image.Image, img: Image.Image, x, y, w, h, r=18) -> Image.Image:
    img = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=r, fill=255)
    img.putalpha(mask)
    base_r = base.convert("RGBA")
    base_r.paste(img, (x, y), img)
    return base_r.convert("RGB")


def _draw_bar(base: Image.Image, bx, by_top, by_bot, progress: float = 0.06,
              c_base=(202,215,221), c_light=(225,235,240), c_dark=(140,155,162)) -> Image.Image:

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    bw = 8
    knob_y = by_top + int((by_bot - by_top) * progress)
    kr = 14

    # inactive line
    d.rounded_rectangle(
        [(bx - bw//2, by_top), (bx + bw//2, by_bot)],
        radius=4,
        fill=(131, 141, 147, 255)
    )

    # active line
    if knob_y > by_top:
        d.rounded_rectangle(
            [(bx - bw//2, by_top), (bx + bw//2, knob_y)],
            radius=4,
            fill=(*c_base, 255)
        )

    # glow rings
    d.ellipse(
        [(bx - kr - 16, knob_y - kr - 16),
         (bx + kr + 16, knob_y + kr + 16)],
        fill=(*c_base, 35)
    )

    d.ellipse(
        [(bx - kr - 9, knob_y - kr - 9),
         (bx + kr + 9, knob_y + kr + 9)],
        fill=(*c_base, 70)
    )

    # main knob
    d.ellipse(
        [(bx - kr, knob_y - kr),
         (bx + kr, knob_y + kr)],
        fill=(*c_base, 255)
    )

    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def _truncate(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w: return text
    while text and draw.textlength(text + "…", font=font) > max_w: text = text[:-1]
    return text + "…"


async def get_thumb(videoid: str, user_name: str = "Unknown") -> str:
    output = f"cache/{videoid}.png"
    cache  = f"cache/thumb{videoid}.jpg"
    os.makedirs("cache", exist_ok=True)

    # 1) Already generated this session (in-memory, survives even if file missing)
    if videoid in _thumb_memory and os.path.isfile(_thumb_memory[videoid]):
        return _thumb_memory[videoid]

    # 2) File already exists on disk from previous call
    if os.path.isfile(output):
        _thumb_memory[videoid] = output
        return output

    # 3) Fetch metadata
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        from py_yt import VideosSearch
        data      = (await VideosSearch(url, limit=1).next())["result"][0]
        title     = re.sub(r"[\x00-\x1f\x7f]", "", data.get("title", "Unknown")).strip()
        duration  = data.get("duration", "00:00") or "00:00"
        thumb_url = data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0]
        v_raw     = str(data.get("viewCount", {}).get("short", "N/A"))
        vc        = re.sub(r'\s*views?\s*', '', v_raw, flags=re.IGNORECASE).strip()
        views, channel = f"{vc} views", data.get("channel", {}).get("name", "Unknown")
    except Exception:
        return "https://files.catbox.moe/m4fx24.jpg"

    # 4) Download thumbnail image
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(thumb_url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                async with aiofiles.open(cache, "wb") as f:
                    await f.write(await r.read())
        song_img = Image.open(cache).convert("RGBA")
    except Exception:
        song_img = Image.new("RGBA", (777, 458), (28, 10, 5))

    # 5) Compose
    c_base, c_light, c_dark = _random_palette()
    
    # thumbnail se base color mood
    bg = song_img.resize((W, H), Image.LANCZOS).convert("RGB")
    bg = bg.filter(ImageFilter.GaussianBlur(55))
    
    # dark cinematic overlay
    dark_overlay = Image.new("RGBA", (W, H), (3, 5, 12, 210))
    bg = Image.alpha_composite(bg.convert("RGBA"), dark_overlay)
    
    # ambient gradient blobs
    # universe / nebula style background glow
    blob_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    blob_draw = ImageDraw.Draw(blob_layer)
    
    # random cosmic palette
    accent = (
        random.randint(40, 255),
        random.randint(40, 255),
        random.randint(40, 255),
        random.randint(25, 45)
    )
    
    cosmic_colors = [
        (*c_base, random.randint(45, 85)),
        (*c_light, random.randint(35, 70)),
        (*c_dark, random.randint(25, 55)),
        accent
    ]
    
    random.shuffle(cosmic_colors)
    
    positions = [
        (-220, 80, 420, 700),
        (820, -150, 1450, 420),
        (300, 420, 1050, 930),
        (420, -180, 980, 260),
    ]
    
    for color, pos in zip(cosmic_colors, positions):
        blob_draw.ellipse(pos, fill=color)
    
    # extra center mist glow
    blob_draw.ellipse(
        (250, 180, 1050, 760),
        fill=(255, 255, 255, 12)
    )
    
    blob_layer = blob_layer.filter(ImageFilter.GaussianBlur(150))
    bg = Image.alpha_composite(bg, blob_layer)
    
    # subtle vignette
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    
    for i in range(220, 0, -8):
        alpha = int(190 * (1 - i / 220))
        vd.rectangle(
            [0, 0, W, H],
            outline=(0, 0, 0, alpha),
            width=i
        )
    
    vignette = vignette.filter(ImageFilter.GaussianBlur(75))
    bg = Image.alpha_composite(bg, vignette)
    
    # soft noise texture
    noise = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise)
    
    for _ in range(1200):
        x = random.randint(0, W)
        y = random.randint(0, H)
        nd.point((x, y), fill=(255, 255, 255, random.randint(8, 20)))
    
    noise = noise.filter(ImageFilter.GaussianBlur(0.5))
    bg = Image.alpha_composite(bg, noise).convert("RGB")
        
    base = bg
    
    # premium card
    base = _draw_card_border_v4(
        base,
        310, 90, 1060, 545,
        30,
        c_base, c_light, c_dark
    )
    
    # thumbnail shadow
    base = _draw_art_shadow(base, 322, 102, 727, 433, 18, c_base)
    
    # thumbnail wapas
    base = _paste_rounded(base, song_img, 322, 102, 727, 433, 18)
    
    # subtle glass effect (optional)
    glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    
    gd.rounded_rectangle(
        [325, 105, 1045, 530],
        radius=22,
        fill=(255, 255, 255, 8)
    )
    
    glass = glass.filter(ImageFilter.GaussianBlur(4))
    base = Image.alpha_composite(base.convert("RGBA"), glass).convert("RGB")
    
    # progress bar
    base = _draw_bar(base, 105, 93, 556, 0.06, c_base, c_light, c_dark)
    draw = ImageDraw.Draw(base)
    f_t   = _get_font(FONT_BOLD,   30)
    f_tit = _get_font(FONT_BOLD,   44)
    f_s   = _get_font(FONT_NORMAL, 30)
    f_wm  = _get_font(FONT_BOLD,   24)

    draw.text((105, 44),  "00:17",                                                  font=f_t,   fill=c_base,     anchor="mm")
    draw.text((105, 598), duration,                                                  font=f_t,   fill=c_base,     anchor="mm")
    draw.text((685, 580), _truncate(draw, title, f_tit, 800),                        font=f_tit, fill=TEXT_WHITE, anchor="mm")
    draw.text((685, 630), _truncate(draw, f"{channel}  |  {views}", f_s, 840),       font=f_s, fill=TEXT_GRAY, anchor="mm")
    safe_name = clean_username(user_name)

    print(f"[DEBUG] user_name = {user_name}")

    # normalize dashes
    safe_name = safe_name.replace("–", "-").replace("—", "-").strip()

    if safe_name.lower() in ["none", "", "-", "null"]:
        safe_name = "Unknown"

    # 🔥 custom color control (yaha change karega tu)
    NAME_COLOR = (255, 255, 255)   # white
    # NAME_COLOR = (255, 215, 0)   # yellow karna ho to ye use kar

    # fonts
    f_req_label = _get_font(FONT_BOLD, 30)     # "Requested by:"
    f_req = _get_font(FONT_BOLD, 30)   # username

    label_text = "Requested by: "
    name_text  = safe_name

    # width calculate (same font)
    label_w = draw.textlength(label_text, font=f_req)
    name_w  = draw.textlength(name_text, font=f_req)

    total_w = label_w + name_w

    center_x = W // 2
    start_x = center_x - total_w // 2
    y = 680

    # label
    draw.text(
        (start_x, y),
        label_text,
        font=f_req,
        fill=c_base,
        anchor="lm"
    )

    # name (same font)
    draw.text(
        (start_x + label_w, y),
        name_text,
        font=f_req,
        fill=NAME_COLOR,
        anchor="lm"
    )
    draw.text((1255, 45), "Dev :- Maanav",                                          font=f_wm,  fill=TEXT_WHITE, anchor="rd")

    base.save(output, "PNG", optimize=True)

    # Cleanup temp download
    try:
        if os.path.exists(cache):
            os.remove(cache)
    except Exception:
        pass

    _thumb_memory[videoid] = output
    return output
