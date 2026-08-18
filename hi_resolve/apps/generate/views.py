from __future__ import annotations

import logging
import time
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from hi_resolve.apps.auth.views import get_current_user
from hi_resolve.apps.generate.schemas import GenerateRequest, GenerateResponse, title_from_prompt
from hi_resolve.db import Chat, Message, User, get_db, utcnow
from hi_resolve.settings import settings

logger = logging.getLogger("hi_resolve")

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
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

    ollama_start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.ollama_url,
                json={
                    "model": body.model,
                    "system": settings.system_prompt,
                    "prompt": body.prompt,
                    "stream": False,
                    "options": {
                        "num_predict": body.num_predict,
                    },
                },
                timeout=settings.ollama_timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            ollama_ms = (time.perf_counter() - ollama_start) * 1000
            logger.error(
                "ollama error model=%s chat_id=%s prompt_len=%d latency=%.1fms: %s",
                body.model,
                body.chat_id,
                len(body.prompt),
                ollama_ms,
                e,
            )
            raise HTTPException(status_code=502, detail=f"Ollama error: {e}") from e

    ollama_ms = (time.perf_counter() - ollama_start) * 1000
    data = response.json()
    answer = data.get("response", "")
    logger.info(
        "ollama ok model=%s chat_id=%s prompt_len=%d answer_len=%d latency=%.1fms",
        body.model,
        body.chat_id,
        len(body.prompt),
        len(answer),
        ollama_ms,
    )

    saved_chat_id = None
    if chat is not None:
        now = utcnow()
        if not chat.messages:
            chat.title = title_from_prompt(body.prompt)
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
        latency_ms=round(ollama_ms, 1),
    )
