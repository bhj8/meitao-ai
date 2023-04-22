from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate
from app.security.password import get_password_hash
from tools.myutils import utils
import asyncio
from sqlalchemy.future import select
import Globals

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
