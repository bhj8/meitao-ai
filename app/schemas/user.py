from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., regex="^(([^<>()\[\]\\.,;:\s@\"]+(\.[^<>()\[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$")
    password: str = Field(..., min_length=6, max_length=128, regex="^[ -~]+$")
