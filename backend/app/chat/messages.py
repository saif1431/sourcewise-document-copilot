import uuid
from typing import Literal

from pydantic import BaseModel


class UIMessagePart(BaseModel):
    type: Literal["text"]
    text: str


class UIMessage(BaseModel):
    id: str | None = None
    role: Literal["user", "assistant", "system"]
    parts: list[UIMessagePart]


class ChatStreamRequest(BaseModel):
    threadId: uuid.UUID
    messages: list[UIMessage]


def latest_user_text(messages: list[UIMessage]) -> str:
    """Text of the newest message in the request.

    The backend treats its own DB as the source of truth for history and only
    acts on the last message here — works whether the client resends full
    history or just the new turn.
    """
    if not messages:
        return ""
    return "".join(part.text for part in messages[-1].parts if part.type == "text")


def to_stored_content(role: Literal["user", "assistant"], text: str) -> dict:
    """Shape persisted into chat_messages.content (JSONB)."""
    return {"role": role, "parts": [{"type": "text", "text": text}]}


def content_to_ui_message(message_id: uuid.UUID, content: dict) -> UIMessage:
    """Shape returned to the client when loading thread history."""
    return UIMessage(id=str(message_id), role=content["role"], parts=content["parts"])
