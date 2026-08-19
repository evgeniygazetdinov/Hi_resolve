from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

texts = [
    "FastAPI is a Python web framework",
    "FastAPI is used to build APIs",
    "I like pizza",
]

embeddings = model.encode(texts)

print(embeddings.shape)

for text, embedding in zip(texts, embeddings):
    print("\nTEXT:")
    print(text)

    print("VECTOR:")
    print(embedding[:10])