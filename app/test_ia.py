import httpx
import asyncio
from config.settings import settings
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
    try:
        async with httpx.AsyncClient() as client:
            inicio = time.perf_counter()
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            
            latencia = time.perf_counter() - inicio

        if response.status_code == 200:
            res_data = response.json()
            texto = res_data['choices'][0]['message']['content']
            print(f"✅ ¡Éxito! La IA respondió: {texto}")
            print(f"Latencia: {latencia:.4f}s")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"🔥 Error de conexión: {str(e)}")

if __name__ == "__main__":
    asyncio.run(ping_ia())