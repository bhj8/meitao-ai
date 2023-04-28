from pydantic import BaseModel

class ChatMessageCreate(BaseModel):
    user_id: int
    role: str
    content: str

    class Config:
        orm_mode = True
