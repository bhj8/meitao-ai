import json
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app.db.crud import  create_chat_message, create_chat_session, get_chat_messages_by_chat_session_id, get_chat_sessions_by_user_id
from app.routers.chatgpt import chat_process,chat_process_stream
from app.schemas.chat_message import ChatMessageCreate
from app.schemas.chatgpt import chat_FastRequestProps, chat_stream_RequestProps
from app.security.auth import verify_token, verify_token_and_balance
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
    token_data: dict = Depends(verify_token),
    rate_limited: None = Depends(rate_limiter),
):
    message = req_body.message
    if not message:
        return JSONResponse(status_code=400, content={"message": "Message cannot be empty."})

    try:
        response = await get_moderation(input=message)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

    return response.results[0].flagged

@router.post("/chatgpt_fast/chat-stream-text")
async def fast_chat_process_stream(
    req_body: chat_FastRequestProps,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_token_and_balance),
    rate_limited: None = Depends(rate_limiter),
):

    user_id = int(token_data["sub"])

    try:
        user_message = req_body.messages
        messages = await construct_messages_from_chat_history(db, user_id, req_body.chat_session_id, req_body.system_message,input_message=req_body.messages)
        full_request = chat_RequestProps(
            user_message= user_message,
            chat_session_id = req_body.chat_session_id,
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.7,
            top_p=1,
            n=1,
            stop=None,
            max_tokens=1000,
            presence_penalty=0,
            frequency_penalty=0,
            logit_bias=None,
        )
    except Exception as e:
        traceback.print_exc()
        # return JSONResponse(status_code=500, content={"message": str(e)})

    return await chat_process_stream(full_request, db, token_data, rate_limited)

    
    
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
        messages = await construct_messages_from_chat_history(db, user_id, req_body.chat_session_id, req_body.system_message, req_body.message)
        full_request = chat_RequestProps(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.7,
            top_p=1,
            n=1,
            stop=None,
            max_tokens=1000,
            presence_penalty=0,
            frequency_penalty=0,
            logit_bias=None,
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"message": str(e)})
    return await chat_process(full_request, db, token_data, rate_limited)


async def construct_messages_from_chat_history(db: AsyncSession, user_id: int, chat_session_id: int, system_message: str, input_message: str) -> List[Dict[str, str]]:
    chat_sessions = await get_chat_sessions_by_user_id(db, user_id)
    if not chat_sessions or chat_session_id not in [chat_session.id for chat_session in chat_sessions]:
        new_chat_session = await create_chat_session(db, user_id, chat_session_id)

    
    chat_messages = await get_chat_messages_by_chat_session_id(db, chat_session_id)
    
    messages = [
        {"role": "system", "content": system_message},
    ]
    if chat_messages:
        # Check if the user owns the chat session
        # if chat_messages[0].user_id != user_id:
        #     raise HTTPException(status_code=403, detail="You do not have permission to access this chat session")

        total_length = len(system_message)

        for message in chat_messages:
            message_length = len(message.content)
            
            # Break the loop if adding the next message would exceed the 250 character limit
            if total_length + message_length > 1500:
                break

            messages.insert(1, {"role": message.role, "content": message.content})
            total_length += message_length

    messages.append({"role": "user", "content": input_message})

    return messages




