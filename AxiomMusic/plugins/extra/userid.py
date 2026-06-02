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


from AxiomMusic import app
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_message(filters.command('id'))
async def getid(client, message):
    chat = message.chat
    your_id = message.from_user.id
    message_id = message.id
    reply = message.reply_to_message

    text = f"<blockquote expandable><b>✧ [ᴍᴇssᴀɢᴇ ɪᴅ:]({message.link}) `{message_id}`\n"
    text += f"✧ [ʏᴏᴜʀ ɪᴅ:](tg://user?id={your_id}) `{your_id}`\n</b></blockquote>"

    if not message.command:
        message.command = message.text.split()

    if len(message.command) == 2:
        try:
            split = message.text.split(None, 1)[1].strip()
            user_id = (await client.get_users(split)).id
            text += f"<blockquote expandable><b>✧ [ᴜsᴇʀ ɪᴅ:](tg://user?id={user_id}) `{user_id}`\n</b></blockquote>"
        except Exception:
            return await message.reply_text("<blockquote expandable><b>✧ ᴛʜɪs ᴜsᴇʀ ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ. </b></blockquote>", quote=True)

    text += f"<blockquote expandable><b>✧ [ᴄʜᴀᴛ ɪᴅ:](https://t.me/{chat.username}) `{chat.id}`\n\n</b></blockquote>" if chat.username else f"<blockquote expandable><b>✧ ᴄʜᴀᴛ ɪᴅ:** `{chat.id}`\n\n</b></blockquote>"

    if (
        reply
        and not getattr(reply, "empty", True)
        and not message.forward_from_chat
        and not reply.sender_chat
    ):
        text += f"<blockquote expandable><b>✧ [ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪᴅ:]({reply.link}) `{reply.id}`\n"
        text += f"✧ [ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ ɪᴅ:](tg://user?id={reply.from_user.id}) `{reply.from_user.id}`\n\n</b></blockquote>"

    if reply and reply.forward_from_chat:
        text += f"<blockquote expandable><b>✧ ᴛʜᴇ ғᴏʀᴡᴀʀᴅᴇᴅ ᴄʜᴀɴɴᴇʟ, {reply.forward_from_chat.title}, ʜᴀs ᴀɴ ɪᴅ ᴏғ `{reply.forward_from_chat.id}`\n\n</b></blockquote>"

    if reply and reply.sender_chat:
        text += f"<blockquote expandable><b>✧ ɪᴅ ᴏғ ᴛʜᴇ ʀᴇᴘʟɪᴇᴅ ᴄʜᴀᴛ/ᴄʜᴀɴɴᴇʟ, ɪs `{reply.sender_chat.id}`</b></blockquote>"

    await message.reply_text(
        text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.DEFAULT,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")
              ]]
        )
    )
