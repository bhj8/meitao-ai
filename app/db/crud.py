from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.security.password import get_password_hash
from tools.myutils import utils
# 查询用户根据ID
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# 查询用户根据用户名
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def update_balance_in_database(db: Session, user_id: int, new_balance: float):
    user = get_user_by_id(db, user_id)
    if user:
        user.balance = new_balance
        db.commit()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    while True:
        user_id = utils.generate_12_digit_number()
        if not get_user_by_id(db, user_id):
            break
    db_user = User(id=user_id, username=user.username, hashed_password=hashed_password, balance=0)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
