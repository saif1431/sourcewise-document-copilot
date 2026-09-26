import asyncio
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import AuthApiError

from app.database.supabase import get_supabase_client

bearer_scheme = HTTPBearer(auto_error=False)

_unauthorized = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing or invalid authentication token",
    headers={"WWW-Authenticate": "Bearer"},
)


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    """Verify the Supabase access token and return the authenticated user.

    Calls Supabase Auth's user endpoint rather than verifying the JWT locally
    (see docs/architecture.md's Supabase and FastAPI Communication section).
    Run in a thread since the Supabase client is synchronous and this sits on
    the request path.
    """
    if credentials is None:
        raise _unauthorized

    try:
        response = await asyncio.to_thread(get_supabase_client().auth.get_user, credentials.credentials)
    except AuthApiError:
        raise _unauthorized from None

    if response is None or response.user.email is None:
        raise _unauthorized

    return CurrentUser(id=uuid.UUID(response.user.id), email=response.user.email)
