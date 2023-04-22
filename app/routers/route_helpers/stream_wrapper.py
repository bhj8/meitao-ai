from contextlib import asynccontextmanager
import traceback

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
        cost = calculate_cost(self.total_characters)
        await update_user_balance(self.db, self.user_id, cost)

    async def response_stream(self, req_body, chat_reply_process, write_to_stream):
        try:
            async for content in chat_reply_process(
                    message=req_body.prompt,
                    last_context=req_body.options,
                    process=write_to_stream,
                    system_message=req_body.systemMessage,
                    temperature=req_body.temperature,
                    top_p=req_body.top_p,
            ):
                self.total_characters += len(content)
                yield content
        except Exception as e:
            traceback.print_exc()
            yield "Error"
