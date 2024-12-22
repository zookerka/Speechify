from aiogram import Router
from aiogram.filters import Command
from db.connection import async_session
from db.crud import create_user
from aiogram.types import Message

from keyboards.reply_kb import reply_user_menu

from core.logger import logger


router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    """
    Handle the /start command to welcome the user and create a user entry in the database.
    """
    try:
        user_id = message.from_user.id
        logger.info(f"User {user_id} initiated the /start command.")

        async with async_session() as session:
            await create_user(session, user_id)

        await message.answer("Welcome to Speechify! Here, you can enter text, and it will be read out loud in your chosen voice and language."
                             "Try it out and hear how words sound in different languages and voices!",
                             reply_markup=await reply_user_menu())
    except Exception as e:
        logger.error(f"Unexpected error in start_command for user {message.from_user.id}: {e}")
        await message.answer("An unexpected error occurred, please try again later.")
