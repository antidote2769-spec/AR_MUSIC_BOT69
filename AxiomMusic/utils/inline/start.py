from pyrogram.types import InlineKeyboardButton
from pyrogram.enums import ButtonStyle
import config
from AxiomMusic import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{app.username}?startgroup=true", style=ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT, style=ButtonStyle.SECONDARY),
        ],
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_back_helper", style=ButtonStyle.PRIMARY),
        ],
    ]
    return buttons
