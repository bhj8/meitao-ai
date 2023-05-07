from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., regex="^\\d{11}$")
    password: str = Field(..., min_length=6, max_length=128, regex="^[ -~]+$")
    invitee_id: str = "0" # 新增 invitee_id 字段，默认值为 0
    verification_code: str = Field(..., regex="^\\d{6}$")
