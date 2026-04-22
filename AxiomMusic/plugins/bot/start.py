import random
import time

from py_yt import VideosSearch
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from AxiomMusic import app
from AxiomMusic.misc import _boot_
from AxiomMusic.plugins.sudo.sudoers import sudoers_list
from AxiomMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from AxiomMusic.utils.decorators.language import LanguageStart
from AxiomMusic.utils.formatters import get_readable_time
from AxiomMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string

# 🎆 Message Effects
EFFECT_ID = [
    5104841245755180586,
    5107584321108051014,
    5104841245755180586,
    5107584321108051014,
    5104841245755180586,
    5107584321108051014,
    5104841245755180586,
    5107584321108051014,
]

# 🌄 Random Start Images
Manav = [
    "https://files.catbox.moe/m4fx24.jpg",
]

# 🍓 Random Reactions — strawberry + 4 extras, changes every start
REACTIONS = ["🍓", "🔥", "❤️", "⚡", "🎉", "🥰", "👏", "💫", "🎶", "🌟", "👍",]


# =====================================================
# START IN PRIVATE
# =====================================================
@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    # 🍓 Random reaction — har baar alag
    try:
        await message.react(random.choice(REACTIONS), big=True)
    except Exception:
        pass

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        
        if name.startswith("help"):
            keyboard = help_pannel(_)
            return await message.reply_photo(
                        photo=random.choice(Manav),  
                has_spoiler=True,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )

        
        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} checked <b>sudolist</b>\n\n"
                         f"<b>ID:</b> <code>{message.from_user.id}</code>\n"
                         f"<b>User:</b> @{message.from_user.username}",
                )
            return

        # Track info
        if name.startswith("inf"):
            m = await message.reply_text("🔎 Searching...")
            query = name.replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"

            results = VideosSearch(query, limit=1)
            data = (await results.next())["result"][0]

            title = data["title"]
            duration = data["duration"]
            views = data["viewCount"]["short"]
            thumbnail = data["thumbnails"][0]["url"].split("?")[0]
            channellink = data["channel"]["link"]
            channel = data["channel"]["name"]
            link = data["link"]
            published = data["publishedTime"]

            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )

            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(_["S_B_8"], url=link),
                        InlineKeyboardButton(_["S_B_6"], url=config.SUPPORT_CHAT),
                    ]
                ]
            )

            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                has_spoiler=True,
                protect_content=True,
                caption=searched_text,
                reply_markup=key,
            )

            if await is_on_off(2):
                await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"<blockquote><b><u>✧ ηєᴡ υsєʀ sᴛᴧʀᴛєᴅ ᴛʜє ᴧxɪσϻ ϻυsɪᴄ ʙσᴛ ᴛσ ᴄʜєᴄᴋ ᴛʀᴧᴄᴋ ɪηғσ.</u></b></blockquote>\n\n"
                         f"<blockquote><b>✧ ηᴧϻє:- {message.from_user.mention}\n"
                         f"<b>✧ υsєʀηᴧϻє:-</b> @{message.from_user.username}\n"
                         f"<b>✧ υɪᴅ:-</b> <code>{message.from_user.id}</code>.</blockquote>",
                )
            return

    # 🌄 Normal Start
    out = private_panel(_)

    await message.reply_photo(
        photo=random.choice(Manav),  # ✅ RANDOM IMAGE FIXED
        has_spoiler=True,
        protect_content=True,
       message_effect_id=random.choice(EFFECT_ID),
        caption=_["start_2"].format(message.from_user.mention, app.mention),
        reply_markup=InlineKeyboardMarkup(out),
    )

    if await is_on_off(2):
        await app.send_message(
            chat_id=config.LOGGER_ID,
            text=f"<blockquote><b><u>❖ ηєᴡ υsєʀ sᴛᴧʀᴛєᴅ ᴛʜє ᴧxɪσϻ ϻυsɪᴄ ʙσᴛ.</u></b></blockquote>\n\n"
                 f"<blockquote><b>✧ ηᴧϻє:-<b> {message.from_user.mention}\n"
                 f"<b>✧ υsєʀηᴧϻє:-</b> @{message.from_user.username}\n"
                 f"<b>✧ υɪᴅ:-</b> <code>{message.from_user.id}</code></blockquote>",
        )


# =====================================================
# START IN GROUP
# =====================================================
@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)

    await message.reply_photo(
        photo=config.START_IMG_URL,
        has_spoiler=True,
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=InlineKeyboardMarkup(out),
    )

    await add_served_chat(message.chat.id)


# =====================================================
# WELCOME HANDLER
# =====================================================
@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            # Ban banned users
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass

            # Bot added
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)

                await message.reply_photo(
                    photo=config.START_IMG_URL,
                    has_spoiler=True,
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )

                await add_served_chat(message.chat.id)
                await message.stop_propagation()

        except Exception as ex:
            print("WELCOME ERROR:", ex)
