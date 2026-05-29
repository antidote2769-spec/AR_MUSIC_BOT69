# -----------------------------------------------
# 🔸 AxiomMusic Project
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from AxiomMusic import app
from AxiomMusic.utils.database import autoplay_off, autoplay_on, is_autoplay
from AxiomMusic.utils.decorators.admins import ActualAdminCB, AdminActual
from config import BANNED_USERS


def autoplay_markup(status: bool):
    toggle_text = "ᴛᴜʀɴ ᴏғғ ❌" if status else "ᴛᴜʀɴ ᴏɴ ✅"
    toggle_state = "off" if status else "on"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    toggle_text,
                    callback_data=f"autoplay_toggle|{toggle_state}",
                )
            ],
            [InlineKeyboardButton("⋞ ᴄʟᴏsє ⋟", callback_data="close")],
        ]
    )


def autoplay_text(status: bool):
    current = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"
    return (
        "<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<b>ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs:</b> {current}\n\n"
        "<blockquote>When enabled, if the queue becomes empty after a YouTube "
        "track ends, the bot will fetch a fresh related suggestion and play it "
        "automatically instead of leaving the voice chat.</blockquote>"
    )


@app.on_message(filters.command("autoplay") & filters.group & ~BANNED_USERS)
@AdminActual
async def autoplay_command(_, message: Message, __):
    status = await is_autoplay(message.chat.id)
    await message.reply_text(
        autoplay_text(status),
        reply_markup=autoplay_markup(status),
        disable_web_page_preview=True,
    )


@app.on_callback_query(filters.regex(r"^autoplay_toggle\|(on|off)$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_callback(_, callback_query: CallbackQuery, __):
    state = callback_query.data.split("|", 1)[1]
    chat_id = callback_query.message.chat.id

    if state == "on":
        await autoplay_on(chat_id)
        status = True
        alert = "Autoplay enabled ✅"
    else:
        await autoplay_off(chat_id)
        status = False
        alert = "Autoplay disabled ❌"

    await callback_query.answer(alert, show_alert=True)
    await callback_query.edit_message_text(
        autoplay_text(status),
        reply_markup=autoplay_markup(status),
        disable_web_page_preview=True,
    )
