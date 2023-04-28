from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.error_codes.error_codes import ErrorCode, ErrorMessage
from app.schemas.token import Token, VerifyTokenRequest
from app.schemas.session import SessionResponse
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
            content={
                    "status": ErrorCode.PASSWORD_NOT_VALID,
                    "message": ErrorMessage.PASSWORD_NOT_VALID,
            }
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return JSONResponse(content={"status": "Success","data":{ "access_token": access_token, "token_type": "bearer"}})

@router.post("/verify")
async def verify_token_endpoint(request_data: VerifyTokenRequest):
    token = request_data.token
    is_token_valid = await verify_token(token)

    if is_token_valid:
        return JSONResponse(            
            content={
                "status": "Success",
                "message": "Token is valid",},
        )
    else:
        return JSONResponse(
            content={
                "status": ErrorCode.TOKEN_INVALID,
                "message": ErrorCode.TOKEN_INVALID,},
        )
    


# @router.post("/session", response_model=SessionResponse)
# async def session() -> SessionResponse:
#     try:
#         data = {
#             "auth": False,
#             "model": "ChatGPTUnofficialProxyAPI",
#         }
#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content=data
#         )
#     except Exception as error:
#         return JSONResponse(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             content={"message": "server down"}
#         )

# from pydantic import BaseModel
# class SessionResponse(BaseModel):
#     auth: bool
#     model: str

# def is_not_empty_string(s: str) -> bool:
#     return bool(s and s.strip())

# @router.post("/session", response_model=SessionResponse)
# async def session() -> SessionResponse:
#     try:
#         has_auth = True

#         data = {
#             "auth": has_auth,
#             "model": "ChatGPTUnofficialProxyAPI",
#         }

#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content=data
#         )

#     except Exception as error:
#         return JSONResponse(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             content={"message": "server down"}
#         )