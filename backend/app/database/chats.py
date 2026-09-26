import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database.models import ChatMessage, ChatThread, User
from app.database.session import session_maker


def get_or_create_user(user_id: uuid.UUID, email: str) -> User:
    """Provision the app-side `users` row on first login.

    Only called from thread creation: chat_messages/message_citations key off
    thread_id, never user_id, so this is the one place a users row must exist
    before a foreign-key-dependent write.
    """
    with session_maker() as session:
        stmt = (
            insert(User)
            .values(id=user_id, email=email)
            .on_conflict_do_update(index_elements=[User.id], set_={"email": email})
            .returning(User)
        )
        result = session.execute(stmt)
        session.commit()
        return result.scalar_one()


def list_threads(user_id: uuid.UUID) -> list[ChatThread]:
    with session_maker() as session:
        stmt = select(ChatThread).where(ChatThread.user_id == user_id).order_by(ChatThread.updated_at.desc())
        return list(session.execute(stmt).scalars())


def create_thread(user_id: uuid.UUID, title: str | None = None) -> ChatThread:
    with session_maker() as session:
        thread = ChatThread(user_id=user_id, title=title)
        session.add(thread)
        session.commit()
        session.refresh(thread)
        return thread


def get_thread(thread_id: uuid.UUID) -> ChatThread | None:
    with session_maker() as session:
        return session.get(ChatThread, thread_id)


def list_messages(thread_id: uuid.UUID) -> list[ChatMessage]:
    with session_maker() as session:
        stmt = select(ChatMessage).where(ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at.asc())
        return list(session.execute(stmt).scalars())


def add_message(thread_id: uuid.UUID, role: str, content: dict) -> ChatMessage:
    with session_maker() as session:
        message = ChatMessage(thread_id=thread_id, role=role, content=content)
        session.add(message)
        # ChatThread.updated_at's onupdate=func.now() only fires on an UPDATE to
        # that row, which adding a message never triggers on its own — bump it
        # explicitly so the thread list can sort by recency.
        thread = session.get(ChatThread, thread_id)
        thread.updated_at = datetime.now(UTC)
        session.commit()
        session.refresh(message)
        return message
