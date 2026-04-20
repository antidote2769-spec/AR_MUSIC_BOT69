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

from pyrogram.enums import ParseMode
from AxiomMusic import app
from AxiomMusic.utils.database import is_on_off
from config import LOGGER_ID


async def play_logs(message, streamtype):
    if await is_on_off(2):
        logger_text = f"""<blockquote expandable>
        <b>{app.mention} ᴘʟᴀʏ ʟᴏɢ </blockquote>

<blockquote expandable>❖ ᴄʜᴀᴛ ɪᴅ : <code>{message.chat.id}</code>
❖ ᴄʜᴀᴛ ɴᴀᴍᴇ : {message.chat.title}
❖ ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ : @{message.chat.username} </blockquote>

<blockquote expandable>✦ ᴜsᴇʀ ɪᴅ : <code>{message.from_user.id}</code>
✦ ɴᴀᴍᴇ : {message.from_user.mention}
✦ ᴜsᴇʀɴᴀᴍᴇ : @{message.from_user.username} </blockquote>

<blockquote expandable>➤ ǫᴜᴇʀʏ : {message.text.split(None, 1)[1]}
➤ sᴛʀᴇᴀᴍᴛʏᴘᴇ : {streamtype}</b></blockquote>"""
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
        return
