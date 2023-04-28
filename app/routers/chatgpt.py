from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app.schemas.chatgpt import chat_stream_RequestProps
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

router = APIRouter(tags=["ChatGPT"])


@router.post("/chatgpt/moderation")
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

    return response


@router.post("/chatgpt/chat")
async def chat_process(
    req_body: chat_RequestProps,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_token_and_balance),
    rate_limited: None = Depends(rate_limiter),
):
    total_characters = 0
    content = ""
    status_code = 200

    try:
        response = await get_chat_response(
            model=req_body.model,
            messages=req_body.messages,
            temperature=req_body.temperature,
            top_p=req_body.top_p,
            n=req_body.n,
            stop=req_body.stop,
            max_tokens=req_body.max_tokens,
            presence_penalty=req_body.presence_penalty,
            frequency_penalty=req_body.frequency_penalty,
            logit_bias=req_body.logit_bias,
        )
        total_characters = response.usage.total_tokens

        # Calculate the cost based on the number of characters in the response
        cost = calculate_cost(total_characters)

        # Deduct the cost from the user's balance
        await update_user_balance(db, int(token_data["sub"]), cost)

    except Exception as e:
        traceback.print_exc()
        response = JSONResponse(status_code=400, content={"message": e})
    return response


@router.post("/chatgpt/chat-stream-text")
async def chat_process( req_body: chat_stream_RequestProps, db: AsyncSession = Depends(get_db), token_data: dict = Depends(verify_token_and_balance), rate_limited: None = Depends(rate_limiter)):
    user_id = int(token_data["sub"])

    async with ResponseStreamWrapper(db, user_id) as stream_wrapper:
        return StreamingResponse(stream_wrapper.response_stream(req_body, chat_reply_process, write_to_stream), media_type="application/octet-stream")


async def chat_reply_process(process, **kwargs):
    response_generator = await get_chat_response_stream(**kwargs)

    response_text = ""
    async for chunk in response_generator:  # Iterate through chunks in the response
        content = chunk["choices"][0].get("delta", {}).get("content")
        if content is not None:
            # Pass the content to the process function
            response_text = await process(content)
            yield response_text


async def write_to_stream(content: str):
    response_text = f"{content}"
    return response_text