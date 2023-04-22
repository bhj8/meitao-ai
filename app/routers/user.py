from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.user import UserCreate
from services.user_operations import create_user, get_user_by_username
import asyncio

router = APIRouter(tags=["User"])

@router.post("/register", response_class=JSONResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_username(db, user.username)
    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": 400,
                "message": "Username already exists",
            },
        )
    await create_user(db, user)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User registered successfully"})
