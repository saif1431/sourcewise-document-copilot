from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.auth.dependencies import CurrentUser, get_current_user
from app.config import settings

app = FastAPI(title="Document Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/me")
async def me(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    return current_user
