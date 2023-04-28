# user.py (updated)
from sqlalchemy import Column, Integer, String
from app.db.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    balance = Column(Integer)
    hashed_password = Column(String)

    # Create a relationship to the ChatSession model
    chat_sessions = relationship("ChatSession", back_populates="user")