# -----------------------------------------------
# 🔸 AxiomMusic Project
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by AxiomBots
# -----------------------------------------------

import asyncio
import re

from pyrogram import errors, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from AxiomMusic import YouTube, app
from AxiomMusic.core.call import Axiomm
from AxiomMusic.misc import SUDOERS, db
from AxiomMusic.utils.database import (
    get_active_chats,
    get_lang,
    get_upvote_count,
    is_active_chat,
    is_music_playing,
    is_nonadmin_chat,
    music_off,
    music_on,
    set_loop,
)
from AxiomMusic.utils.decorators.language import languageCB
from AxiomMusic.utils.formatters import seconds_to_min
from AxiomMusic.utils.inline import close_markup, stream_markup, stream_markup_timer
from AxiomMusic.utils.stream.autoclear import auto_clean
from AxiomMusic.utils.thumbnails import get_thumb
from config import (
    BANNED_USERS,
    SUPPORT_CHAT,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
    confirmer,
    votemode,
)
from strings import get_string

checker = {}
upvoters = {}


# ── helper: check if caller has VC admin rights ──────────────────────────────
async def _check_vc_admin(CallbackQuery, chat_id, _) -> bool:
    is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
    if not is_non_admin:
        if CallbackQuery.from_user.id not in SUDOERS:
            admins = adminlist.get(CallbackQuery.message.chat.id)
            if not admins:
                await CallbackQuery.answer(_["admin_13"], show_alert=True)
                return False
            if CallbackQuery.from_user.id not in admins:
                await CallbackQuery.answer(_["admin_14"], show_alert=True)
                return False
    return True


