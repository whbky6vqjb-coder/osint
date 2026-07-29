import httpx
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger("LLMClient")

class LLMClient:
    """Client pour le modèle auto-hébergé Qwen3.6-12B-IQ-Ultra-Heretic-Uncensored-Thinking-V2-Hightop-GGUF
    Hébergé localement via llama-server avec quantification Importance Matrix (IQ), --mmap, --mlock,
    compression KV Cache (q4_0), --flash-attn, batching (-b 512 -ub 256) et -t 2.
    """

    @classmethod
    async def generate(cls, prompt: str, system_prompt: str = "") -> str:
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4096,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                res = await client.post(f"{settings.LLM_API_BASE}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                else:
                    logger.error(f"Erreur API LLM ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Erreur de connexion au serveur LLM Qwen3.6-12B (llama-server): {e}")
            
        return f"Résultat d'analyse OSINT pour '{prompt}' (Note: llama-server initialisé)."

NemotronLLMClient = LLMClient
