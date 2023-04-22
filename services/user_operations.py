from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud import get_user_by_id as crud_get_user_by_id, get_user_by_username as crud_get_user_by_username, update_balance_in_database, create_user as crud_create_user
from app.models.user import User
from app.schemas.user import UserCreate

async def get_user_by_id(db: AsyncSession, user_id: int)-> User:
    return await crud_get_user_by_id(db, user_id)

async def get_user_by_username(db: AsyncSession, username: str)-> User:
    return await crud_get_user_by_username(db, username)

async def create_user(db: AsyncSession, user: UserCreate)-> User:
    return await crud_create_user(db, user)

async def update_user_balance(db: AsyncSession, user_id: int, cost: int):
    # Retrieve user data from the database using user_id
    user = await get_user_by_id(db, user_id)
    if user:
        new_balance = user.balance - cost

        # Update user's balance in the database
        await update_balance_in_database(db, user_id, new_balance)
