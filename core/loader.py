from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import commands, common
from core.config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def setup_routers(dp: Dispatcher):
    dp.include_router(commands.router)
    dp.include_router(common.router)


async def setup_commands():
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Получить помощь"),
    ]
    await bot.set_my_commands(commands)
