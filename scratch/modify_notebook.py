import json

notebook_path = "kaggle_runtime/kaggle_osint_runner.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Code de remplacement pour la cellule 4
new_source = [
    "# 4. Tunnel HTTPS Cloudflare redirigé vers llama-server (Port 8080) & Envoi de l'URL à Render\n",
    "import os, sys, subprocess, time, re, urllib.request, json\n",
    "\n",
    "print('Installation de cloudflared...')\n",
    "!curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared || true\n",
    "\n",
    "subprocess.run(['pkill', '-f', 'cloudflared'])\n",
    "time.sleep(1)\n",
    "\n",
    "print('Lancement du Tunnel HTTPS Cloudflare pour llama-server (Port 8080)...')\n",
    "tunnel_process = subprocess.Popen(['cloudflared', 'tunnel', '--url', 'http://localhost:8080'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)\n",
    "\n",
    "url_found = None\n",
    "render_url = os.environ.get('RENDER_URL', 'https://osint-app.onrender.com')\n",
    "llm_secret = os.environ.get('LLM_URL_SECRET', 'default_secret')\n",
    "\n",
    "for _ in range(40):\n",
    "    line = tunnel_process.stdout.readline()\n",
    "    if line and 'trycloudflare.com' in line:\n",
    "        match = re.search(r'https://[a-zA-Z0-9-]+\\.trycloudflare\\.com', line)\n",
    "        if match:\n",
    "            url_found = match.group(0)\n",
    "            print('\\n======================================================')\n",
    "            print(f'🚀 LLM TUNNEL EST EN LIGNE : {url_found}')\n",
    "            print('======================================================\\n')\n",
    "            \n",
    "            # POST au serveur sur Render\n",
    "            print(f'Envoi de la nouvelle URL LLM au serveur Render ({render_url})...')\n",
    "            try:\n",
    "                req = urllib.request.Request(\n",
    "                    f'{render_url}/api/internal/update-llm-url',\n",
    "                    data=json.dumps({'url': f'{url_found}/v1'}).encode('utf-8'),\n",
    "                    headers={\n",
    "                        'Content-Type': 'application/json',\n",
    "                        'X-Secret': llm_secret\n",
    "                    },\n",
    "                    method='POST'\n",
    "                )\n",
    "                with urllib.request.urlopen(req) as response:\n",
    "                    res_data = json.loads(response.read().decode())\n",
    "                    print(f'✅ Serveur Render mis à jour : {res_data}')\n",
    "            except Exception as e:\n",
    "                print(f'❌ Échec de mise à jour Render : {e}')\n",
    "            break\n",
    "    time.sleep(0.5)\n",
    "\n",
    "if not url_found:\n",
    "    print('⚠️ Capture Cloudflare : Le tunnel s\\'initialise en tâche de fond.')"
]

# Remplacer la source de la 4ème cellule (index 3)
data["cells"][3]["source"] = new_source

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print("[OK] Notebook mis a jour avec succes !")
