from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.token import Token
from app.security.auth import create_access_token, pwd_context, ACCESS_TOKEN_EXPIRE_MINUTES
from services.user_operations import get_user_by_username
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

router = APIRouter()

async def authenticate_user(db, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user

@router.post("/token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
