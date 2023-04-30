from fastapi import APIRouter, Depends, HTTPException
from app.db.crud import (
    create_chat_session, delete_chat_session, get_chat_session_by_id,
    get_chat_session_by_user_id_and_chat_session_id
)
from app.db.database import get_db
from app.security.auth import verify_token_and_membership, verify_token
from app.security.rate_limiter import rate_limiter
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Chat_Sessions"])

from pydantic import BaseModel

class ChatSessionCreateProps(BaseModel):
    chat_session_id: int

@router.post("/chat_sessions/create")
async def create_chat_session_endpoint(
    req_body: ChatSessionCreateProps,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_token),
    rate_limited: None = Depends(rate_limiter),
):
    user_id = int(token_data["sub"])
    chat_session = await get_chat_session_by_id(db, req_body.chat_session_id)

    if chat_session is not None:
        raise HTTPException(status_code=400, detail="Chat session ID already exists")

    new_chat_session = await create_chat_session(db, user_id, req_body.chat_session_id)
    return {"chat_session_id": new_chat_session.id}

@router.delete("/chat_sessions/{chat_session_id}/delete")
async def delete_chat_session_endpoint(
    req_body: ChatSessionCreateProps,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(verify_token),
    rate_limited: None = Depends(rate_limiter),
):
    user_id = int(token_data["sub"])
    chat_session = await get_chat_session_by_user_id_and_chat_session_id(db, user_id, req_body.chat_session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    await delete_chat_session(db, user_id, req_body.chat_session_id)
    return {"detail": "Chat session successfully deleted"}
