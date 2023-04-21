from pydantic import BaseModel

class RequestProps(BaseModel):
    prompt: str
    options: dict = None
    systemMessage: str = None
    temperature: float = None
    top_p: float = None
