from pydantic import BaseModel

from hi_resolve.settings import settings


class GenerateRequest(BaseModel):
    prompt: str
    model: str = settings.ollama_model
    num_predict: int = settings.ollama_num_predict
    chat_id: int | None = None


class GenerateResponse(BaseModel):
    response: str
    model: str
    done: bool
    chat_id: int | None = None
    latency_ms: float | None = None


def title_from_prompt(prompt: str) -> str:
    text = " ".join(prompt.split())
    if len(text) > 60:
        return text[:57] + "…"
    return text or "Новый чат"
