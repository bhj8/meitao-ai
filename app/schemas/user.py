from pydantic import BaseModel,Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, regex="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128, regex="^[ -~]+$")
