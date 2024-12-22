import os
from dotenv import load_dotenv


load_dotenv()

# AWS region
REGION_NAME = os.getenv("REGION_NAME")

# TG_bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# AWS keys
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")

# Async db url: postgresql+asyncpg://username:password@hostname:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# Better Stack token
LOG_TOKEN = os.getenv("LOG_TOKEN")

LANGUAGE_MAP = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "Russian": "ru"
}

ENG_VOICE_ACTORS = ['Joanna', 'Matthew', 'Salli', 'Justin', 'Kimberly', 'Ivy', 'Raveena', 'Joey']
