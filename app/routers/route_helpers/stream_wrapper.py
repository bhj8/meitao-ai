from contextlib import asynccontextmanager
import traceback
from app.db.crud import create_chat_message
from app.schemas.chat_message import ChatMessageCreate

from services.billing import calculate_cost
from services.user_operations import update_user_balance

class ResponseStreamWrapper:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id
        self.total_characters = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        # cost = calculate_cost(self.total_characters)
        # await update_user_balance(self.db, self.user_id, cost)
        pass

    async def response_stream(self, req_body, chat_reply_process, write_to_stream):
        try:
            async for content in chat_reply_process(  
                    user_message=req_body.user_message,
                    db=self.db,
                    user_id=self.user_id,                  
                    process=write_to_stream,
                    chat_session_id =req_body.chat_session_id,
                    model=req_body.model,
                    messages=req_body.messages,                    
                    temperature=req_body.temperature,
                    top_p=req_body.top_p,
                    n=req_body.n,
                    stop=req_body.stop,
                    max_tokens=req_body.max_tokens,
                    presence_penalty=req_body.presence_penalty,
                    frequency_penalty=req_body.frequency_penalty,
            ):
                self.total_characters += len(content)
                yield content
        except Exception as e:
            traceback.print_exc()
            yield "Error"