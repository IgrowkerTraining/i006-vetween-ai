import httpx
import asyncio
from app.config.settings import settings
import time

async def ping_ia():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}", # Reemplaza con tu key
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": "Responder solo: OK"}],
        "max_tokens": 1
    }

    print(f"🚀 Enviando ping a Gemma 3...")
    
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload, timeout=10.0)


if __name__ == "__main__":
    asyncio.run(ping_ia())
import httpx
import asyncio
from app.config.settings import settings
import time

async def ping_ia():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}", # Reemplaza con tu key
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemma-3n-e2b-it:free",
        "messages": [{"role": "user", "content": "Responder solo: OK"}],
        "max_tokens": 5
    }

    print(f"🚀 Enviando ping a Gemma 3...")
    
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload, timeout=10.0)


if __name__ == "__main__":
    asyncio.run(ping_ia())