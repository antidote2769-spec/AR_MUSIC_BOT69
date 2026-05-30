import asyncio
import json
import os
import random
import re
from typing import Union
import aiohttp
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from py_yt import VideosSearch
from AxiomMusic import LOGGER
from AxiomMusic.utils.database import is_on_off
from AxiomMusic.utils.formatters import time_to_seconds
from config import YT_API_KEY, YTPROXY_URL as YTPROXY, NEXGEN_API_URL, NEXGEN_VIDEO_API_URL, NEXGEN_API_KEY, INFLIX_API_KEY

logger = LOGGER(__name__)


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.dl_stats = {
            "total_requests": 0,
            "okflix_downloads": 0,
            "cookie_downloads": 0,
            "existing_files": 0
        }
        # Per-chat autoplay history — {chat_id: set of played video IDs}
        self._autoplay_history: dict = {}


    def sanitize_url(self, link: str) -> Union[str, None]:
        """
        Validate and sanitize a YouTube URL.
        - Must match youtube.com or youtu.be domain
        - Must start with http:// or https://
        - Must contain ONLY safe URL characters (no shell metacharacters)
        Returns cleaned URL or None if invalid/suspicious.
        """
        if not link:
            return None
        link = link.strip()
        # Must start with http(s)://
        if not re.match(r"^https?://", link, re.IGNORECASE):
            return None
        # Must be a YouTube domain
        if not re.search(r"(?:youtube\.com|youtu\.be)", link, re.IGNORECASE):
            return None
        # Block shell injection metacharacters: ; | & $ ` ( ) { } < > \ newline null
        if re.search(r"[;|&$`(){}<>\\\x00\n\r]", link):
            return None
        # Allow only safe URL characters
        if not re.match(r"^[A-Za-z0-9\-._~:/?#\[\]@!',*%+=]+$", link):
            return None
        return link

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = self.sanitize_url(link)
        if not link:
            return False
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            if not offset and message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return self.sanitize_url(entity.url)
        if offset in (None,):
            # Fallback: manually check if message text contains a YouTube URL
            raw_text = message_1.text or message_1.caption or ""
            parts = raw_text.split()
            for part in parts:
                if re.search(r"(?:youtube\.com|youtu\.be)", part):
                    return self.sanitize_url(part)
            return None
        extracted = text[offset : offset + length]
        return self.sanitize_url(extracted)

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]


        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        playlist = await Playlist.get(link)
        if playlist:
            videos = []
            for video in playlist["videos"][:limit]:
                try:
                    duration = video.get("duration")
                    if duration:
                        duration_sec = int(time_to_seconds(duration))
                    else:
                        duration_sec = 0
                    videos.append({
                        "vidid": video["id"],
                        "title": video.get("title", "Unknown"),
                        "duration_min": duration,
                        "duration_sec": duration_sec,
                        "thumbnail": video.get("thumbnails", [{}])[0].get("url", "").split("?")[0] if video.get("thumbnails") else "",
                    })
                except:
                    continue
            return videos
        return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        try:
            results = []
            search = VideosSearch(link, limit=10)
            search_results = (await search.next()).get("result", [])

            # Filter videos longer than 1 hour
            for result in search_results:
                duration_str = result.get("duration", "0:00")
                try:
                    parts = duration_str.split(":")
                    duration_secs = 0
                    if len(parts) == 3:
                        duration_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration_secs = int(parts[0]) * 60 + int(parts[1])

                    if duration_secs <= 3600:
                        results.append(result)
                except (ValueError, IndexError):
                    continue

            if not results or query_type >= len(results):
                raise ValueError("No suitable videos found within duration limit")

            selected = results[query_type]
            return (
                selected["title"],
                selected["duration"],
                selected["thumbnails"][0]["url"].split("?")[0],
                selected["id"]
            )

        except Exception as e:
            LOGGER(__name__).error(f"Error in slider: {str(e)}")
            raise ValueError("Failed to fetch video details")

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            vid_id = link
            link = self.base + link
        loop = asyncio.get_running_loop()

        def create_session():
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.1)
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))
            return session

        async def download_with_requests(url, filepath, headers=None):
            try:
                session = create_session()

                # Use headers for authentication (including x-api-key)
                # allow_redirects=True handles redirects, stream=True for large files
                response = session.get(
                    url, 
                    headers=headers, 
                    stream=True, 
                    timeout=60,
                    allow_redirects=True
                )
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks for large files

                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)

                return filepath

            except Exception as e:
                logger.error(f"Requests download failed: {str(e)}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
            finally:
                session.close()

        async def audio_dl(vid_id):
            try:
                if not YT_API_KEY:
                    logger.error("API KEY not set in config, Set API Key you got from @tgmusic_apibot")
                    return None
                if not YTPROXY:
                    logger.error("API Endpoint not set in config\nPlease set a valid endpoint for YTPROXY_URL in config.")
                    return None

                headers = {
                    "x-api-key": f"{YT_API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                filepath = os.path.join("downloads", f"{vid_id}.mp3")

                if os.path.exists(filepath):
                    return filepath

                session = create_session()
                getAudio = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=60)

                try:
                    songData = getAudio.json()
                except Exception as e:
                    logger.error(f"Invalid response from API: {str(e)}")
                    return None
                finally:
                    session.close()

                status = songData.get('status')
                if status == 'success':
                    audio_url = songData.get('audio_url')
                    if not audio_url:
                        logger.error(f"API Error: Owner succeeded but cache empty — no audio_url in response")
                        # Fall through to Shruti fallback
                    else:
                        result = await download_with_requests(audio_url, filepath, headers)
                        if result:
                            return result
                        # download failed, fall through to Shruti

                elif status == 'error':
                    logger.error(f"API Error: {songData.get('message', 'Unknown error from API.')}")
                    # Fall through to Shruti fallback
                else:
                    logger.error(f"Could not fetch Backend (status={status!r}) — falling back to Shruti.")
                    # Fall through to Shruti fallback

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while fetching audio info: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid response from proxy: {str(e)}")
            except Exception as e:
                logger.error(f"Error in audio download: {str(e)}")

            # ── Shruti API Fallback ────────────────────────────────────────
            logger.warning(f"Primary API failed for audio {vid_id}, trying Shruti fallback...")
            try:
                SHRUTI_URL = "https://api.shrutibots.site"
                filepath = os.path.join("downloads", f"{vid_id}.mp3")
                if os.path.exists(filepath):
                    return filepath
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{SHRUTI_URL}/download",
                        params={"url": vid_id, "type": "audio"},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status != 200:
                            logger.error(f"Shruti API /download returned {resp.status}")
                            return None
                        data = await resp.json()
                        token = data.get("download_token")
                        if not token:
                            logger.error("Shruti API: no download_token in response")
                            return None
                    stream_url = f"{SHRUTI_URL}/stream/{vid_id}?type=audio&token={token}"
                    async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=300), allow_redirects=False) as file_resp:
                        if file_resp.status == 302:
                            redirect_url = file_resp.headers.get("Location")
                            if redirect_url:
                                async with session.get(redirect_url) as final:
                                    if final.status != 200:
                                        return None
                                    with open(filepath, "wb") as f:
                                        async for chunk in final.content.iter_chunked(16384):
                                            f.write(chunk)
                            else:
                                return None
                        elif file_resp.status == 200:
                            with open(filepath, "wb") as f:
                                async for chunk in file_resp.content.iter_chunked(16384):
                                    f.write(chunk)
                        else:
                            logger.error(f"Shruti stream returned {file_resp.status}")
                            return None
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    logger.info(f"Shruti fallback audio success: {filepath}")
                    return filepath
                return None
            except Exception as e:
                logger.error(f"Shruti audio fallback failed: {str(e)}")
                if os.path.exists(filepath):
                    try: os.remove(filepath)
                    except: pass

            # ── NexGen API Fallback ───────────────────────────────────────
            if NEXGEN_API_URL and NEXGEN_API_KEY:
                logger.warning(f"Trying NexGen fallback for audio {vid_id}...")
                try:
                    filepath = os.path.join("downloads", f"{vid_id}.mp3")
                    if os.path.exists(filepath):
                        return filepath
                    endp = f"{NEXGEN_API_URL}/song/{vid_id}?api={NEXGEN_API_KEY}"
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=40)) as ng_session:
                        for _ in range(10):
                            async with ng_session.get(endp, headers={"Accept": "application/json"}) as resp:
                                data = await resp.json()
                                if resp.status != 200:
                                    break
                                status = data.get("status")
                                dl_link = data.get("link")
                                if status == "done" and dl_link:
                                    async with ng_session.get(dl_link) as dl_resp:
                                        if dl_resp.status == 200:
                                            with open(filepath, "wb") as f:
                                                async for chunk in dl_resp.content.iter_chunked(131072):
                                                    if chunk:
                                                        f.write(chunk)
                                            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                                                logger.info(f"NexGen fallback audio success: {filepath}")
                                                return filepath
                                    break
                                elif status == "downloading":
                                    await asyncio.sleep(4)
                                    continue
                                else:
                                    break
                except Exception as e:
                    logger.error(f"NexGen audio fallback failed: {str(e)}")
                    if os.path.exists(filepath):
                        try: os.remove(filepath)
                        except: pass

            # ── Inflix API Fallback ───────────────────────────────────────
            if INFLIX_API_KEY:
                logger.warning(f"Trying Inflix fallback for audio {vid_id}...")
                try:
                    INFLIX_URL = "https://teaminflex.xyz"
                    filepath = os.path.join("downloads", f"{vid_id}.mp3")
                    if os.path.exists(filepath):
                        return filepath
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as inflix_session:
                        endp = f"{INFLIX_URL}/song/{vid_id}?api={INFLIX_API_KEY}"
                        async with inflix_session.get(endp, headers={"Accept": "application/json"}) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                dl_link = data.get("link") or data.get("url") or data.get("audio_url")
                                if dl_link:
                                    async with inflix_session.get(dl_link) as dl_resp:
                                        if dl_resp.status == 200:
                                            with open(filepath, "wb") as f:
                                                async for chunk in dl_resp.content.iter_chunked(131072):
                                                    if chunk:
                                                        f.write(chunk)
                                            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                                                logger.info(f"Inflix fallback audio success: {filepath}")
                                                return filepath
                            else:
                                logger.error(f"Inflix audio returned status {resp.status}")
                except Exception as e:
                    logger.error(f"Inflix audio fallback failed: {str(e)}")
                    if os.path.exists(filepath):
                        try: os.remove(filepath)
                        except: pass

            logger.error(f"All APIs failed for audio {vid_id} — Xbit + Shruti + NexGen + Inflix all unavailable.")
            return None


        async def video_dl(vid_id):
            try:
                if not YT_API_KEY:
                    logger.error("API KEY not set in config, Set API Key you got from @tgmusic_apibot")
                    return None
                if not YTPROXY:
                    logger.error("API Endpoint not set in config\nPlease set a valid endpoint for YTPROXY_URL in config.")
                    return None

                headers = {
                    "x-api-key": f"{YT_API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                filepath = os.path.join("downloads", f"{vid_id}.mp4")

                if os.path.exists(filepath):
                    return filepath

                session = create_session()
                getVideo = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=60)

                try:
                    videoData = getVideo.json()
                except Exception as e:
                    logger.error(f"Invalid response from API: {str(e)}")
                    return None
                finally:
                    session.close()

                status = videoData.get('status')
                if status == 'success':
                    video_url = videoData.get('video_url')
                    if not video_url:
                        logger.error(f"API Error: Owner succeeded but cache empty — no video_url in response")
                        # Fall through to Shruti fallback
                    else:
                        result = await download_with_requests(video_url, filepath, headers)
                        if result:
                            return result
                        # download failed, fall through to Shruti

                elif status == 'error':
                    logger.error(f"API Error: {videoData.get('message', 'Unknown error from API.')}")
                    # Fall through to Shruti fallback
                else:
                    logger.error(f"Could not fetch Backend (status={status!r}) — falling back to Shruti.")
                    # Fall through to Shruti fallback

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while fetching video info: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid response from proxy: {str(e)}")
            except Exception as e:
                logger.error(f"Error in video download: {str(e)}")

            # ── Shruti API Fallback ────────────────────────────────────────
            logger.warning(f"Primary API failed for video {vid_id}, trying Shruti fallback...")
            try:
                SHRUTI_URL = "https://api.shrutibots.site"
                filepath = os.path.join("downloads", f"{vid_id}.mp4")
                if os.path.exists(filepath):
                    return filepath
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{SHRUTI_URL}/download",
                        params={"url": vid_id, "type": "video"},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status != 200:
                            logger.error(f"Shruti API /download returned {resp.status}")
                            return None
                        data = await resp.json()
                        token = data.get("download_token")
                        if not token:
                            logger.error("Shruti API: no download_token in response")
                            return None
                    stream_url = f"{SHRUTI_URL}/stream/{vid_id}?type=video&token={token}"
                    async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=600), allow_redirects=False) as file_resp:
                        if file_resp.status == 302:
                            redirect_url = file_resp.headers.get("Location")
                            if redirect_url:
                                async with session.get(redirect_url) as final:
                                    if final.status != 200:
                                        return None
                                    with open(filepath, "wb") as f:
                                        async for chunk in final.content.iter_chunked(16384):
                                            f.write(chunk)
                            else:
                                return None
                        elif file_resp.status == 200:
                            with open(filepath, "wb") as f:
                                async for chunk in file_resp.content.iter_chunked(16384):
                                    f.write(chunk)
                        else:
                            logger.error(f"Shruti stream returned {file_resp.status}")
                            return None
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    logger.info(f"Shruti fallback video success: {filepath}")
                    return filepath
                return None
            except Exception as e:
                logger.error(f"Shruti video fallback failed: {str(e)}")
                if os.path.exists(filepath):
                    try: os.remove(filepath)
                    except: pass

            # ── NexGen API Fallback ───────────────────────────────────────
            if NEXGEN_API_URL and NEXGEN_VIDEO_API_URL and NEXGEN_API_KEY:
                logger.warning(f"Trying NexGen fallback for video {vid_id}...")
                try:
                    filepath = os.path.join("downloads", f"{vid_id}.mp4")
                    if os.path.exists(filepath):
                        return filepath
                    endp = f"{NEXGEN_VIDEO_API_URL}/video/{vid_id}?api={NEXGEN_API_KEY}"
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=40)) as ng_session:
                        for _ in range(10):
                            async with ng_session.get(endp, headers={"Accept": "application/json"}) as resp:
                                data = await resp.json()
                                if resp.status != 200:
                                    break
                                status = data.get("status")
                                dl_link = data.get("link")
                                if status == "done" and dl_link:
                                    async with ng_session.get(dl_link) as dl_resp:
                                        if dl_resp.status == 200:
                                            with open(filepath, "wb") as f:
                                                async for chunk in dl_resp.content.iter_chunked(131072):
                                                    if chunk:
                                                        f.write(chunk)
                                            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                                                logger.info(f"NexGen fallback video success: {filepath}")
                                                return filepath
                                    break
                                elif status == "downloading":
                                    await asyncio.sleep(4)
                                    continue
                                else:
                                    break
                except Exception as e:
                    logger.error(f"NexGen video fallback failed: {str(e)}")
                    if os.path.exists(filepath):
                        try: os.remove(filepath)
                        except: pass

            # ── Inflix API Fallback ───────────────────────────────────────
            if INFLIX_API_KEY:
                logger.warning(f"Trying Inflix fallback for video {vid_id}...")
                try:
                    INFLIX_URL = "https://teaminflex.xyz"
                    filepath = os.path.join("downloads", f"{vid_id}.mp4")
                    if os.path.exists(filepath):
                        return filepath
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as inflix_session:
                        endp = f"{INFLIX_URL}/video/{vid_id}?api={INFLIX_API_KEY}"
                        async with inflix_session.get(endp, headers={"Accept": "application/json"}) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                dl_link = data.get("link") or data.get("url") or data.get("video_url")
                                if dl_link:
                                    async with inflix_session.get(dl_link) as dl_resp:
                                        if dl_resp.status == 200:
                                            with open(filepath, "wb") as f:
                                                async for chunk in dl_resp.content.iter_chunked(131072):
                                                    if chunk:
                                                        f.write(chunk)
                                            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                                                logger.info(f"Inflix fallback video success: {filepath}")
                                                return filepath
                            else:
                                logger.error(f"Inflix video returned status {resp.status}")
                except Exception as e:
                    logger.error(f"Inflix video fallback failed: {str(e)}")
                    if os.path.exists(filepath):
                        try: os.remove(filepath)
                        except: pass

            logger.error(f"All APIs failed for video {vid_id} — Xbit + Shruti + NexGen + Inflix all unavailable.")
            return None

        async def song_video_dl():
            try:
                if not YT_API_KEY:
                    logger.error("API KEY not set in config")
                    return None
                if not YTPROXY:
                    logger.error("API Endpoint not set in config")
                    return None

                headers = {
                    "x-api-key": f"{YT_API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                filepath = f"downloads/{title}.mp4"

                if os.path.exists(filepath):
                    return filepath

                session = create_session()
                getVideo = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=60)

                try:
                    videoData = getVideo.json()
                except Exception as e:
                    logger.error(f"Invalid response from API: {str(e)}")
                    return None
                finally:
                    session.close()

                status = videoData.get('status')
                if status == 'success':
                    video_url = videoData['video_url']

                    result = await download_with_requests(video_url, filepath, headers)
                    return result

                logger.error(f"API Error: {videoData.get('message', 'Unknown error')}")
                return None

            except Exception as e:
                logger.error(f"Error in song video download: {str(e)}")
                return None

        async def song_audio_dl():
            try:
                if not YT_API_KEY:
                    logger.error("API KEY not set in config")
                    return None
                if not YTPROXY:
                    logger.error("API Endpoint not set in config")
                    return None

                headers = {
                    "x-api-key": f"{YT_API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                filepath = f"downloads/{title}.mp3"

                if os.path.exists(filepath):
                    return filepath

                session = create_session()
                getAudio = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=60)

                try:
                    audioData = getAudio.json()
                except Exception as e:
                    logger.error(f"Invalid response from API: {str(e)}")
                    return None
                finally:
                    session.close()

                status = audioData.get('status')
                if status == 'success':
                    audio_url = audioData['audio_url']

                    result = await download_with_requests(audio_url, filepath, headers)
                    return result

                logger.error(f"API Error: {audioData.get('message', 'Unknown error')}")
                return None

            except Exception as e:
                logger.error(f"Error in song audio download: {str(e)}")
                return None

        if songvideo:
            fpath = await song_video_dl()
            if not fpath:
                raise ValueError("song_video_dl returned None — check YT_API_KEY / YTPROXY_URL or API logs")
            return fpath
        elif songaudio:
            fpath = await song_audio_dl()
            if not fpath:
                raise ValueError("song_audio_dl returned None — check YT_API_KEY / YTPROXY_URL or API logs")
            return fpath
        elif video:
            direct = True
            downloaded_file = await video_dl(vid_id)
        else:
            direct = True
            downloaded_file = await audio_dl(vid_id)

        if not downloaded_file:
            raise ValueError(f"Download returned None for vidid={vid_id} — check YT_API_KEY / YTPROXY_URL or API logs")

        return downloaded_file, direct

    async def related_video(self, videoid: str, chat_id: int = 0):
        """
        Related song fetch karo jo KABHI PLAY NAHI HUA.
        Fixes:
        - Title + ID dono history mein track hote hain → same song alag upload se repeat nahi hoga
        - Genre/mood aware queries — hardcoded 'best hindi songs 2024' hata diya
        - Artist + song title alag-alag nikala → better search diversity
        - Seed title match bhi skip hoga (overlap 55% threshold, pehle 70% tha)
        - Last fallback mein bhi title history se filter
        """
        from AxiomMusic.utils.database import ap_history_add, ap_history_get, ap_history_clear
        try:
            # ── Step 1: History load + current song add ────────────────────
            history: set = set(await ap_history_get(chat_id))
            history.add(videoid)
            await ap_history_add(chat_id, videoid)

            if len(history) > 60:
                await ap_history_clear(chat_id)
                history = {videoid}
                await ap_history_add(chat_id, videoid)

            # ── Step 2: Current song ka title + artist fetch — 3 retries ──
            link = self.base + videoid
            current_title = ""
            current_channel = ""
            for _seed_try in range(3):
                try:
                    seed_res  = VideosSearch(link, limit=1)
                    seed_data = (await seed_res.next()).get("result", [])
                    if seed_data:
                        current_title   = seed_data[0].get("title", "").strip()
                        current_channel = seed_data[0].get("channel", {}).get("name", "").strip()
                    if current_title:
                        break
                except Exception:
                    await asyncio.sleep(1)

            if not current_title:
                return None

            # ── Step 3: Title parse — artist aur song name alag nikalo ────
            current_norm = current_title.lower()

            # "Artist - Song Title" ya "Song Title | Artist" pattern handle karo
            artist_kw = ""
            song_kw   = current_norm
            for sep in [" - ", " | ", " – ", " : "]:
                if sep in current_norm:
                    parts     = current_norm.split(sep, 1)
                    artist_kw = parts[0].strip()
                    song_kw   = parts[1].strip()
                    break

            # Agar channel name available hai to use karo
            if not artist_kw and current_channel:
                artist_kw = current_channel.lower().replace("- topic", "").strip()

            # Fallback — pehle 2 words
            if not artist_kw:
                words     = current_norm.split()
                artist_kw = " ".join(words[:2]) if len(words) >= 2 else current_norm

            # ── Step 4: Title-based history set (ID ke alawa) ──────────────
            # Song ka normalized title track karo — alag upload same song block karo
            title_history: set = set(await ap_history_get(chat_id))  # IDs already tracked
            # Title tokens 4+ chars wale words se banao
            def _title_tokens(t: str) -> frozenset:
                return frozenset(w for w in t.lower().split() if len(w) >= 4)
            cur_tokens = _title_tokens(current_title)

            # ── Step 5: Smart filter ───────────────────────────────────────
            def _skip(pick) -> bool:
                pid = pick.get("id", "")
                if not pid or pid in history:
                    return True
                # Live / no-duration skip
                dur_str = pick.get("duration") or ""
                if not dur_str or dur_str.lower() in ("live", ""):
                    return True
                # Duration < 1 min (shorts) skip
                try:
                    parts = dur_str.split(":")
                    secs  = int(parts[-1]) + int(parts[-2]) * 60 if len(parts) >= 2 else 0
                    if secs < 60:
                        return True
                except Exception:
                    pass
                # Title overlap — 55% threshold (pehle 70% tha jo bahut loose tha)
                ptitle = pick.get("title", "").lower().strip()
                if not ptitle:
                    return True
                pick_tokens = _title_tokens(ptitle)
                if cur_tokens and pick_tokens:
                    overlap = len(cur_tokens & pick_tokens) / min(len(cur_tokens), len(pick_tokens))
                    if overlap >= 0.55:
                        return True
                return False

            # ── Step 6: Smart diverse queries — genre/mood aware ──────────
            # Generic "best hindi songs 2024" type queries NAHI — woh unrelated songs dete hain
            queries = [
                f"{artist_kw} songs",                          # Same artist ke songs
                f"songs similar to {song_kw}",                 # Similar vibe
                f"{artist_kw} best songs",                     # Artist ke popular songs
                f"{song_kw} mix playlist",                     # Mood/genre mix
                f"songs like {current_title}",                 # Full title based
            ]

            seen_ids   = set(history)
            candidates = []

            for q in queries:
                try:
                    res  = VideosSearch(q, limit=20)
                    data = (await res.next()).get("result", [])
                    for pick in data:
                        pid = pick.get("id", "")
                        if pid and pid not in seen_ids and not _skip(pick):
                            seen_ids.add(pid)
                            candidates.append(pick)
                    if len(candidates) >= 20:
                        break
                except Exception:
                    continue

            # ── Step 7: No candidates — history reset + retry ─────────────
            if not candidates:
                await ap_history_clear(chat_id)
                history  = {videoid}
                seen_ids = {videoid}
                await ap_history_add(chat_id, videoid)
                try:
                    res  = VideosSearch(f"{artist_kw} songs", limit=20)
                    data = (await res.next()).get("result", [])
                    candidates = [
                        p for p in data
                        if p.get("id") and p["id"] not in seen_ids and not _skip(p)
                    ]
                    random.shuffle(candidates)
                except Exception:
                    pass

            if not candidates:
                return None

            # ── Step 8: Random pick from top 15 ───────────────────────────
            pick = random.choice(candidates[:15])
            await ap_history_add(chat_id, pick["id"])

            return {
                "id":       pick["id"],
                "title":    pick.get("title", "Unknown"),
                "duration": pick.get("duration", "0:00"),
            }

        except Exception as e:
            LOGGER(__name__).warning(f"[related_video] Exception: {e}")
            return None
