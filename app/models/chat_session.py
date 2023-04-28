# chat_session.py
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Create a relationship to the User model
    user = relationship("User", back_populates="chat_sessions")

    # Create a relationship to the ChatMessage model
    chat_messages = relationship("ChatMessage", back_populates="chat_session")