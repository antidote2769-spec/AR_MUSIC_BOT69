import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()


def get_env(*keys, default=None):
    for key in keys:
        value = getenv(key)
        if value is not None and value.strip():
            return value.strip().strip('"').strip("'")
    return default

# ✅ Time Conversion Utility
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

# ✅ Basic Config
API_ID = int(getenv("API_ID", ""))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
COOKIES = getenv("COOKIES", None)
MONGO_DB_URI = get_env("MONGO_DB_URI", "MONGO_URL", "MONGODB_URI", default="")

# ✅ Duration Config
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 54000))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "54000"))

# ✅ Limits Conversion (after defining time_to_seconds)
DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))
SONG_DOWNLOAD_DURATION_LIMIT = int(time_to_seconds(f"{SONG_DOWNLOAD_DURATION}:00"))

# ✅ Owner & Bot Identity
LOGGER_ID = int(getenv("LOGGER_ID", "-1003991995988"))
OWNER_ID = int(getenv("OWNER_ID", "7169279112"))
OWNER_USERNAME = getenv("OWNER_USERNAME", "@III_MAA7NAV_III") 
BOT_USERNAME = getenv("BOT_USERNAME", "@vcmnvbot")

# ✅ Command Handler
COMMAND_HANDLER = getenv("COMMAND_HANDLER", "! / .").split()

# ✅ Heroku
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# ✅ Git & Upstream Repo
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://t.me/III_MAA7NAV_III")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", "")  # Only for private repo

# ✅ Support Links
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/axiombots")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/manavkiduniya")


PLAYLIST_ID = "-1003991995988"



# Vars For API End Pont.
YTPROXY_URL = getenv("YTPROXY_URL", 'https://tgapi.xbitcode.com') ## xBit Music Endpoint.
YT_API_KEY = getenv("YT_API_KEY" , 'xbit_HZlx-3yc9HWPdqkCyFTJIMkHyUDo6BrD' ) ## Your API key like: xbit_10000000xx0233 Get from  https://t.me/tgmusic_apibot
YOUTUBE_DATA_API_KEY = getenv("YOUTUBE_DATA_API_KEY", "INFLEX90156228D")  ## Google YouTube Data API v3 key

# NexGen API (Fallback after Shruti) — https://console.nexgenbots.xyz
NEXGEN_API_URL = getenv("NEXGEN_API_URL", "https://console.nexgenbots.xyz")
NEXGEN_VIDEO_API_URL = getenv("NEXGEN_VIDEO_API_URL", "https://api.video.nexgenbots.xyz")
NEXGEN_API_KEY = getenv("NEXGEN_API_KEY", "")

# Inflix API (Fallback after NexGen) — https://teaminflex.xyz | Key from @InflexAPIBot
INFLIX_API_KEY = getenv("INFLIX_API_KEY", "INFLEX96052828D")



# ✅ Auto Features
AUTO_LEAVING_ASSISTANT = bool(getenv("AUTO_LEAVING_ASSISTANT", False))
AUTO_SUGGESTION_MODE = getenv("AUTO_SUGGESTION_MODE", "True")
AUTO_SUGGESTION_TIME = int(getenv("AUTO_SUGGESTION_TIME", "500"))


# ✅ Spotify                              
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "")

# ✅ Limits
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 25))
CLEANMODE_DELETE_MINS = int(getenv("CLEANMODE_MINS", "5"))
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", 21474836480))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", 21474836480))

# ✅ String Sessions
STRING1 = getenv("STRING_SESSION", "")
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)

# ✅ Runtime Storage
BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}
chatstats = {}
userstats = {}
clean = []

# ✅ UI Images
START_IMG_URL = getenv("START_IMG_URL", "https://files.catbox.moe/kjdsse.jpg")
PING_IMG_URL = getenv("PING_IMG_URL", "https://files.catbox.moe/kjdsse.jpg")
PLAYLIST_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"
STATS_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"
TELEGRAM_AUDIO_URL = "https://files.catbox.moe/kjdsse.jpg"
TELEGRAM_VIDEO_URL = "https://files.catbox.moe/kjdsse.jpg"
STREAM_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"
SOUNCLOUD_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"
YOUTUBE_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://files.catbox.moe/kjdsse.jpg"

# ✅ URL Validation
if SUPPORT_CHANNEL and not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - Your SUPPORT_CHANNEL URL is invalid. Must start with https://")

if SUPPORT_CHAT and not re.match(r"(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - Your SUPPORT_CHAT URL is invalid. Must start with https://")
