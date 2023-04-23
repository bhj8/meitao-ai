from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.models.token import Token, VerifyTokenRequest
from app.security.auth import create_access_token, pwd_context, ACCESS_TOKEN_EXPIRE_MINUTES, verify_token
from services.user_operations import get_user_by_username
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

router = APIRouter(tags=["User"])

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
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "message": "Incorrect username or password",
                "headers": {"WWW-Authenticate": "Bearer"},
            }
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return JSONResponse(content={"access_token": access_token, "token_type": "bearer"})

@router.post("/verify")
async def verify_token_endpoint(request_data: VerifyTokenRequest):
    token = request_data.token
    is_token_valid = await verify_token(token)

    if is_token_valid:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Token is valid"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid token"}
        )
    
@router.post("/session")
async def get_session():
    # 你可以根据实际情况对这里的返回数据进行修改
    return {"auth": True, "model": "ChatGPTAPI"}
