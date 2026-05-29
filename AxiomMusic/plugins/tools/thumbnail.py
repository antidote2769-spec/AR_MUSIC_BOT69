from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from AxiomMusic import app
from AxiomMusic.utils.database import is_thumbmode, thumb_off, thumb_on
from AxiomMusic.utils.decorators.admins import ActualAdminCB, AdminActual
from config import BANNED_USERS


def thumbnail_markup(status: bool):
    toggle_text = "ᴅɪsᴀʙʟᴇ ❌" if status else "ᴇɴᴀʙʟᴇ ✅"
    toggle_state = "off" if status else "on"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    toggle_text,
                    callback_data=f"thumbnail_toggle|{toggle_state}",
                )
            ],
            [InlineKeyboardButton("⋞ ᴄʟᴏsє ⋟", callback_data="close")],
        ]
    )


def thumbnail_text(status: bool):
    current = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"
    return (
        "<b>𝚻ʜ꧊‌𝛖ϻβηᴧιℓ 𝚺ᴇᴛᴛɪɴɢs</b>\n\n"
        f"<b>ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs:</b> {current}\n\n"
        "<blockquote>Disabled hone par /play ke baad custom generated "
        "thumbnail PNG nahi banegi; bot normal streaming card/buttons ke saath "
        "default image use karega.</blockquote>"
    )


@app.on_message(filters.command(["thumbnail", "thum"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def thumbnail_cmd(_, message: Message, __):
    status = await is_thumbmode(message.chat.id)
    await message.reply_text(
        thumbnail_text(status),
        reply_markup=thumbnail_markup(status),
        disable_web_page_preview=True,
    )


@app.on_callback_query(filters.regex(r"^thumbnail_toggle\|(on|off)$") & ~BANNED_USERS)
@ActualAdminCB
async def thumbnail_callback(_, callback_query: CallbackQuery, __):
    state = callback_query.data.split("|", 1)[1]
    chat_id = callback_query.message.chat.id

    if state == "on":
        await thumb_on(chat_id)
        status = True
        alert = "Thumbnail enabled ✅"
    else:
        await thumb_off(chat_id)
        status = False
        alert = "Thumbnail disabled ❌"

    await callback_query.answer(alert, show_alert=True)
    await callback_query.edit_message_text(
        thumbnail_text(status),
        reply_markup=thumbnail_markup(status),
        disable_web_page_preview=True,
    )
