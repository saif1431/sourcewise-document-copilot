import asyncio
import json
import uuid
from collections.abc import AsyncIterator

# AI SDK v5 UI Message Stream protocol: SSE lines of `data: <json>\n\n`,
# terminated by `data: [DONE]\n\n`. Client-side this is what DefaultChatTransport
# expects behind the `x-vercel-ai-ui-message-stream: v1` response header.
_CHUNK_DELAY_SECONDS = 0.03


def _sse(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode()


async def stream_stub_reply(text: str) -> AsyncIterator[bytes]:
    """Stream `text` as AI SDK v5 UI message chunks, word by word.

    Phase 3 has no real LLM yet — this validates the streaming plumbing
    end-to-end (route, transport, persistence) before Phase 6 swaps in the
    real agent behind app/chat/orchestrator.py.
    """
    part_id = str(uuid.uuid4())
    yield _sse({"type": "start"})
    yield _sse({"type": "text-start", "id": part_id})

    words = text.split(" ")
    for index, word in enumerate(words):
        delta = word if index == len(words) - 1 else f"{word} "
        yield _sse({"type": "text-delta", "id": part_id, "delta": delta})
        await asyncio.sleep(_CHUNK_DELAY_SECONDS)

    yield _sse({"type": "text-end", "id": part_id})
    yield _sse({"type": "finish"})
    yield b"data: [DONE]\n\n"
