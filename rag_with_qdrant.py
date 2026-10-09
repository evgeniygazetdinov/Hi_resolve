import json
from pathlib import Path

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from hi_resolve.settings import settings

RAG_DOCS_DIR = Path(__file__).resolve().parent / "rag_docs"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QUESTIONS = "Where place in saint petersburg is best for a walk?"

_model: SentenceTransformer | None = None

client = QdrantClient(url=settings.qdrant_url)

client.recreate_collection(
    collection_name="test_rag",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE,
    ),
)

def chunk_text(text: str, chunk_size: int = settings.chunk_size, overlap: int = settings.chunk_overlap) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def load_rag_docs(docs_dir: Path | str = RAG_DOCS_DIR) -> list[dict]:
    """Читает все JSON-файлы из rag_docs по одному и возвращает список словарей."""
    docs_path = Path(docs_dir)
    documents: list[dict] = []

    for path in sorted(docs_path.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            documents.append(json.load(f))

    return documents


def parse_rag_doc(doc: dict) -> dict:
    """Парсит JSON-документ и возвращает словарь с данными."""
    return {
        "id": doc.get("id"),
        "type": doc.get("type"),
        "metadata": doc.get("metadata"),
        "content": doc.get("content"),
    }


def embed_text(text: str) -> list[float]:
    """Строит embedding для одного текста (например doc['content'])."""
    model = get_embedding_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()


def build_rag_prompt(question: str, contexts: list[str]) -> str:
    context_block = "\n\n".join(f"- {context}" for context in contexts)
    return (
        "Используй только контекст ниже для ответа. "
        "Если в контексте нет ответа, так и скажи.\n\n"
        f"Контекст:\n{context_block}\n\n"
        f"Вопрос: {question}"
    )


def ask_ollama(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    num_predict: int | None = None,
) -> str:
    """Отправляет prompt в Ollama и возвращает текст ответа."""
    response = httpx.post(
        settings.ollama_url,
        json={
            "model": model or settings.ollama_model,
            "system": system or settings.system_prompt,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": num_predict or settings.ollama_num_predict,
            },
        },
        timeout=settings.ollama_timeout,
    )
    response.raise_for_status()
    return response.json().get("response", "")


if __name__ == "__main__":
    docs = load_rag_docs()
    print(f"Loaded {len(docs)} documents")

    points = []
    for i, doc in enumerate(docs):
        parsed = parse_rag_doc(doc)
        embedding = embed_text(parsed["content"])  # уже list[float]
        chunks = chunk_text(parsed["content"])
        for chunk in chunks:
            embedding = embed_text(chunk)
            points.append(
                PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "id": parsed["id"],
                        "type": parsed["type"],
                        "text": chunk,
                        "metadata": parsed["metadata"],
                    },
                )
            )

    client.upsert(
        collection_name="test_rag",
        points=points,
    )

    hits = client.query_points(
        collection_name="test_rag",
        query=embed_text(QUESTIONS),
        limit=1,
    ).points
    best = hits[0]
    print(f"Best score: {best.score} document: {best.payload['id']}")
    print(f"Best document: {best.payload}")

    rag_prompt = build_rag_prompt(QUESTIONS, [best.payload["text"]])
    answer = ask_ollama(rag_prompt)
    print(f"\nOllama answer:\n{answer}")
