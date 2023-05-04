import re
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud import add_inviter_recharge_amount_and_balance, add_user_balance_by_id, get_balance_by_user_id, get_flexible_data, get_invited_users_by_user_id, get_membership_expiration, get_used_card_codes, get_withdraw_amount_by_user_id, update_membership_expiration_with_activation_code, update_membership_expiration_with_hours

from app.db.database import get_db
from app.schemas.user import UserCreate
from app.security.auth import verify_token, verify_token_and_membership
from services.user_operations import create_user, get_user_by_id, get_user_by_username
from app.error_codes.error_codes import ErrorCode, ErrorMessage

router = APIRouter(prefix="/user", tags=["User"])



registered_ips = {}

@router.post("/register", response_class=JSONResponse)
async def register_user(user: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.client.host
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
        # 检查 user.invitee_id 是否为9位纯数字
        def validate_inviter_id(id: str):
            return re.match(r'^\d{9}$', id) is not None

        if not validate_inviter_id(user.invitee_id):
            user.invitee_id = "0" 
            
        mew_user = await create_user(db, user)       
        
        #新用户送1个小时
        await update_membership_expiration_with_hours(db, mew_user.id, 1)
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



#返回用户的id
@router.post("/get_user_id", response_class=JSONResponse)
async def get_user_id(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    return JSONResponse(content={"status": "Success", "user_id": str(user_id)})

# 根据id查询余额
@router.post("/get_user_balance", response_class=JSONResponse)
async def get_user_balance(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    balance = await get_balance_by_user_id(db, user_id)
    if balance is not None:
        return JSONResponse(content={"status": "Success", "balance": str(balance)})
    else:
        return JSONResponse(content={"status": "Error", "message": "User not found"}, status_code=404)

        
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

# # 5. 查询邀请过的人的id
# @router.post("/invited_user_ids", response_class=JSONResponse)
# async def get_user_invited_ids(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
#     user_id = int(token_data["sub"])
#     invited_ids = await get_invited_user_ids(db, user_id)
#     return JSONResponse(content={"status": "Success", "invited_user_ids": invited_ids})



# 1. 通过用户 ID 查询其邀请的用户信息（invited_user_names 字段）
@router.post("/invited_user_names", response_class=JSONResponse)
async def get_invited_user_names(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    invited_users = await get_invited_users_by_user_id(db, user_id)
    return JSONResponse(content={"status": "Success", "invited_user_names_dic": invited_users})

# 2. 通过用户 ID 和金额参数更新用户余额
@router.put("/add_balance", response_class=JSONResponse)
async def add_balance(amount: float, token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    await add_user_balance_by_id(db, user_id, amount)
    return JSONResponse(content={"status": "Success", "message": "User balance updated"})

# 3. 查询用户已提现金额
@router.post("/withdraw_amount", response_class=JSONResponse)
async def get_withdraw_amount(token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = int(token_data["sub"])
    withdraw_amount = await get_withdraw_amount_by_user_id(db, user_id)
    return JSONResponse(content={"status": "Success", "withdraw_amount": withdraw_amount})




class UpdateMembershipExpirationRequest(BaseModel):
    activation_code: str


# 根据卡密修改用户订阅时间
@router.post("/update_membership_expiration", response_class=JSONResponse)
async def update_membership_expiration_endpoint(
    request_data: UpdateMembershipExpirationRequest,
    token_data: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(token_data["sub"])
    activation_code = request_data.activation_code

    try:
        await update_membership_expiration_with_activation_code(db, user_id, activation_code)
        return JSONResponse(content={"status": "Success", "message": "Membership expiration updated successfully."})
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid activation code.")