import datetime
import math
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activation_code import ActivationCode
from app.models.chat_session import ChatSession
from app.models.user import User
from app.schemas.user import UserCreate
from app.security.password import get_password_hash
from tools.myutils import utils
import asyncio
from sqlalchemy.future import select
import Globals

from app.models.chat_message import ChatMessage
from app.schemas.chat_message import ChatMessageCreate

# 根据用户 ID 获取用户
async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# 根据用户名获取用户
async def get_user_by_username(db: AsyncSession, username: str) -> User:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# 更新数据库中的余额
async def update_balance_in_database(db: AsyncSession, user_id: int, new_balance: float):
    user = await get_user_by_id(db, user_id)
    if user:
        user.balance = new_balance
        await db.commit()

# 根据用户 ID 增加用户余额
async def add_user_balance_by_id(db: AsyncSession, user_id: int, amount: float):
    user = await get_user_by_id(db, user_id)
    if user:
        user.balance += amount
        await db.commit()
        
# 创建用户
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_password = await get_password_hash(user.password)
    while True:
        user_id = utils. generate_random_digit_number(9)
        if not await get_user_by_id(db, user_id):
            break
    db_user = User(id=user_id, username=user.username, hashed_password=hashed_password, balance=int(Globals.INITIAL_USER_BALANCE), invitee_id=user.invitee_id)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# 根据用户 ID 获取金额
async def get_balance_by_user_id(db: AsyncSession, user_id: int):
    user = await get_user_by_id(db, user_id)
    if user:
        return user.balance
    return None

# 根据用户 ID 获取已提现金额
async def get_withdraw_amount_by_user_id(db: AsyncSession, user_id: int):
    user = await get_user_by_id(db, user_id)
    if user:
        return user.withdraw_amount
    return None

# 根据用户 ID 获取邀请的用户名的字典
async def get_invited_users_by_user_id(db: AsyncSession, user_id: int):
    user = await get_user_by_id(db, user_id)
    if user:
        return user.invited_user_names
    return None

# 修改其邀请人的余额
async def add_inviter_recharge_amount_and_balance(db: AsyncSession, user_id: int, amount: float,scale: float = 0.3):
    '''
    :param db: 数据库
    :param user_id: 用户 ID
    :param amount: 充值金额(分)
    :param scale: 返利比例
    :return: None   
    
    '''
    user = await get_user_by_id(db, user_id)
    if user and user.invitee_id != 0:
        inviter = await get_user_by_id(db, user.invitee_id)
        
        amount = math.ceil(amount * scale * 100) / 10000
        if inviter:
            # 更新邀请人的 recharge_amount
            invited_user_entry = inviter.invited_user_names.get(user.username)
            if invited_user_entry:
                invited_user_entry["recharge_amount"] += amount
            else:
                inviter.invited_user_names[user.username] = {"recharge_amount": amount}
            
            # 更新邀请人的余额
            await add_user_balance_by_id(db, inviter.id, amount)
            
            await db.commit()


#直接增加订阅时间
async def update_membership_expiration_with_hours(db: AsyncSession, user_id: int, hours: int):
    # 获取用户
    user = await get_user_by_id(db, user_id)

    # 检查小时参数是否大于0
    if hours > 0:
        # 获取当前时间
        now = datetime.datetime.utcnow()

        # 检查会员订阅是否已过期
        if user.membership_expiration < now:
            # 从当前时间开始计算新的到期时间
            user.membership_expiration = now + datetime.timedelta(hours=hours)
        else:
            # 从原到期时间开始计算新的到期时间
            user.membership_expiration += datetime.timedelta(hours=hours)

        # 提交更改到数据库
        await db.commit()
    else:
        raise ValueError("Invalid hours value.")




