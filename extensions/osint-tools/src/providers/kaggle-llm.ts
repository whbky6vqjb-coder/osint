import { defineModelProvider } from "openclaw/plugin-sdk";

// Cette variable dynamique stockera l'URL courante du tunnel Cloudflare de Kaggle.
// Elle sera mise à jour en temps réel par le webhook.
let currentLLMUrl: string = process.env.LLM_API_BASE || "http://localhost:8080/v1";

export function updateKaggleLLMUrl(newUrl: string) {
  currentLLMUrl = newUrl;
  console.log(`[LLM Provider] URL LLM mise à jour : ${currentLLMUrl}`);
}

export function getKaggleLLMUrl(): string {
  return currentLLMUrl;
}

export const kaggleLLMProvider = defineModelProvider({
  id: "kaggle-qwen",
  name: "Qwen3.6-12B (Kaggle GPU)",
  
  async chat(messages, options) {
    if (!currentLLMUrl) {
      throw new Error("[LLM Provider] L'URL du LLM Kaggle n'est pas encore initialisée.");
    }
    
    // Nettoyer l'URL pour s'assurer qu'elle se termine par /v1/chat/completions ou correspond au standard OpenAI
    const endpoint = currentLLMUrl.endsWith("/v1") 
      ? `${currentLLMUrl}/chat/completions` 
      : `${currentLLMUrl}/v1/chat/completions`;

    console.log(`[LLM Provider] Appel de l'inférence sur : ${endpoint}`);

    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-no-key-required"
      },
      body: JSON.stringify({
        model: "KevinJK51/Qwen3.6-12B-IQ-Ultra-Heretic-Uncensored-Thinking-V2-Hightop-GGUF",
        messages: messages.map(m => ({
          role: m.role,
          content: m.content
        })),
        temperature: 0.3,
        max_tokens: 4096,
        stream: false
      })
    });
    
    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`[LLM Provider] Erreur HTTP du LLM (${res.status}): ${errText}`);
    }
    
    return await res.json();
  }
});
