import asyncio
from core.loader import setup_commands, setup_routers, dp, bot
from db.connection import init_db
from core.logger import logger


async def on_startup():

    logger.info("Starting up the bot...")

    await init_db()
    logger.info("Connected to Database")

    await setup_routers(dp)
    logger.info("Routers have been set up")

    await setup_commands()
    logger.info("Bot commands have been set up")

    logger.info("Starting polling...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logger.info("Running main entry point")
    asyncio.run(on_startup())
