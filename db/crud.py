from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import User

from core.logger import logger


async def create_user(session: AsyncSession, user_id: int, eng_voice_actor: str = "") -> User:
    """Create a new user in the database or return the existing user.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user to create.
        eng_voice_actor (str): The name of the user's voice actor.

    Returns:
        User: The created or existing user.
    """
    logger.info(f"Attempting to create a user with ID {user_id}.")
    result = await session.execute(select(User).where(User.user_id == user_id))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.info(f"User with ID {user_id} already exists.")
        return existing_user
    logger.info(f"User with ID {user_id} does not exist. Creating a new user.")

    new_user = User(user_id=user_id, eng_voice_actor=eng_voice_actor)
    session.add(new_user)

    await session.commit()
    await session.refresh(new_user)

    logger.info(f"User with ID {user_id} created successfully.")

    return new_user


async def get_voice_actor(session: AsyncSession, user_id: int) -> str | None:
    """Retrieve the voice actor for a specified user by user_id.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user to retrieve the voice actor for.

    Returns:
        str | None: The name of the voice actor if found, otherwise None.
    """
    logger.info(f"Retrieving voice actor for user ID {user_id}.")
    user = await get_user(session, user_id)
    if user:
        logger.info(f"Found voice actor for user ID {user_id}: {user.eng_voice_actor}")
    else:
        logger.warning(f"No voice actor found for user ID {user_id}.")
    return user.eng_voice_actor if user else None


async def update_voice_actor(session: AsyncSession, user_id: int, new_voice_actor: str) -> bool:
    """Update the eng_voice_actor for a specified user.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user to update.
        new_voice_actor (str): The new voice actor name.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    logger.info(f"Updating voice actor for user ID {user_id} to '{new_voice_actor}'.")
    user = await get_user(session, user_id)
    if user:
        logger.info(f"User with ID {user_id} found. Proceeding with update.")
        user.eng_voice_actor = new_voice_actor
        await session.commit()
        logger.info(f"Voice actor for user ID {user_id} updated successfully.")
        return True
    else:
        logger.warning(f"User with ID {user_id} not found. Update failed.")
    return False


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Retrieve a user by user_id.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        User | None: The user if found, otherwise None.
    """
    logger.info(f"Retrieving user with ID {user_id}.")
    result = await session.execute(select(User).filter(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        logger.info(f"User with ID {user_id} retrieved successfully.")
    else:
        logger.warning(f"User with ID {user_id} not found.")
    return user
