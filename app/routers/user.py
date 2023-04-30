import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud import get_flexible_data, get_invited_user_ids, get_membership_expiration, get_used_card_codes, update_membership_expiration

from app.db.database import get_db
from app.schemas.user import UserCreate
from app.security.auth import verify_token, verify_token_and_membership
from services.user_operations import create_user, get_user_by_id, get_user_by_username
from app.error_codes.error_codes import ErrorCode, ErrorMessage

router = APIRouter(prefix="/user", tags=["User"])



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
        
        
        
# 1. 查询会员到期时间
@router.post("/get_membership_expiration", response_class=JSONResponse)
async def get_membership_expiration_endpoint(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    expiration = await get_membership_expiration(db, user_id)
    return JSONResponse(content={"status": "Success", "membership_expiration": str(expiration)})

# # 2. 修改会员到期时间
# @router.put("/update_membership_expiration", response_class=JSONResponse)
# async def update_membership_expiration_endpoint(user_id: int, new_expiration: datetime, db: AsyncSession = Depends(get_db)):
#     await update_membership_expiration(db, user_id, new_expiration)
#     return JSONResponse(content={"status": "Success", "message": "Membership expiration updated"})

# 2. 查询user.info
@router.post("/user_info", response_class=JSONResponse)
async def get_user_info(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    user = await get_user_by_id(db, user_id)
    user_info = user.dict()
    del user_info["hashed_password"]
    return JSONResponse(content={"status": "Success", "user_info": user_info})

# 3. 查询使用过的卡密
@router.post("/used_card_codes", response_class=JSONResponse)
async def get_used_codes(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    used_codes = await get_used_card_codes(db, user_id)
    return JSONResponse(content={"status": "Success", "used_card_codes": used_codes})

# 4. 查询灵活使用的字典
@router.post("/flexible_data", response_class=JSONResponse)
async def get_user_flexible_data(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    flexible_data = await get_flexible_data(db, user_id)
    return JSONResponse(content={"status": "Success", "flexible_data": flexible_data})

# 5. 查询邀请过的人的id
@router.post("/invited_user_ids", response_class=JSONResponse)
async def get_user_invited_ids(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    invited_ids = await get_invited_user_ids(db, user_id)
    return JSONResponse(content={"status": "Success", "invited_user_ids": invited_ids})
