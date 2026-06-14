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


import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import LOGGER_ID as LOG_GROUP_ID
from AxiomMusic import app 
from pyrogram.errors import RPCError
from typing import Union, Optional
from PIL import Image, ImageDraw, ImageFont
import asyncio, os, aiohttp
from pathlib import Path
from pyrogram.enums import ParseMode

photo = [
    "https://litter.catbox.moe/8569kh.jpg",
    "https://litter.catbox.moe/8569kh.jpg",
    "https://litter.catbox.moe/8569kh.jpg",
    "https://litter.catbox.moe/8569kh.jpg",
    "https://litter.catbox.moe/8569kh.jpg",
]

@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):    
    chat = message.chat
    link = await app.export_chat_invite_link(chat.id)
    for member in message.new_chat_members:
        if member.id == app.id:
            count = await app.get_chat_members_count(chat.id)
            msg = (
                f"<blockquote expandable><b>📝 ᴍᴜsɪᴄ ʙᴏᴛ ᴀᴅᴅᴇᴅ ɪɴ ᴀ ɴᴇᴡ ɢʀᴏᴜᴘ </blockquote>\n\n"
                f"•─── ⋅ ⋅ ⋅ ─────── ⋅  ⋅ ─────── ⋅ ⋅ ⋅ ───•\n"
                f"<blockquote expandable><b>📌 ᴄʜᴀᴛ ɴᴀᴍᴇ: {chat.title}\n"
                f"🍂 ᴄʜᴀᴛ ɪᴅ: {chat.id}\n"
                f"🔐 ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ: @{chat.username}\n"
                f"🛰 ᴄʜᴀᴛ ʟɪɴᴋ: [ᴄʟɪᴄᴋ]({link})\n"
                f"📈 ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs: {count}\n"
                f"🤔 ᴀᴅᴅᴇᴅ ʙʏ: {message.from_user.mention}</b></blockquote>"
            )
            await app.send_photo(LOG_GROUP_ID, photo=random.choice(photo), has_spoiler=True, caption=msg, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"sᴇᴇ ɢʀᴏᴜᴘ👀", url=f"{link}"),
                 InlineKeyboardButton(" ⌯ ᴅєᴠєʟᴏᴘєꝛ​ ⌯ ", url="tg://user?id=7169279112")]
            ]))

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if (await app.get_me()).id == message.left_chat_member.id:
        remove_by = message.from_user.mention if message.from_user else "𝐔ɴᴋɴᴏᴡɴ 𝐔sᴇʀ"
        title = message.chat.title
        username = f"@{message.chat.username}" if message.chat.username else "𝐏ʀɪᴠᴀᴛᴇ 𝐂ʜᴀᴛ"
        chat_id = message.chat.id
        left = f"<blockquote expandable><b>✧ <u>#𝐋ᴇғᴛ_𝐆ʀᴏᴜᴘ</u> \n\n✧ 𝐂ʜᴀᴛ 𝐓ɪᴛʟᴇ : {title}\n\n✧ 𝐂ʜᴀᴛ 𝐈ᴅ : {chat_id}\n\n✧ 𝐑ᴇᴍᴏᴠᴇᴅ 𝐁ʏ : {remove_by}\n\n✧ 𝐁ᴏᴛ : @{app.username} </b></blockquote>"
        await app.send_photo(LOG_GROUP_ID, photo=random.choice(photo), has_spoiler=True, caption=left, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{app.username}?startgroup=true"),
                 InlineKeyboardButton(" ⌯ ᴅєᴠєʟᴏᴘєꝛ​ ⌯ ", url="tg://user?id=7169279112")]
            ]))
