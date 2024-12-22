from sqlalchemy import Integer, Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User (Base):
    """Represents a user in the database."""
    __tablename__ = 'User'
    user_id = Column(Integer, primary_key=True)
    eng_voice_actor = Column(String)
