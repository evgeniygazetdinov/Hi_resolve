from pydantic import BaseModel

from hi_resolve.db import Chat


class ChatCreate(BaseModel):
    title: str = "Новый чат"


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class ChatOut(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str


class ChatDetail(ChatOut):
    messages: list[MessageOut]


def iso(dt) -> str:
    return dt.isoformat() if dt else ""


def chat_out(chat: Chat) -> ChatOut:
    return ChatOut(
        id=chat.id,
        title=chat.title,
        created_at=iso(chat.created_at),
        updated_at=iso(chat.updated_at),
    )
