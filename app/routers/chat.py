from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse,JSONResponse
from app.models.chat import RequestProps
from app.security.auth import verify_token_and_balance
from services.billing import calculate_cost
from services.user_operations import update_user_balance
from app.security.rate_limiter import rate_limiter

import traceback

from services.api_openai import get_chat_response_stream,get_chat_response

router = APIRouter()

async def chat_reply_process(message: str, last_context: dict, process, system_message: str, temperature: float, top_p: float):
    response_generator = await get_chat_response_stream(message=message, last_context=last_context, system_message=system_message, temperature=temperature, top_p=top_p)  # Add the missing parameters

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
async def chat_process(request: Request, req_body: RequestProps, token_data: dict = Depends(verify_token_and_balance),rate_limited: None = Depends(rate_limiter)):
    total_characters = 0
    async def response_stream():
        try:
            async for content in chat_reply_process(
                    message=req_body.prompt,
                    last_context=req_body.options,
                    process=write_to_stream,
                    system_message=req_body.systemMessage,
                    temperature=req_body.temperature,
                    top_p=req_body.top_p,
            ):
                total_characters += len(content)
                yield content
        except Exception as e:
            traceback.print_exc()
            yield "Error"
    # Calculate the cost based on the number of characters in the response
    cost = calculate_cost(total_characters)

    # Deduct the cost from the user's balance
    await update_user_balance(token_data["sub"], cost)

    return StreamingResponse(response_stream(), media_type="application/octet-stream")

@router.post("/chat-process")
async def chat_process(request: Request, req_body: RequestProps, token_data: dict = Depends(verify_token_and_balance),rate_limited: None = Depends(rate_limiter)):
    total_characters = 0
    content = ""
    status_code = 200

    try:
        response = await get_chat_response(
            message=req_body.prompt,
            last_context=req_body.options,
            system_message=req_body.systemMessage,
            temperature=req_body.temperature,
            top_p=req_body.top_p,
        )
        total_characters = response.usage.total_tokens

        # Calculate the cost based on the number of characters in the response
        cost = calculate_cost(total_characters)

        # Deduct the cost from the user's balance
        await update_user_balance(token_data["sub"], cost)

    except Exception as e:
        traceback.print_exc()
        response = JSONResponse(status_code=500, content={"message": "ai-server error."})
    return response
