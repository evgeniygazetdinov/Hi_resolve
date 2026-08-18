from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from hi_resolve.apps.auth.views import require_user
from hi_resolve.apps.chats.schemas import ChatCreate, ChatDetail, ChatOut, MessageOut, chat_out, iso
from hi_resolve.db import Chat, User, get_db, utcnow

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def list_chats(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user.id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return [chat_out(c) for c in chats]


@router.post("", response_model=ChatOut)
def create_chat(
    body: ChatCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    now = utcnow()
    chat = Chat(
        user_id=user.id,
        title=body.title.strip() or "Новый чат",
        created_at=now,
        updated_at=now,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat_out(chat)


@router.get("/{chat_id}", response_model=ChatDetail)
def get_chat(
    chat_id: int,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return ChatDetail(
        **chat_out(chat).model_dump(),
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=iso(m.created_at),
            )
            for m in chat.messages
        ],
    )


@router.delete("/{chat_id}")
def delete_chat(
    chat_id: int,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    db.delete(chat)
    db.commit()
    return {"ok": True}
