import asyncio
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"


async def main():
    prompt = "Объясни что такое RAG простыми словами ответь на русском"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": "tinyllama",   # или mistral / deepseek
                "prompt": prompt,
                "stream": False,
                "options": {
    "num_predict": 100
},
            },
            timeout=60
        )

        data = response.json()
        print(data)


if __name__ == "__main__":
    asyncio.run(main())