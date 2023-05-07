from datetime import datetime, timedelta
import random
import re
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.db.crud import add_inviter_recharge_amount_and_balance, add_user_balance_by_id, get_balance_by_user_id, get_flexible_data, get_invited_users_by_user_id, get_membership_expiration, get_used_card_codes, get_withdraw_amount_by_user_id, update_membership_expiration_with_activation_code, update_membership_expiration_with_hours

from app.db.database import get_db
from app.routers.authentication import login_access_token, login_access_token_nopassword
from app.schemas.user import UserCreate
from app.security.auth import verify_token, verify_token_and_membership
from app.security.rate_limiter import rate_limiter
from services.user_operations import create_user, get_user_by_id, get_user_by_username
from app.error_codes.error_codes import ErrorCode, ErrorMessage
from tools.api_tx_sms import TencentSmsSender
from tools.mylog import logger

router = APIRouter(prefix="/user", tags=["User"])


registered_ips = {}
TIME_BETWEEN_REQUESTS = timedelta(minutes=0.5)

@router.post("/register_or_login", response_class=JSONResponse)
async def register_or_login(user: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    
    #基于IP限制
    # client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.client.host
    # if client_ip in registered_ips:
    #     time_since_last_request = datetime.now() - registered_ips[client_ip]
    #     if time_since_last_request < TIME_BETWEEN_REQUESTS:
    #         return JSONResponse(content={"status": "Error", "message": "Request limit exceeded"}, status_code=429)
    #     else:
    #         registered_ips[client_ip] = datetime.now()
    # else:
    #     registered_ips[client_ip] = datetime.now()
        
    # 检查验证码
    if phone_number_verification_codes.get(user.username) != user.verification_code:
        return JSONResponse(
            content={
                "status": ErrorCode.VERIFICATION_CODE_INCORRECT,
                "message": ErrorMessage.VERIFICATION_CODE_INCORRECT,
            },
        )

    # 检查用户是否存在
    existing_user = await get_user_by_username(db, user.username)

    if existing_user:
        # 用户存在，执行登录逻辑
        return await login_access_token_nopassword(db, username=user.username)
    else:
        # 用户不存在，执行注册逻辑并直接返回访问令牌
        return await register_user(user, request, db)

# @router.post("/register", response_class=JSONResponse)
async def register_user(user: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    #基于IP限制
    # client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.client.host
    # if client_ip in ip_request_count:
    #     time_since_last_request = datetime.now() - ip_request_count[client_ip]
    #     if time_since_last_request < TIME_BETWEEN_REQUESTS:
    #         return JSONResponse(content={"status": "Error", "message": "Request limit exceeded"}, status_code=429)
    #     else:
    #         ip_request_count[client_ip] = datetime.now()
    # else:
    #     ip_request_count[client_ip] = datetime.now()
        
        
    if phone_number_verification_codes.get(user.username) != user.verification_code:
        return JSONResponse(
            content={
                "status": ErrorCode.VERIFICATION_CODE_INCORRECT,
                "message": ErrorMessage.VERIFICATION_CODE_INCORRECT,
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
            
        new_user = await create_user(db, user)       
        
        logger.debug(f"New user created: {new_user.username}")
        #新用户送1个小时
        await update_membership_expiration_with_hours(db, new_user.id, 1)
         # 在注册成功后，直接生成并返回访问令牌
        return  await login_access_token_nopassword(db, username=new_user.username)
    
    
    except ValidationError as e:
        error_detail = e.errors()[0]
        error_message = error_detail["msg"]
        return JSONResponse(
            content={
                "status": ErrorCode.INVALID_INPUT,
                "message": ErrorMessage.INVALID_INPUT,
            },
        )




api_tx_sms = TencentSmsSender()  # Initialize your SMS sender class
ip_request_count = {}  # A temporary dictionary to store the IP address and count
phone_number_verification_codes = {"15079857414":"025025"}  # A temporary dictionary to store phone numbers and their verification codes
MAX_REQUESTS_PER_IP = 5  # Set the maximum requests per IP, you can change this value

class PhoneNumberRequest(BaseModel):
    phone_number:  str


@router.post("/send_verification_code", response_class=JSONResponse)
async def send_verification_code(phone_number_request: PhoneNumberRequest, request: Request, db: AsyncSession = Depends(get_db)):
    global ip_request_count
    global phone_number_verification_codes

    # Get the client's IP address
    client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.client.host

    # Remove expired requests
    now = datetime.now()
    if client_ip in ip_request_count:
        ip_request_count[client_ip] = [t for t in ip_request_count[client_ip] if now - t < timedelta(hours=24)]

    # Check if the IP has reached the request limit
    if client_ip in ip_request_count and len(ip_request_count[client_ip]) >= MAX_REQUESTS_PER_IP:
        return JSONResponse(content={"status": "Error", "message": "你的网络已达到今日最大短信限制，请明天再试"})

    # Update the IP request count
    if client_ip not in ip_request_count:
        ip_request_count[client_ip] = []
    ip_request_count[client_ip].append(now)

    # Generate a random 6-digit verification code
    verification_code = random.randint(100000, 999999)
    verification_code =str(verification_code)


    try:
        # Call the send_sms method from your SMS sender class
        api_tx_sms.send_sms(phone_number_request.phone_number, [str(verification_code)])
        
        #成功了再改验证码信息
        # Store the phone number and verification code in the temporary dictionary
        phone_number_verification_codes[phone_number_request.phone_number] = verification_code
        return JSONResponse(content={"status": "Success", "message": "Verification code sent"})
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return JSONResponse(content={"status": "Error", "message": str(e)}, status_code=500)










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