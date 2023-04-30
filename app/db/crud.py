from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat_session import ChatSession
from app.models.user import User
from app.schemas.user import UserCreate
from app.security.password import get_password_hash
from tools.myutils import utils
import asyncio
from sqlalchemy.future import select
import Globals

from app.models.chat_message import ChatMessage
from app.schemas.chat_message import ChatMessageCreate

async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> User:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_balance_in_database(db: AsyncSession, user_id: int, new_balance: float):
    user = await get_user_by_id(db, user_id)
    if user:
        user.balance = new_balance
        await db.commit()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_password = await get_password_hash(user.password)
    while True:
        user_id = utils.generate_int32_digit_number()
        if not await get_user_by_id(db, user_id):
            break
    db_user = User(id=user_id, username=user.username, hashed_password=hashed_password, balance=int(Globals.INITIAL_USER_BALANCE))
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user




# 创建一个聊天记录，返回创建的聊天记录
async def create_chat_message(db: AsyncSession, chat_message: ChatMessageCreate, chat_session_id: int) -> ChatMessage:
    db_chat_message = ChatMessage(chat_session_id=chat_session_id, role=chat_message.role, content=chat_message.content)
    db.add(db_chat_message)
    await db.commit()
    await db.refresh(db_chat_message)
    return db_chat_message

# 获取某个用户的所有聊天会话
async def get_chat_sessions_by_user_id(db: AsyncSession, user_id: int) -> list[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# 获取某个聊天会话的所有聊天记录
async def get_chat_messages_by_chat_session_id(db: AsyncSession, chat_session_id: int) -> list[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.chat_session_id == chat_session_id).order_by(ChatMessage.timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

# 获取某个聊天记录
async def get_chat_message_by_user_id_and_message_id(db: AsyncSession, chat_session_id: int, chat_message_id: int) -> ChatMessage:
    stmt = select(ChatMessage).where(ChatMessage.chat_session_id == chat_session_id, ChatMessage.id == chat_message_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# 获取某个聊天会话
async def get_chat_session_by_id(db: AsyncSession, chat_session_id: int) -> ChatSession:
    stmt = select(ChatSession).where(ChatSession.id == chat_session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# 删除某个聊天记录
async def delete_chat_message(db: AsyncSession, chat_session_id: int, chat_message_id: int) -> None:
    chat_message = await get_chat_message_by_user_id_and_message_id(db, chat_session_id, chat_message_id)
    
    if chat_message is not None:
        await db.delete(chat_message)
        await db.commit()

# 删除某个聊天会话的所有聊天记录
async def delete_all_chat_messages(db: AsyncSession, chat_session_id: int) -> None:
    chat_messages = await get_chat_messages_by_chat_session_id(db, chat_session_id)
    
    if chat_messages:
        for chat_message in chat_messages:
            await db.delete(chat_message)
        await db.commit()

# 删除某个聊天会话
async def delete_chat_session(db: AsyncSession, user_id: int, chat_session_id: int) -> None:
    chat_session = await get_chat_session_by_user_id_and_chat_session_id(db, user_id, chat_session_id)
    if chat_session is not None:
        await delete_all_chat_messages(db, chat_session_id)
        await db.delete(chat_session)
        await db.commit()

# 创建一个聊天会话，返回创建的聊天会话
async def create_chat_session(db: AsyncSession, user_id: int, chat_session_id: int) -> ChatSession:
    db_chat_session = ChatSession(id=chat_session_id, user_id=user_id)
    db.add(db_chat_session)
    await db.commit()
    await db.refresh(db_chat_session)
    return db_chat_session


# 获取某个用户的所有聊天会话
async def get_chat_session_by_user_id_and_chat_session_id(db: AsyncSession, user_id: int, chat_session_id: int) -> ChatSession:
    stmt = select(ChatSession).where(ChatSession.user_id == user_id).where(ChatSession.id == chat_session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
