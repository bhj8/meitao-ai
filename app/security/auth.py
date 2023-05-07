from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
import Globals
from fastapi.responses import JSONResponse

from app.db.database import get_db
from services.user_operations import get_user_by_id
SECRET_KEY = Globals.SECRET_KEY
ALGORITHM = Globals.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Globals.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print("JWTError:", e)
        raise HTTPException(status_code=401, detail={"status": "Unauthorized", "detail": "Invalid token"})

async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



async def verify_token_and_membership(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    # 从令牌数据中获取用户名
    user_id = int(token_data["sub"])

    # 从数据库中查找与用户关联的帐户信息
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(status_code=401, detail={"status": "Unauthorized", "detail": "Invalid token"})

    # 检查会员是否在有效期内
    current_time = datetime.utcnow()
    if user.membership_expiration < current_time:
        raise HTTPException(
            status_code=1020, detail={"status": "Forbidden", "detail": "Membership expired"}
        )

    return token_data


# async def verify_token_and_balance(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
#     # 从令牌数据中获取用户名
#     user_id = int(token_data["sub"])

#     # 从数据库中查找与用户关联的帐户信息
#     user = await get_user_by_id(db, user_id)

#     if user is None:
#         raise HTTPException(status_code=401, detail={"status": "Unauthorized", "detail": "Invalid token"})

#     # 检查余额是否充足
#     # minimum_balance_required = 10  # 您可以根据需求设置所需的最低余额
#     # if user.balance < minimum_balance_required:
#     #     raise HTTPException(
#     #         status_code=402, detail="Insufficient balance"
#     #     )

#     return token_data