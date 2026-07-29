import httpx
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger("LLMClient")

class NemotronLLMClient:
    """Client pour le modèle Nemotron-3-Nano (30B MoE Mamba-Hybrid, 1M Context Window)
    Pilotage intégral par l'IA des étapes d'enquête, CoT et révision critique Dual-Agent.
    """

    def __init__(self):
        self.api_base = settings.LLM_API_BASE
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.provider = settings.LLM_PROVIDER

    async def generate_reasoning(self, prompt: str, system_prompt: str = "") -> str:
        """Génère un raisonnement dynamique piloté à 100% par le LLM Nemotron-3-Nano (1M Context)"""
        
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
            "temperature": 0.2,
            "max_tokens": 4096,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                else:
                    logger.error(f"Erreur API LLM ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Erreur de connexion au serveur LLM Nemotron: {e}")
            
        raise RuntimeError(f"Le serveur LLM Nemotron-3-Nano ({self.api_base}) est indisponible. L'IA doit contrôler l'ensemble de l'enquête.")
