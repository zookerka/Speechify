from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL
from .models import Base

# Replace with your actual database URL
engine = create_async_engine(DATABASE_URL)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
