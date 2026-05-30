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


from pyrogram.types import InlineKeyboardButton
from pyrogram.enums import ButtonStyle
import config
from AxiomMusic import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true", style=ButtonStyle.SECONDARY,
            )
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_CHANNEL, style=ButtonStyle.SECONDARY,
            ),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true", style=ButtonStyle.SECONDARY,
            ),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], user_id=config.OWNER_ID, style=ButtonStyle.SECONDARY),
            InlineKeyboardButton(text="📼ʏᴛ-ᴀᴘɪ", callback_data="api_status", style=ButtonStyle.SECONDARY),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_6"],
                url=config.SUPPORT_CHAT, style=ButtonStyle.SECONDARY,
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_CHANNEL, style=ButtonStyle.SECONDARY,
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_4"],
                callback_data="settings_back_helper", style=ButtonStyle.SECONDARY,
            ),
        ],
    ]
    return buttons