# ── helper: play the next queued track (shared by skip command & callback) ───
async def _do_skip_or_replay(CallbackQuery_or_message, chat_id, _, is_replay=False):
    """
    Skips to the next track (or replays current if is_replay=True).
    Works with both callback queries and messages.
    """
    check = db.get(chat_id)
    is_cb = hasattr(CallbackQuery_or_message, "answer")  # True = CallbackQuery
    mention = CallbackQuery_or_message.from_user.mention

    if is_replay:
        txt = f"<blockquote expandable><b>✧ ʀᴇ-ᴘʟᴀʏɪɴɢ 💝\n│ \n└ʙʏ : {mention} 📿 </b></blockquote>"
    else:
        txt = f"<blockquote expandable><b>✧ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ 💝\n│ \n└ʙʏ : {mention} 📿 </b></blockquote>"
        popped = None
        try:
            popped = check.pop(0)
            if popped:
                await auto_clean(popped)
            if not check:
                if is_cb:
                    await CallbackQuery_or_message.edit_message_text(txt)
                    await CallbackQuery_or_message.message.reply_text(
                        text=_["admin_6"].format(mention, CallbackQuery_or_message.message.chat.title),
                        reply_markup=close_markup(_),
                    )
                else:
                    await CallbackQuery_or_message.reply_text(
                        text=_["admin_6"].format(mention, CallbackQuery_or_message.chat.title),
                        reply_markup=close_markup(_),
                    )
                try:
                    return await Axiomm.stop_stream(chat_id)
                except Exception:
                    return
        except Exception:
            try:
                if is_cb:
                    await CallbackQuery_or_message.edit_message_text(txt)
                    await CallbackQuery_or_message.message.reply_text(
                        text=_["admin_6"].format(mention, CallbackQuery_or_message.message.chat.title),
                        reply_markup=close_markup(_),
                    )
                else:
                    await CallbackQuery_or_message.reply_text(
                        text=_["admin_6"].format(mention, CallbackQuery_or_message.chat.title),
                        reply_markup=close_markup(_),
                    )
                return await Axiomm.stop_stream(chat_id)
            except Exception:
                return

    # ── play next/current track ───────────────────────────────────────────────
    queued = check[0]["file"]
    title = (check[0]["title"]).title()
    user = check[0]["by"]
    duration = check[0]["dur"]
    streamtype = check[0]["streamtype"]
    videoid = check[0]["vidid"]
    status = True if str(streamtype) == "video" else None
    db[chat_id][0]["played"] = 0

    exis = (check[0]).get("old_dur")
    if exis:
        db[chat_id][0]["dur"] = exis
        db[chat_id][0]["seconds"] = check[0]["old_second"]
        db[chat_id][0]["speed_path"] = None
        db[chat_id][0]["speed"] = 1.0

    reply_to = CallbackQuery_or_message.message if is_cb else CallbackQuery_or_message

    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await reply_to.reply_text(
                text=_["admin_7"].format(title),
                reply_markup=close_markup(_),
            )
        try:
            image = await YouTube.thumbnail(videoid, True)
        except Exception:
            image = None
        try:
            await Axiomm.skip_stream(chat_id, link, video=status, image=image)
        except Exception:
            return await reply_to.reply_text(_["call_6"])
        button = stream_markup(_, chat_id)
        img = await get_thumb(videoid, user)
        run = await reply_to.reply_photo(
            photo=img,
            has_spoiler=True,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                duration,
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    elif "vid_" in queued:
        mystic = await reply_to.reply_text(_["call_7"], disable_web_page_preview=True)
        try:
            file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=status)
        except Exception:
            return await mystic.edit_text(_["call_6"])
        try:
            image = await YouTube.thumbnail(videoid, True)
        except Exception:
            image = None
        try:
            await Axiomm.skip_stream(chat_id, file_path, video=status, image=image)
        except Exception:
            return await mystic.edit_text(_["call_6"])
        button = stream_markup(_, chat_id)
        img = await get_thumb(videoid, user)
        run = await reply_to.reply_photo(
            photo=img,
            has_spoiler=True,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                duration,
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
        await mystic.delete()

    elif "index_" in queued:
        try:
            await Axiomm.skip_stream(chat_id, videoid, video=status)
        except Exception:
            return await reply_to.reply_text(_["call_6"])
        button = stream_markup(_, chat_id)
        run = await reply_to.reply_photo(
            photo=STREAM_IMG_URL,
            has_spoiler=True,
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    else:
        if videoid in ("telegram", "soundcloud"):
            image = None
        else:
            try:
                image = await YouTube.thumbnail(videoid, True)
            except Exception:
                image = None
        try:
            await Axiomm.skip_stream(chat_id, queued, video=status, image=image)
        except Exception:
            return await reply_to.reply_text(_["call_6"])

        if videoid == "telegram":
            photo = TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else TELEGRAM_VIDEO_URL
            caption = _["stream_1"].format(SUPPORT_CHAT, title[:23], duration, user)
        elif videoid == "soundcloud":
            photo = SOUNCLOUD_IMG_URL if str(streamtype) == "audio" else TELEGRAM_VIDEO_URL
            caption = _["stream_1"].format(SUPPORT_CHAT, title[:23], duration, user)
        else:
            img = await get_thumb(videoid, user)
            caption = _["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                duration,
                user,
            )

        button = stream_markup(_, chat_id)
        run = await reply_to.reply_photo(
            photo=photo,
            has_spoiler=True,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg" if videoid in ("telegram", "soundcloud") else "stream"

    if is_cb:
        try:
            await CallbackQuery_or_message.edit_message_text(txt, reply_markup=close_markup(_))
        except Exception:
            pass


# ── ADMIN callback handler ────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")

    counter = None
    if "_" in str(chat):
        bet = chat.split("_")
        chat = bet[0]
        counter = bet[1]
    chat_id = int(chat)

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)

    mention = CallbackQuery.from_user.mention

    # ── UpVote logic (unchanged from original) ─────────────────────────────
    if command == "UpVote":
        if chat_id not in votemode:
            votemode[chat_id] = {}
        if chat_id not in upvoters:
            upvoters[chat_id] = {}

        voters = (upvoters[chat_id]).get(CallbackQuery.message.id)
        if not voters:
            upvoters[chat_id][CallbackQuery.message.id] = []

        vote = (votemode[chat_id]).get(CallbackQuery.message.id)
        if not vote:
            votemode[chat_id][CallbackQuery.message.id] = 0

        if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
            (upvoters[chat_id][CallbackQuery.message.id]).remove(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] -= 1
        else:
            (upvoters[chat_id][CallbackQuery.message.id]).append(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] += 1

        upvote = await get_upvote_count(chat_id)
        get_upvotes = int(votemode[chat_id][CallbackQuery.message.id])

        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote
            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
            except Exception:
                return await CallbackQuery.edit_message_text("ғᴀɪʟᴇᴅ.")
            try:
                if current["vidid"] != exists["vidid"] or current["file"] != exists["file"]:
                    return await CallbackQuery.edit_message_text(_["admin_35"])
            except Exception:
                return await CallbackQuery.edit_message_text(_["admin_36"])
            try:
                await CallbackQuery.edit_message_text(_["admin_37"].format(upvote))
            except Exception:
                pass
            command = counter
            mention = "ᴜᴘᴠᴏᴛᴇs"
        else:
            if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
                await CallbackQuery.answer(_["admin_38"], show_alert=True)
            else:
                await CallbackQuery.answer(_["admin_39"], show_alert=True)
            upl = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text=f"💝 {get_upvotes}",
                    callback_data=f"ADMIN  UpVote|{chat_id}_{counter}",
                )
            ]])
            await CallbackQuery.answer(_["admin_40"], show_alert=True)
            return await CallbackQuery.edit_message_reply_markup(reply_markup=upl)

    # ── admin permission check for all other commands ──────────────────────
    if not await _check_vc_admin(CallbackQuery, chat_id, _):
        return

    # ── Pause ──────────────────────────────────────────────────────────────
    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_1"], show_alert=True)
        await CallbackQuery.answer()
        await music_off(chat_id)
        await Axiomm.pause_stream(chat_id)
        await CallbackQuery.message.reply_text(
            _["admin_2"].format(mention), reply_markup=close_markup(_)
        )

    # ── Resume ─────────────────────────────────────────────────────────────
    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_3"], show_alert=True)
        await CallbackQuery.answer()
        await music_on(chat_id)
        await Axiomm.resume_stream(chat_id)
        await CallbackQuery.message.reply_text(
            _["admin_4"].format(mention), reply_markup=close_markup(_)
        )

    # ── Stop / End ─────────────────────────────────────────────────────────
    elif command in ("Stop", "End"):
        await CallbackQuery.answer()
        await Axiomm.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await CallbackQuery.message.reply_text(
            _["admin_5"].format(mention), reply_markup=close_markup(_)
        )
        await CallbackQuery.message.delete()

    # ── Skip / Replay ──────────────────────────────────────────────────────
    elif command in ("Skip", "Replay"):
        await CallbackQuery.answer()
        await _do_skip_or_replay(
            CallbackQuery,
            chat_id,
            _,
            is_replay=(command == "Replay"),
        )


# ── Progress bar timer (unchanged) ───────────────────────────────────────────
async def markup_timer():
    while not await asyncio.sleep(7):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id):
                    continue
                playing = db.get(chat_id)
                if not playing:
                    continue
                duration_seconds = int(playing[0]["seconds"])
                if duration_seconds == 0:
                    continue
                try:
                    mystic = playing[0]["mystic"]
                except Exception:
                    continue
                try:
                    check = checker[chat_id][mystic.id]
                    if check is False:
                        continue
                except Exception:
                    pass
                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except Exception:
                    _ = get_string("en")
                try:
                    buttons = stream_markup_timer(
                        _,
                        chat_id,
                        seconds_to_min(playing[0]["played"]),
                        playing[0]["dur"],
                    )
                    await mystic.edit_reply_markup(
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                except Exception:
                    continue
            except Exception:
                continue


asyncio.create_task(markup_timer())
