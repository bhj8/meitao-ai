from sqlalchemy.orm import Session
from app.db.crud import get_user_by_id as crud_get_user_by_id, get_user_by_username as crud_get_user_by_username, update_balance_in_database, create_user as crud_create_user
from app.models.user import User
from app.schemas.user import UserCreate

def get_user_by_id(db: Session, user_id: int):
    return crud_get_user_by_id(db, user_id)

def get_user_by_username(db: Session, username: str):
    return crud_get_user_by_username(db, username)

def create_user(db: Session, user: UserCreate):
    return crud_create_user(db, user)

def update_user_balance(db: Session, user_id: int, cost: float):
    # Retrieve user data from the database using user_id
    user = get_user_by_id(db, user_id)
    if user:
        new_balance = user.balance - cost

        # Update user's balance in the database
        update_balance_in_database(db, user_id, new_balance)
