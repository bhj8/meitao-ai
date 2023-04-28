from discord import HTTPException
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app.db.crud import get_chat_message_by_user_id_and_message_id, get_chat_messages_by_chat_session_id, get_chat_messages_by_user_id, get_chat_sessions_by_user_id
from app.routers.chatgpt import chat_process
from app.schemas.chatgpt import chat_FastRequestProps, chat_stream_RequestProps
from app.security.auth import verify_token_and_balance
from services.billing import calculate_cost
from services.user_operations import update_user_balance
from app.security.rate_limiter import rate_limiter
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers.route_helpers.stream_wrapper import ResponseStreamWrapper
import traceback

from services.api_openai import get_chat_response_stream, get_chat_response, get_moderation
from app.schemas.chatgpt import Moderation_RequestProps, chat_RequestProps

router = APIRouter(tags=["ChatGPT_Fast"])


@router.post("/chatgpt_fast/moderation")
async def moderation_endpoint(
    req_body: Moderation_RequestProps,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_token_and_balance),
    rate_limited: None = Depends(rate_limiter),
):
    message = req_body.message
    if not message:
        return JSONResponse(status_code=400, content={"message": "Message cannot be empty."})

    try:
        response = await get_moderation(message)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

    return response.results[0].flagged


from typing import List, Dict

@router.post("/chatgpt_fast/chat")
async def chat_process_fast(
    req_body: chat_FastRequestProps,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_token_and_balance),
    rate_limited: None = Depends(rate_limiter),
):
    
    user_id = int(token_data["sub"])
    try:
        messages = await construct_messages_from_chat_history(db, user_id, req_body.chat_message_id, req_body.system_message, req_body.messages)
        full_request = chat_RequestProps(
            messages=messages,
            model="text-davinci-002",
            temperature=0.7,
            top_p=1,
            n=1,
            stop=None,
            max_tokens=150,
            presence_penalty=0,
            frequency_penalty=0,
            logit_bias=None,
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": str(e)})
    return await chat_process(full_request, db, token_data, rate_limited)

async def construct_messages_from_chat_history(db: AsyncSession, user_id: int, chat_session_id: int, system_message: str, input_message: str) -> List[Dict[str, str]]:
    chat_session_ids = await get_chat_sessions_by_user_id(db, user_id)
    if not chat_session_ids or chat_session_id not in chat_session_ids:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    chat_messages = await get_chat_messages_by_chat_session_id(db, chat_session_id)

    if not chat_messages:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Check if the user owns the chat session
    if chat_messages[0].user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this chat session")

    messages = [
        {"role": "system", "content": system_message},
    ]

    total_length = len(system_message)

    for message in chat_messages:
        message_length = len(message.content)
        
        # Break the loop if adding the next message would exceed the 250 character limit
        if total_length + message_length > 250:
            break

        messages.insert(1, {"role": message.role, "content": message.content})
        total_length += message_length

    messages.append({"role": "user", "content": input_message})

    return messages