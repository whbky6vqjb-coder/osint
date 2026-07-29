import httpx
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger("LLMClient")

class NemotronLLMClient:
    """Client pour le modèle auto-hébergé Qwen3.6-12B-IQ-Ultra-Heretic-Uncensored-Thinking-V2-Hightop-GGUF
    Hébergé localement via llama-server avec quantification Importance Matrix (IQ), --mmap, --mlock,
    compression KV Cache (q4_0), --flash-attn, batching (-b 512 -ub 256) et -t 2.
    """

    def __init__(self):
        self.api_base = settings.LLM_API_BASE
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.provider = settings.LLM_PROVIDER

    async def generate_reasoning(self, prompt: str, system_prompt: str = "") -> str:
        """Génère un raisonnement dynamique piloté à 100% par le LLM auto-hébergé Qwen3.6-12B IQ Ultra Heretic"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4096,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                res = await client.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                else:
                    logger.error(f"Erreur API LLM ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Erreur de connexion au serveur LLM Qwen3.6-12B (llama-server): {e}")
            
        raise RuntimeError(f"Le serveur LLM auto-hébergé Qwen3.6-12B-IQ-Ultra-Heretic ({self.api_base}) est indisponible. Assurez-vous que llama-server tourne avec les optimisations IQ, --mlock, --cache-type-k q4_0.")
