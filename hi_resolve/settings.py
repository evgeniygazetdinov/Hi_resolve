from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    oauth_redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "")

    ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT", "120"))
    ollama_num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "256"))
    system_prompt = (
        "Ты полезный ассистент. Отвечай только на русском языке. "
        "Не используй английский, кроме имён собственных, кода и технических терминов."
    )
    chunk_size = int(os.getenv("CHUNK_SIZE", "100"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))
    rag_path = Path(os.getenv("RAG_PATH", "data/personal_knoledge.txt"))
    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    session_same_site = os.getenv("SESSION_SAME_SITE", "lax")
    session_https_only = os.getenv("SESSION_HTTPS_ONLY", "").lower() in {"1", "true", "yes"}

    static_dir = BASE_DIR / "static"
    data_dir = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def rag_file(self) -> Path:
        return self.rag_path if self.rag_path.is_absolute() else BASE_DIR / self.rag_path

    @property
    def google_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


settings = Settings()
