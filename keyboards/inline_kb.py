from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import ENG_VOICE_ACTORS


async def inline_voice_actors():
    builder = InlineKeyboardBuilder()
    for i in ENG_VOICE_ACTORS:
        builder.button(text=i, callback_data=i)
    builder.adjust(3, 3)

    return builder.as_markup()
