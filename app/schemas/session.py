from pydantic import BaseModel
class SessionResponse(BaseModel):
    auth: bool
    model: str