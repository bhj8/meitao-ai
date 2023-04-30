# activation_code.py
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from app.db.database import Base

class ActivationCode(Base):
    __tablename__ = "activation_codes"

    # 卡密，一个长度为10的大写小字母和数字组成的str
    code = Column(String(10), primary_key=True, unique=True)

    # 卡密的属性，激活后增加的时长(按小时为单位）
    duration_in_hours = Column(Integer)

    # 卡密可使用次数
    usage_limit = Column(Integer)

    # 当卡密被使用后，一个储存使用他的用户的id的字段，采用JSON类型，默认为空列表
    used_by_user_ids = Column(JSON, default=list)
