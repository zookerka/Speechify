from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from core.config import LANGUAGE_MAP


async def reply_user_menu():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(text='Synthesize text into voice'),
                KeyboardButton(text='Settings')
            ]
        ]
    )
    return kb


async def reply_settings():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='Change voice actor')],
            [KeyboardButton(text='⬅️ Main menu')]
        ]
    )
    return kb


async def reply_back():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='⬅️ Main menu')]
        ]
    )
    return kb


async def reply_yes_or_no():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(text='Yes'),
                KeyboardButton(text='No')
            ],
            [KeyboardButton(text='⬅️ Main menu')]
        ]
    )
    return kb


async def reply_translation_languages(exclude_language=None):
    kb = ReplyKeyboardMarkup(resize_keyboard=True,
                             keyboard=[
                                 [KeyboardButton(text=i) for i in LANGUAGE_MAP if i != exclude_language],
                                 [KeyboardButton(text='⬅️ Main menu')]
                                 ])
    return kb


async def reply_text_to_speech():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='Convert it')],
            [KeyboardButton(text='⬅️ Main menu')]
        ]
    )
    return kb
