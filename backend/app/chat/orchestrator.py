import asyncio
import uuid
from collections.abc import AsyncIterator

from app.chat.messages import to_stored_content
from app.chat.streaming import stream_stub_reply
from app.database.chats import add_message

_STUB_REPLY = (
    "This is a stubbed response from Document Copilot. Real retrieval and grounded, "
    "cited answers come online in a later phase — for now this confirms the chat, "
    "streaming, and persistence plumbing all work end to end."
)


async def run_turn(thread_id: uuid.UUID, user_text: str) -> AsyncIterator[bytes]:
    """Coordinate one chat turn: persist the user message, stream a reply, persist it.

    Stubbed for Phase 3 — Phase 6 replaces the reply generation here with the
    real PydanticAI agent + retrieval + grounding, without touching the route.
    """
    await asyncio.to_thread(add_message, thread_id, "user", to_stored_content("user", user_text))

    async for chunk in stream_stub_reply(_STUB_REPLY):
        yield chunk

    await asyncio.to_thread(add_message, thread_id, "assistant", to_stored_content("assistant", _STUB_REPLY))
