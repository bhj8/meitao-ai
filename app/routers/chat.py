from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse,JSONResponse
from app.models.chat import RequestProps
from app.security.auth import verify_token_and_balance
from services.billing import calculate_cost
from services.user_operations import update_user_balance
from app.security.rate_limiter import rate_limiter
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers.route_helpers.stream_wrapper import ResponseStreamWrapper
import traceback

from services.api_openai import get_chat_response_stream,get_chat_response

router = APIRouter()

async def chat_reply_process(message: str, last_context: dict, process, system_message: str, temperature: float, top_p: float):
    response_generator = await get_chat_response_stream()  # Add the missing parameters

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

@router.post("/chat-process-stream")
async def chat_process(request: Request, req_body: RequestProps, db: AsyncSession = Depends(get_db), token_data: dict = Depends(verify_token_and_balance),rate_limited: None = Depends(rate_limiter)):
    user_id = int(token_data["sub"])

    async with ResponseStreamWrapper(db, user_id) as stream_wrapper:
        return StreamingResponse(stream_wrapper.response_stream(req_body, chat_reply_process, write_to_stream), media_type="application/octet-stream")

@router.post("/chat-process")
async def chat_process(request: Request, req_body: RequestProps, db: AsyncSession = Depends(get_db), token_data: dict = Depends(verify_token_and_balance),rate_limited: None = Depends(rate_limiter)):
    total_characters = 0
    try:
        response = await get_chat_response(
            # message=req_body.prompt,
            # last_context=req_body.options,
            # system_message=req_body.systemMessage,
            # temperature=req_body.temperature,
            # top_p=req_body.top_p,
        )
        content = response.choices[0].message.content.strip()
        total_characters = response.usage.total_tokens
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={"error": "Error"}, status_code=500)

    # Calculate the cost based on the number of characters in the response
    cost = calculate_cost(total_characters)

    # Deduct the cost from the user's balance
    await update_user_balance(db,int(token_data["sub"]), cost)

    return JSONResponse(content={"response": content}, status_code=200)
