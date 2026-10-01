import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

RAG_DOCS_DIR = Path(__file__).resolve().parent / "rag_docs"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QUESTIONS = "Where place in saint petersburg is best for a walk?"

_model: SentenceTransformer | None = None


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


if __name__ == "__main__":
    docs = load_rag_docs()
    print(f"Loaded {len(docs)} documents")
    embedded_question = embed_text(QUESTIONS)
    best_score = 0
    best_doc = None
    for doc in docs:
        parsed = parse_rag_doc(doc)
        embedding = embed_text(parsed["content"])
        scores = cos_sim(
            embedded_question,
            embedding
        )

        if scores[0][0] > best_score:
            best_score = scores[0][0]
            best_doc = parsed
    print(f"Best score: {best_score} document: {best_doc['id']}")
    print(f"Best document: {best_doc}")