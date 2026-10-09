import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from hi_resolve.settings import settings
import numpy as np
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
QDRANT_URL = settings.qdrant_url
_model: SentenceTransformer | None = None

RAG_DOCS_DIR = Path(__file__).resolve().parent / "rag_docs"


def load_questions(path: Path | str | None = None) -> list[str]:
    """Читает вопросы из rag_docs/questions.json."""
    questions_path = Path(path) if path else RAG_DOCS_DIR / "questions.json"
    with questions_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [item["question"] for item in data["test_questions"]]


def load_chunks(path: Path | str | None = None) -> list[dict]:
    """Читает чанки (контент/ответы) из rag_docs/new_.json."""
    chunks_path = Path(path) if path else RAG_DOCS_DIR / "new_.json"
    with chunks_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["chunks"]

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model

def embed_text(text: str) -> list[float]:
    """Строит embedding для одного текста (например doc['content'])."""
    model = get_embedding_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()

def cos_sim(a: list[float], b: list[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
points = []


if __name__ == "__main__":
    questions = load_questions('rag_docs/questions.json')
    chunks = load_chunks('rag_docs/new_.json')
    """
    chunks = load("new_.json")["chunks"]
    chunk_vecs = [embed(c["content"]) for c in chunks]
    for item in questions:
        q = item["question"]
        q_vec = embed(q)
        scored = []
        for chunk, vec in zip(chunks, chunk_vecs):
            score = cos_sim(q_vec, vec)[0][0].item()
            scored.append((score, chunk))
        top3 = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
        # print question + top3
    # optional: ask_ollama(build_rag_prompt(q, [c["content"] for _, c in top3]))
    """
    for question in questions:
        i = 0
        embedding = embed_text(question)
        points.append(
            PointStruct(
                id=i,
                vector=embedding,
                payload={"question": question},
            )
        )
        i += 1
        scored = []
        for i, chunk in enumerate(chunks):
            chunk_embedding = embed_text(chunk["content"])
            score = cos_sim(embedding, chunk_embedding)
            scored.append((score, chunk))
        top3 = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
        print(question) 
        print(top3)