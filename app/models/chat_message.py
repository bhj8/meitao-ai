from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
# chat_message.py (updated)
from sqlalchemy.orm import relationship
from app.db.database import Base
import datetime

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Update the relationship to the ChatSession model
    chat_session = relationship("ChatSession", back_populates="chat_messages")

    # __table_args__ = (UniqueConstraint('role', 'content', name='unique_role_content'),)
