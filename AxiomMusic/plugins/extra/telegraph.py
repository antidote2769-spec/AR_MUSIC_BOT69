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

import os
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from AxiomMusic import app

def upload_file(file_path):
    url = "https://catbox.moe/user/api.jpg"
    data = {"reqtype": "fileupload", "json": "true"}
    with open(file_path, "rb") as file:
        response = requests.post(url, data=data, files={"fileToUpload": file})
    if response.status_code == 200:
        return True, response.text.strip()
    else:
        return False, f"Error: {response.status_code} - {response.text}"

@app.on_message(filters.command(["tgm", "tm", "telegraph", "tl"]))
async def get_link_group(client, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "<blockquote expandable><b>✧ ⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴛᴏ ᴜᴘʟᴏᴀᴅ. </b></blockquote>"
        )

    media = message.reply_to_message
    file_size = 0

    if media.photo:
        file_size = media.photo.file_size
    elif media.video:
        file_size = media.video.file_size
    elif media.document:
        file_size = media.document.file_size

    if file_size == 0:
        return await message.reply_text("<blockquote expandable><b>✧ ⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴅᴏᴇsɴ'ᴛ ᴄᴏɴᴛᴀɪɴ ᴀɴʏ ᴅᴏᴡɴʟᴏᴀᴅᴀʙʟᴇ ᴍᴇᴅɪᴀ. </b></blockquote>")

    if file_size > 200 * 1024 * 1024:
        return await message.reply_text("<blockquote expandable><b>✧ ⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴜɴᴅᴇʀ 200MB. </b></blockquote>")

    text = await message.reply("<blockquote expandable><b>✧ 🔄 ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ғɪʟᴇ... </b></blockquote>")

    async def progress(current, total):
        try:
            await text.edit_text(f"<blockquote expandable><b>✧ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ... {current * 100 / total:.1f}% </b></blockquote>")
        except Exception:
            pass

    try:
        local_path = await media.download(progress=progress)

        if not os.path.exists(local_path):
            return await text.edit_text("<blockquote expandable><b>✧ ❌ Failed to download the media. </b></blockquote>")

        await text.edit_text("<blockquote expandable><b>✧ ᴜᴘʟᴏᴀᴅᴇᴅ ᴛᴏ ᴄᴀᴛʙᴏx... </b></blockquote>")

        success, result = upload_file(local_path)

        if success:
            await message.reply_photo(
                local_path,
                caption=f"<blockquote expandable><b>✧ {message.from_user.mention(style='md')}, this is your uploaded media! </b></blockquote>",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴘʜ ʟɪɴᴋ", url=result)]]
                ),
            )
        else:
            await text.edit_text(f"<blockquote expandable><b>✧ ❌ ᴜᴘʟᴏᴀᴅ ғᴀɪʟᴇᴅ!\nError: {result} </b></blockquote>")

    except Exception as e:
        await text.edit_text(f"<blockquote expandable><b>✧ ❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ:\n{e} </b></blockquote>")

    finally:
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception:
            pass
