from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.user import UserCreate
from services.user_operations import create_user, get_user_by_username
from app.error_codes.error_codes import ErrorCode, ErrorMessage

router = APIRouter(tags=["User"])


registered_ips = {}

@router.post("/register", response_class=JSONResponse)
async def register_user(user: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host
    if client_ip in registered_ips:
        return JSONResponse(
            content={
                "status": ErrorCode.IP_ALREADY_REGISTERED,
                "message": ErrorMessage.IP_ALREADY_REGISTERED,
            },
        )
    try:
        existing_user = await get_user_by_username(db, user.username)
        if existing_user:
            return JSONResponse(
                content={
                    "status": ErrorCode.USER_ALREADY_EXISTS,
                    "message": ErrorMessage.USER_ALREADY_EXISTS,
                },
            )
        await create_user(db, user)
        registered_ips[client_ip] = True
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": 'Success'})
    except ValidationError as e:
        error_detail = e.errors()[0]
        error_message = error_detail["msg"]
        return JSONResponse(
            content={
                "status": ErrorCode.INVALID_INPUT,
                "message": ErrorMessage.INVALID_INPUT,
            },
        )