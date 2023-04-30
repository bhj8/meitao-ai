from typing import List, Union, Optional
from pydantic import BaseModel


class Moderation_RequestProps(BaseModel):
    message: str
    
    
    
class chat_RequestProps(BaseModel):
    user_message:str
    chat_session_id: int
    model: str= "gpt-3.5-turbo"
    messages: List[dict]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    
    
class chat_stream_RequestProps(BaseModel):
    user_message:str
    chat_session_id: int
    model: str = "gpt-3.5-turbo"
    messages: List[dict]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    
    

class chat_FastRequestProps(BaseModel):
    system_message: str
    messages: str
    chat_session_id: int
