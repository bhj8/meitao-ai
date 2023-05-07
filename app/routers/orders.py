import re
import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud import add_inviter_recharge_amount_and_balance, get_user_by_id, update_membership_expiration_with_activation_code, update_membership_expiration_with_hours
from app.db.database import get_db
from app.schemas.user import UserCreate
from app.security.auth import verify_token, verify_token_and_membership
from app.error_codes.error_codes import ErrorCode, ErrorMessage
from app.schemas.orders import PlanNameResponse
from app.security.rate_limiter import rate_limiter
from tools.my_crypt import decrypt_message, encrypt_message
from tools.mylog import logger
import Globals

router = APIRouter(prefix="/orders", tags=["Orders"])





class PaymentCallbackData(BaseModel):
    user_id: int
    out_trade_no: str
    amount: float
    goods: str
    attach: dict



temporary_paid_orders={}
@router.post("/payment_callback", response_class=JSONResponse)
async def payment_success_callback(request: Request, callback_data: PaymentCallbackData , db: AsyncSession = Depends(get_db)):
    user_id = callback_data.user_id
    out_trade_no = callback_data.out_trade_no
    amount = callback_data.amount
    goods = callback_data.goods

    if out_trade_no not in temporary_paid_orders:
        # 1. 修改其订阅时间
        # 假设 goods 中包含订阅时长（以小时为单位），您可以根据实际情况进行修改
        subscription_duration = time_hour_dic[goods]
        await update_membership_expiration_with_hours(db, user_id, subscription_duration)

        # 2. 修改其邀请人的已邀请过的用户信息（如果不是0，而且能查到的话）
        user = await get_user_by_id(db, user_id)
        if user and user.invitee_id != 0:
            await add_inviter_recharge_amount_and_balance(db, user_id, amount)

        # 3. 将订单号添加到到这个用户个人信息
        if user:
            user.paid_orders.append(out_trade_no)
            await db.commit()
            
        with open("orders.txt", "a") as file:
            file.write(f"用户ID: {user_id}, 用户名: {user.username}, 商品: {goods}, 金额: {amount}, 订单ID: {out_trade_no}，邀请人ID: {user.invitee_id}\n")
        logger.debug(f"用户ID: {user_id}, 用户名: {user.username}, 商品: {goods}, 金额: {amount}, 订单ID: {out_trade_no}，邀请人ID: {user.invitee_id}")

        # 4. 将订单号存放在临时字典里。以便前端频繁回调检查
        # 假设已经定义了一个名为 temporary_paid_orders 的全局字典
        temporary_paid_orders[out_trade_no] = {"user_id": user_id, "amount": amount, "goods": goods}
    return JSONResponse(content={"status": "Success", "message": "Payment processed successfully."})

class OrderStatusRequest(BaseModel):
    order_number: str

@router.post("/check_order_status", response_class=JSONResponse)
async def check_order_status(order_status_request: OrderStatusRequest):
    order_number = order_status_request.order_number

    if order_number in temporary_paid_orders:
        return JSONResponse(content={"status": "Success", "message": "ok"})
    else:
        return JSONResponse(content={"status": "Success", "message": "fail"})
    
    

time_hour_dic={"套餐1":30*24,"套餐2":90*24,"套餐3":365*24,"套餐4":100*365*24,"测试":1}
price_dic={"套餐1":3800,"套餐2":9800,"套餐3":19800,"套餐4":99900,"测试":1}

from random import sample
from string import ascii_letters, digits

# 订单号和二维码链接
@router.post("/create", response_class=JSONResponse)
async def get_user_id( plan: PlanNameResponse,token_data: dict = Depends(verify_token), db: AsyncSession = Depends(get_db),rate_limited: None = Depends(rate_limiter)):
    user_id = int(token_data["sub"])
    
    # 你可以在这里根据 plan_name 处理订单创建逻辑，获取二维码链接和订单号
    # 以下为示例数据，你需要替换为实际数据
    qr_code_url = "https://example.com/qr-code.png"
    out_trade_no = ''.join(sample(ascii_letters + digits, 16))
    response =  await get_order_async__request(user_id, plan.plan_name, price_dic[plan.plan_name], Globals.MY_PAY_AES_KEY)
    
    # 解析响应
    if response:
        code_url = response['code_url']
        out_trade_no = response['out_trade_no']

        return JSONResponse(content={"status": "Success", "user_id": str(user_id), "qrCodeUrl": code_url, "orderNumber": out_trade_no})
    else:
        return JSONResponse(content={"status": "Failed", "message": "Failed to get response from server."})
    
    
import requests
import json
import asyncio

async def get_order_async__request(user_id, goods, amount, encryption_key, retries=3):
    for i in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "user_id": user_id,
                    "goods": goods,
                    "amount": amount
                }

                # 将数据转换为 JSON 格式并加密
                json_data = json.dumps(data)
                encrypted_message = encrypt_message(json_data, encryption_key)

                # 发送 POST 请求到指定端点
                url = "http://www.ahuismart.com/l0hfnNSBUKZVFXGx123/pay/t1"
                async with session.post(url, data={"message": encrypted_message}) as response:
                    if response.status == 200:
                        # 获取响应中的加密信息并解密
                        response_data = await response.json()
                        encrypted_response_message = response_data["message"]
                        decrypted_response_message = decrypt_message(encrypted_response_message, encryption_key)
                        return decrypted_response_message
                    else:
                        print(f"Request failed with status code {response.status}")
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Request failed with exception {e}. Retrying ({i + 1}/{retries})")
            await asyncio.sleep(1)
    print(f"Request failed after {retries} retries")
    return None