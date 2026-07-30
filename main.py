from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from auth import get_current_user, require_user, router as auth_router
from db import Chat, Message, User, get_db, init_db, utcnow

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/generate"
STATIC_DIR = Path(__file__).parent / "static"
SYSTEM_PROMPT = (
    "Ты полезный ассистент. Отвечай только на русском языке. "
    "Не используй английский, кроме имён собственных, кода и технических терминов."
)

app = FastAPI(title="Hi Resolve")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"),
    same_site="lax",
    https_only=False,
)
app.include_router(auth_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "qwen2.5:1.5b"
    num_predict: int = 256
    chat_id: int | None = None


class GenerateResponse(BaseModel):
    response: str
    model: str
    done: bool
    chat_id: int | None = None


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


def _iso(dt) -> str:
    return dt.isoformat() if dt else ""


def _chat_out(chat: Chat) -> ChatOut:
    return ChatOut(
        id=chat.id,
        title=chat.title,
        created_at=_iso(chat.created_at),
        updated_at=_iso(chat.updated_at),
    )


def _title_from_prompt(prompt: str) -> str:
    text = " ".join(prompt.split())
    if len(text) > 60:
        return text[:57] + "…"
    return text or "Новый чат"


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/chats", response_model=list[ChatOut])
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
    return [_chat_out(c) for c in chats]


@app.post("/api/chats", response_model=ChatOut)
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
    return _chat_out(chat)


@app.get("/api/chats/{chat_id}", response_model=ChatDetail)
def get_chat(
    chat_id: int,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return ChatDetail(
        **_chat_out(chat).model_dump(),
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=_iso(m.created_at),
            )
            for m in chat.messages
        ],
    )


@app.delete("/api/chats/{chat_id}")
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


@app.post("/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    request_user: Annotated[User | None, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    chat: Chat | None = None
    if body.chat_id is not None:
        if request_user is None:
            raise HTTPException(status_code=401, detail="Требуется авторизация")
        chat = (
            db.query(Chat)
            .filter(Chat.id == body.chat_id, Chat.user_id == request_user.id)
            .one_or_none()
        )
        if chat is None:
            raise HTTPException(status_code=404, detail="Чат не найден")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": body.model,
                    "system": SYSTEM_PROMPT,
                    "prompt": body.prompt,
                    "stream": False,
                    "options": {
                        "num_predict": body.num_predict,
                    },
                },
                timeout=120,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Ollama error: {e}") from e

    data = response.json()
    answer = data.get("response", "")

    saved_chat_id = None
    if chat is not None:
        now = utcnow()
        if not chat.messages:
            chat.title = _title_from_prompt(body.prompt)
        db.add(Message(chat_id=chat.id, role="user", content=body.prompt, created_at=now))
        db.add(Message(chat_id=chat.id, role="assistant", content=answer, created_at=utcnow()))
        chat.updated_at = utcnow()
        db.commit()
        saved_chat_id = chat.id

    return GenerateResponse(
        response=answer,
        model=data.get("model", body.model),
        done=data.get("done", True),
        chat_id=saved_chat_id,
    )
