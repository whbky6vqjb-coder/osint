import os
import re
import time
import json
import urllib.request
import urllib.parse

def find_cloudflare_url(log_file="/tmp/cloudflared.log", max_wait=30):
    """
    Recherche l'URL du tunnel Cloudflare dans le fichier de log.
    """
    url_pattern = re.compile(r"https://[-a-zA-Z0-9]+\.trycloudflare\.com")
    start = time.time()
    
    while time.time() - start < max_wait:
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = url_pattern.findall(content)
                    if matches:
                        return matches[-1] # Prendre la dernière URL générée
            except Exception as e:
                print(f"Erreur de lecture du log Cloudflare: {e}")
        time.sleep(2)
    return None

def publish_to_github(url, repo="whbky6vqjb-coder/osint", token=None):
    """
    Met à jour le fichier storage/llm_url.txt sur le dépôt GitHub via l'API.
    """
    if not token:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_PAT")
    
    if not token:
        print("⚠️ Aucun token GitHub (GITHUB_TOKEN/GH_PAT) trouvé. Ignoré.")
        return False

    api_url = f"https://api.github.com/repos/{repo}/contents/storage/llm_url.txt"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Kaggle-Publisher/1.0"
    }

    # 1. Obtenir le SHA actuel du fichier s'il existe
    sha = None
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                sha = data.get("sha")
    except Exception:
        pass

    # 2. Encoder le contenu en Base64
    import base64
    content_b64 = base64.b64encode(f"{url}/v1\n".encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"chore: update dynamic Cloudflare LLM URL [{url}]",
        "content": content_b64,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(api_url, data=data_bytes, headers=headers, method="PUT")
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201):
                print(f"✅ URL LLM publiée avec succès sur GitHub ({repo}/storage/llm_url.txt)")
                return True
    except Exception as e:
        print(f"❌ Erreur lors de la publication sur GitHub: {e}")
    
    return False

def send_render_webhook(url, render_url=None, secret=None):
    """
    Envoie le webhook POST vers Render/Hermes WebUI.
    """
    if not render_url:
        render_url = os.environ.get("RENDER_URL", "").strip()
    if not secret:
        secret = os.environ.get("LLM_URL_SECRET", "").strip()

    if not render_url:
        print("ℹ️ RENDER_URL non défini. Webhook direct ignoré.")
        return False

    endpoint = render_url.rstrip("/") + "/api/internal/update-llm-url"
    payload = {"url": f"{url}/v1"}
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Secret"] = secret

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print(f"✅ Webhook envoyé avec succès à Render ({endpoint})")
                return True
    except Exception as e:
        print(f"⚠️ Webhook Render échoué (normal si le serveur démarre encore): {e}")

    return False

if __name__ == "__main__":
    print("🔎 Recherche de l'URL du tunnel Cloudflare sur Kaggle...")
    llm_url = find_cloudflare_url()
    
    if llm_url:
        print(f"🌐 URL Cloudflare détectée : {llm_url}")
        # Écrire dans le fichier local du repo si cloné
        os.makedirs("storage", exist_ok=True)
        with open("storage/llm_url.txt", "w", encoding="utf-8") as f:
            f.write(f"{llm_url}/v1\n")
            
        publish_to_github(llm_url)
        send_render_webhook(llm_url)
    else:
        print("❌ Aucune URL Cloudflare trouvée après 30s d'attente.")