# 查询卡密码是多少
async def get_activation_code(db: AsyncSession, activation_code: str):
    stmt = select(ActivationCode).where(ActivationCode.code == activation_code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# 查询卡密码是否可用
async def is_activation_code_valid(db: AsyncSession, activation_code: str) -> bool:
    code = await get_activation_code(db, activation_code)
    if code and code.usage_limit > 0:
        return True
    return False


# 根据卡密修改用户订阅时间
async def update_membership_expiration_with_activation_code(db: AsyncSession, user_id: int, activation_code: str):
    # 获取用户
    user = await get_user_by_id(db, user_id)

    # 获取激活码
    code = await get_activation_code(db, activation_code)

    # 检查激活码是否存在且可用
    if code and code.usage_limit > 0:
        # 获取当前时间
        now = datetime.datetime.utcnow()

        # 检查会员订阅是否已过期
        if user.membership_expiration < now:
            # 从当前时间开始计算新的到期时间
            user.membership_expiration = now + datetime.timedelta(hours=code.duration_in_hours)
        else:
            # 从原到期时间开始计算新的到期时间
            user.membership_expiration += datetime.timedelta(hours=code.duration_in_hours)

        # 更新激活码的使用次数
        code.usage_limit -= 1

        # 将用户ID添加到激活码的使用列表
        code.used_by_user_ids.append(user_id)

        # 提交更改到数据库
        await db.commit()
    else:
        raise ValueError("Invalid activation code.")



# 查询会员到期时间
async def get_membership_expiration(db: AsyncSession, user_id: int) -> datetime:
    user = await get_user_by_id(db, user_id)
    if user:
        return user.membership_expiration

# 修改会员到期时间
async def update_membership_expiration(db: AsyncSession, user_id: int, new_expiration: datetime):
    user = await get_user_by_id(db, user_id)
    if user:
        user.membership_expiration = new_expiration
        await db.commit()

# 查询注册时间
async def get_registration_time(db: AsyncSession, user_id: int) -> datetime:
    user = await get_user_by_id(db, user_id)
    if user:
        return user.registration_time

# 查询使用过的卡密
async def get_used_card_codes(db: AsyncSession, user_id: int) -> list:
    user = await get_user_by_id(db, user_id)
    if user:
        return user.used_card_codes

# 查询灵活使用的字典
async def get_flexible_data(db: AsyncSession, user_id: int) -> dict:
    user = await get_user_by_id(db, user_id)
    if user:
        return user.flexible_data

# # 查询邀请过的人的id
# async def get_invited_user_ids(db: AsyncSession, user_id: int) -> list:
#     user = await get_user_by_id(db, user_id)
#     if user:
#         return user.invited_user_ids
    
    
    
    
    



# 创建一个聊天记录，返回创建的聊天记录
async def create_chat_message(db: AsyncSession, chat_message: ChatMessageCreate, chat_session_id: int) -> ChatMessage:
    db_chat_message = ChatMessage(chat_session_id=chat_session_id, role=chat_message.role, content=chat_message.content)
    db.add(db_chat_message)
    await db.commit()
    await db.refresh(db_chat_message)
    return db_chat_message

# 获取某个用户的所有聊天会话
async def get_chat_sessions_by_user_id(db: AsyncSession, user_id: int) -> list[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# 获取某个聊天会话的所有聊天记录
async def get_chat_messages_by_chat_session_id(db: AsyncSession, chat_session_id: int) -> list[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.chat_session_id == chat_session_id).order_by(ChatMessage.timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

# # 获取某个聊天记录
# async def get_chat_message_by_user_id_and_message_id(db: AsyncSession, chat_session_id: int, chat_message_id: int) -> ChatMessage:
#     stmt = select(ChatMessage).where(ChatMessage.chat_session_id == chat_session_id, ChatMessage.id == chat_message_id)
#     result = await db.execute(stmt)
#     return result.scalar_one_or_none()

# 获取某个聊天会话
async def get_chat_session_by_id(db: AsyncSession, chat_session_id: int) -> ChatSession:
    stmt = select(ChatSession).where(ChatSession.id == chat_session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# # 删除某个聊天记录
# async def delete_chat_message(db: AsyncSession, chat_session_id: int, chat_message_id: int) -> None:
#     chat_message = await get_chat_message_by_user_id_and_message_id(db, chat_session_id, chat_message_id)
    
#     if chat_message is not None:
#         await db.delete(chat_message)
#         await db.commit()

# 删除某个聊天会话的所有聊天记录
async def delete_all_chat_messages(db: AsyncSession, chat_session_id: int) -> None:
    chat_messages = await get_chat_messages_by_chat_session_id(db, chat_session_id)
    
    if chat_messages:
        for chat_message in chat_messages:
            await db.delete(chat_message)
        await db.commit()

# 删除某个聊天会话
async def delete_chat_session(db: AsyncSession, user_id: int, chat_session_id: int) -> None:
    chat_session = await get_chat_session_by_user_id_and_chat_session_id(db, user_id, chat_session_id)
    if chat_session is not None:
        await delete_all_chat_messages(db, chat_session_id)
        await db.delete(chat_session)
        await db.commit()

# 创建一个聊天会话，返回创建的聊天会话
async def create_chat_session(db: AsyncSession, user_id: int, chat_session_id: int) -> ChatSession:
    db_chat_session = ChatSession(id=chat_session_id, user_id=user_id)
    db.add(db_chat_session)
    await db.commit()
    await db.refresh(db_chat_session)
    return db_chat_session


# 获取某个用户的所有聊天会话
async def get_chat_session_by_user_id_and_chat_session_id(db: AsyncSession, user_id: int, chat_session_id: int) -> ChatSession:
    stmt = select(ChatSession).where(ChatSession.user_id == user_id).where(ChatSession.id == chat_session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()












###########工具类###########
from tools.myutils import utils

# 创建一个新的激活码
async def create_activation_code(db: AsyncSession, duration_in_hours: int, usage_limit: int):
    '''
    密的属性，激活后增加的时长(按小时为单位）
    
    '''
    # 生成一个长度为10的大小写字母和数字组成的随机字符串
    activation_code_str = utils.generate_alphanumeric_string(10)

    # 创建一个新的激活码对象
    new_activation_code = ActivationCode(
        code=activation_code_str,
        duration_in_hours=duration_in_hours,
        usage_limit=usage_limit
    )

    # 将新的激活码对象添加到数据库中
    db.add(new_activation_code)
    await db.commit()
    await db.refresh(new_activation_code)

    return [activation_code_str,duration_in_hours,usage_limit]
