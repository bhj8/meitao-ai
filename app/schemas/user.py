from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., regex="^\\d{11}$")
    password: str = Field(..., min_length=6, max_length=128, regex="^[ -~]+$")
