# -----------------------------------------------
# 🔸 AxiomMusic Project
# 🔹 Developed & Maintained by: Axiom Bots
# -----------------------------------------------

import os
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from AxiomMusic import app


# 🔹 Upload to Catbox
def upload_file(file_path):
    url = "https://catbox.moe/user/api.php"

    data = {
        "reqtype": "fileupload"
        # "userhash": "YOUR_USERHASH"  # optional (recommended if error persists)
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        with open(file_path, "rb") as file:
            response = requests.post(
                url,
                data=data,
                files={"fileToUpload": file},
                headers=headers,
                timeout=60
            )

        if response.status_code == 200:
            return True, response.text.strip()
        else:
            return False, f"{response.status_code} - {response.text}"

    except Exception as e:
        return False, str(e)


# 🔹 Command Handler
@app.on_message(filters.command(["tgm", "tm", "telegraph", "tl"]))
async def get_link_group(client, message):

    if not message.reply_to_message:
        return await message.reply_text(
            "<blockquote><b>⚠️ Reply to a media file first.</b></blockquote>"
        )

    media = message.reply_to_message
    file_size = 0

    # 🔹 Detect media
    if media.photo:
        file_size = media.photo.file_size
    elif media.video:
        file_size = media.video.file_size
    elif media.document:
        file_size = media.document.file_size

    if file_size == 0:
        return await message.reply_text(
            "<blockquote><b>⚠️ No downloadable media found.</b></blockquote>"
        )

    # 🔹 Size limit (Catbox ~200MB safe)
    if file_size > 200 * 1024 * 1024:
        return await message.reply_text(
            "<blockquote><b>⚠️ File must be under 200MB.</b></blockquote>"
        )

    text = await message.reply("<b>🔄 Processing...</b>")

    # 🔹 Progress bar
    async def progress(current, total):
        try:
            percent = current * 100 / total
            await text.edit_text(f"<b>📥 Downloading... {percent:.1f}%</b>")
        except:
            pass

    local_path = None

    try:
        # 🔹 Download file
        local_path = await media.download(progress=progress)

        if not local_path or not os.path.exists(local_path):
            return await text.edit_text("<b>❌ Download failed.</b>")

        # 🔹 Check file size again (debug safety)
        if os.path.getsize(local_path) == 0:
            return await text.edit_text("<b>❌ File corrupted (0 bytes).</b>")

        await text.edit_text("<b>📤 Uploading to Catbox...</b>")

        # 🔹 Upload
        success, result = upload_file(local_path)

        if success:
            await message.reply_photo(
                local_path,
                caption=f"<b>✅ Uploaded successfully!</b>\n\n{message.from_user.mention(style='md')}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🌐 Open Link", url=result)]]
                ),
            )
            await text.delete()

        else:
            await text.edit_text(f"<b>❌ Upload failed:\n{result}</b>")

    except Exception as e:
        await text.edit_text(f"<b>❌ Error:\n{e}</b>")

    finally:
        # 🔹 Cleanup
        try:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
        except:
            pass
