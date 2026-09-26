import asyncio
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat.messages import ChatStreamRequest, UIMessage, content_to_ui_message, latest_user_text
from app.chat.orchestrator import run_turn
from app.database import chats
from app.database.models import ChatThread

router = APIRouter(prefix="/chat", tags=["chat"])

Auth = Annotated[CurrentUser, Depends(get_current_user)]


class ThreadOut(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateThreadIn(BaseModel):
    title: str | None = None


async def _get_owned_thread(thread_id: uuid.UUID, current_user: CurrentUser) -> ChatThread:
    thread = await asyncio.to_thread(chats.get_thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    if thread.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your thread")
    return thread


@router.get("/threads", response_model=list[ThreadOut])
async def get_threads(current_user: Auth) -> list[ChatThread]:
    return await asyncio.to_thread(chats.list_threads, current_user.id)


@router.post("/threads", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
async def post_thread(body: CreateThreadIn, current_user: Auth) -> ChatThread:
    await asyncio.to_thread(chats.get_or_create_user, current_user.id, current_user.email)
    return await asyncio.to_thread(chats.create_thread, current_user.id, body.title)


@router.get("/threads/{thread_id}/messages", response_model=list[UIMessage])
async def get_thread_messages(thread_id: uuid.UUID, current_user: Auth) -> list[UIMessage]:
    thread = await _get_owned_thread(thread_id, current_user)
    messages = await asyncio.to_thread(chats.list_messages, thread.id)
    return [content_to_ui_message(message.id, message.content) for message in messages]


@router.post("/stream")
async def post_stream(body: ChatStreamRequest, current_user: Auth) -> StreamingResponse:
    thread = await _get_owned_thread(body.threadId, current_user)
    user_text = latest_user_text(body.messages)
    return StreamingResponse(
        run_turn(thread.id, user_text),
        media_type="text/event-stream",
        headers={"x-vercel-ai-ui-message-stream": "v1"},
    )
