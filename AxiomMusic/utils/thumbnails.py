import os
import re
import random
import aiohttp
import aiofiles
import colorsys
from functools import lru_cache
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS      = os.path.join(BASE_DIR, "..", "assets")
FONT_BOLD   = os.path.join(ASSETS, "f.ttf")
FONT_NORMAL = os.path.join(ASSETS, "cfont.ttf")

# ═══════════════════════════════════════════════════════════════════
# THUMBNAIL GENERATOR - VERSION 4.1 (Performance Edition)
# Fixes: removed unused numpy import, added in-memory cache guard
# ═══════════════════════════════════════════════════════════════════

W, H = 1280, 720
BG_COLOR   = (45,  60,  65)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY  = (175, 182, 188)

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
    mode = random.choice(["vivid", "monochrome", "dark", "pastel"])
    if mode == "vivid":
        h, s, v = random.random(), random.uniform(0.7, 1.0), random.uniform(0.8, 1.0)
    elif mode == "monochrome":
        h, s, v = 0, 0, random.choice([0.1, 0.5, 0.95])
    elif mode == "dark":
        h, s, v = random.random(), random.uniform(0.4, 0.8), random.uniform(0.2, 0.4)
    else:
        h, s, v = random.random(), random.uniform(0.2, 0.4), random.uniform(0.9, 1.0)
    base  = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, s, v))
    light = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, max(s-0.3, 0), min(v+0.2, 1.0)))
    dark  = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, min(s+0.2, 1.0), max(v-0.3, 0)))
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
    for i in range(25, 0, -1):
        alpha = int(60 * (1 - i / 25) ** 1.5)
        d.rounded_rectangle([x1 - i, y1 - i, x2 + i, y2 + i], radius=r + i, fill=(255, 255, 255, alpha))
    for i in range(12, 0, -1):
        d.rounded_rectangle([x1 - i, y1 - i, x2 + i, y2 + i], radius=r + i, fill=(*c_base, int(45 * (1 - i / 12))))
    d.rounded_rectangle([x1 + 10, y1 + 10, x2 - 10, y2 - 10], radius=max(r - 10, 4), fill=(18, 24, 26, 255))
    for offset, color, bw in [(0, (*c_dark, 255), 5), (2, (*c_base, 255), 3), (4, (255, 255, 255, 180), 2)]:
        d.rounded_rectangle([x1 + offset, y1 + offset, x2 - offset, y2 - offset], radius=max(r - offset, 4), outline=color, width=bw)
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def _draw_art_shadow(base: Image.Image, x, y, w, h, r=18, c_base=(202,215,221)) -> Image.Image:
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd, off_x, off_y = ImageDraw.Draw(shadow_layer), 8, 12
    for i in range(35, 0, -1):
        sd.rounded_rectangle([x+off_x-i, y+off_y-i, x+w+off_x+i, y+h+off_y+i], radius=r+i, fill=(0, 0, 0, int(210*(1-i/35)**1.2)))
    for i in range(15, 0, -1):
        sd.rounded_rectangle([x+off_x-i, y+off_y-i, x+w+off_x+i, y+h+off_y+i], radius=r+i, fill=(*c_base, int(100*(1-i/15)**2.0)))
    return Image.alpha_composite(base.convert("RGBA"), shadow_layer.filter(ImageFilter.GaussianBlur(15))).convert("RGB")


def _paste_rounded(base: Image.Image, img: Image.Image, x, y, w, h, r=18) -> Image.Image:
    img = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=r, fill=255)
    img.putalpha(mask)
    base_r = base.convert("RGBA")
    base_r.paste(img, (x, y), img)
    return base_r.convert("RGB")


def _draw_bar(base: Image.Image, bx, by_top, by_bot, progress: float = 0.06, c_base=(202,215,221), c_light=(225,235,240), c_dark=(140,155,162)) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw, knob_y, kr = 8, by_top + int((by_bot - by_top) * progress), 14
    d.rounded_rectangle([(bx - bw//2, by_top), (bx + bw//2, by_bot)], radius=4, fill=(131, 141, 147, 255))
    if knob_y > by_top:
        d.rounded_rectangle([(bx - bw//2, by_top), (bx + bw//2, knob_y)], radius=4, fill=(*c_base, 255))
    d.ellipse([(bx - kr - 6, knob_y - kr - 6), (bx + kr + 6, knob_y + kr + 6)], fill=(*c_base, 50))
    d.ellipse([(bx - kr, knob_y - kr), (bx + kr, knob_y + kr)], fill=(*c_base, 255))
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def _truncate(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w: return text
    while text and draw.textlength(text + "…", font=font) > max_w: text = text[:-1]
    return text + "…"


async def get_thumb(videoid: str, user_id=None) -> str:
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
    base = _make_bg_v4()
    base = _draw_card_border_v4(base, 310, 90, 1060, 545, 28, c_base, c_light, c_dark)
    base = _draw_art_shadow(base, 322, 102, 727, 433, 18, c_base)
    base = _paste_rounded(base, song_img, 322, 102, 727, 433, 18)
    base = _draw_bar(base, 105, 93, 556, 0.06, c_base, c_light, c_dark)

    draw = ImageDraw.Draw(base)
    f_t   = _get_font(FONT_BOLD,   30)
    f_tit = _get_font(FONT_BOLD,   44)
    f_s   = _get_font(FONT_NORMAL, 30)
    f_wm  = _get_font(FONT_BOLD,   24)

    draw.text((105, 44),  duration,                                                  font=f_t,   fill=c_base,     anchor="mm")
    draw.text((105, 598), "00:25",                                                   font=f_t,   fill=c_base,     anchor="mm")
    draw.text((685, 592), _truncate(draw, title, f_tit, 800),                        font=f_tit, fill=TEXT_WHITE, anchor="mm")
    draw.text((685, 640), _truncate(draw, f"{channel}  |  {views}", f_s, 840),       font=f_s,   fill=TEXT_GRAY,  anchor="mm")
    draw.text((1255, 695), "Dev :- Maanav",                                           font=f_wm,  fill=TEXT_WHITE, anchor="rd")

    base.save(output, "PNG", optimize=True)

    # Cleanup temp download
    try:
        if os.path.exists(cache):
            os.remove(cache)
    except Exception:
        pass

    _thumb_memory[videoid] = output
    return output
