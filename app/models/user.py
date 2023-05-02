# user.py (updated)
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)   
    
    hashed_password = Column(String)
    
    # 余额，默认值为0
    balance = Column(Integer, default=0)
    
    #已提现金额
    withdraw_amount = Column(Integer, default=0)

    # 积分余额，默认值为0
    points_balance = Column(Integer, default=0)

    # 会员到期时间，默认值为注册时间
    membership_expiration = Column(DateTime, default=datetime.utcnow)

    # 注册时间，默认值为当前UTC时间
    registration_time = Column(DateTime, default=datetime.utcnow)

    # 已经使用过的卡密，采用JSON类型，默认为空列表
    used_card_codes = Column(JSON, default=list)

    # 已经邀请过的用户ID，采用JSON类型，默认为空字典
    # 字典结构： {invited_user_name: {"recharge_amount": 0}}
    invited_user_names = Column(JSON, default=dict)

    # 被邀请人的ID，唯一
    invitee_id = Column(Integer,default=0)
    


    # 一个灵活的存储信息的字典，以便未来在不迁移数据库的前提下，快速的存一些临时的资料
    flexible_data = Column(JSON, default=dict)

    # Create a relationship to the ChatSession model
    chat_sessions = relationship("ChatSession", back_populates="user")
