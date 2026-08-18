from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hi_resolve.settings import settings


def chunk_text(
    text: str,
    chunk_size: int = settings.chunk_size,
    overlap: int = settings.chunk_overlap,
) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def main() -> None:
    text = settings.rag_file.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        print(f"\n===== CHUNK {i} =====")
        print(chunk)


if __name__ == "__main__":
    main()
