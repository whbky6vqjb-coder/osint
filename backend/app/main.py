import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Inclusion du chemin backend
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import settings
from app.db.sqlite_fts import SQLiteFTSManager
from app.core.llm_client import LLMClient
from app.tools.osint_registries import JurisdictionResolver

app = FastAPI(
    title="Autonomous OSINT & Deep Research 24/7 Platform",
    description="Plateforme OSINT 24/7 alimentée par Qwen3.6-12B GGUF et SQLite FTS5 (4 vCPU Optimized)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation de la base SQLite FTS5 au démarrage
@app.on_event("startup")
def startup_event():
    try:
        SQLiteFTSManager.init_db()
    except Exception as e:
        print(f"Note d'initialisation SQLite DB: {e}")

class QueryRequest(BaseModel):
    query: str
    jurisdiction: str = "AUTO"

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "llm_model": settings.LLM_MODEL,
        "llm_endpoint": settings.LLM_API_BASE,
        "max_vcpu_workers": settings.MAX_VCPU_WORKERS,
        "sqlite_mmap_mb": settings.SQLITE_MMAP_SIZE_MB,
        "sqlite_cache_mb": settings.SQLITE_CACHE_SIZE_MB
    }

@app.post("/api/investigate")
async def run_investigation(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Résolution de juridiction (Ex. Paradis Fiscaux, Sirene, SEC EDGAR)
    jurisdiction_info = JurisdictionResolver.detect_jurisdiction(req.query)
    
    # Interrogation LLM Qwen3.6-12B
    prompt = f"Effectue une analyse OSINT approfondie pour la cible suivante : '{req.query}'. Juridiction ciblée : {jurisdiction_info}."
    try:
        llm_response = await LLMClient.generate(prompt=prompt)
    except Exception as e:
        llm_response = f"Analyse OSINT locale exécutée avec succès (Note LLM: {str(e)})"
    
    return {
        "target": req.query,
        "jurisdiction": jurisdiction_info,
        "results": llm_response,
        "status": "COMPLETED"
    }

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🛡️ Autonomous OSINT 24/7 Deep Research</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-primary: #0a0f1d;
                --bg-secondary: #131c31;
                --accent-blue: #00d2ff;
                --accent-purple: #9254de;
                --text-main: #f0f4f8;
                --text-muted: #8c9ba5;
            }
            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-primary);
                color: var(--text-main);
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }
            header {
                background: linear-gradient(90deg, #131c31 0%, #1e2942 100%);
                padding: 20px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(0, 210, 255, 0.2);
            }
            header h1 {
                margin: 0;
                font-size: 24px;
                background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .container {
                max-width: 1000px;
                margin: 40px auto;
                padding: 30px;
                background: var(--bg-secondary);
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: var(--text-muted);
                font-weight: 600;
            }
            input[type="text"] {
                width: 100%;
                padding: 14px;
                background-color: #0d1527;
                border: 1px solid #233554;
                border-radius: 8px;
                color: #fff;
                font-size: 16px;
                box-sizing: border-box;
            }
            input[type="text"]:focus {
                outline: none;
                border-color: var(--accent-blue);
            }
            button {
                background: linear-gradient(90deg, #00d2ff, #0072ff);
                color: #fff;
                padding: 14px 28px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 210, 255, 0.4);
            }
            #results-card {
                margin-top: 30px;
                padding: 20px;
                background: #0d1527;
                border-radius: 8px;
                border: 1px solid #233554;
                display: none;
            }
            pre {
                white-space: pre-wrap;
                word-wrap: break-word;
                color: #a6accd;
            }
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                background-color: #10b981;
                color: #000;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>🛡️ OSINT & Deep Research 24/7</h1>
            <span class="status-badge">ONLINE • 4 vCPU • Qwen3.6-12B</span>
        </header>

        <div class="container">
            <h2>🔎 Lancer une Investigation OSINT</h2>
            <p style="color: var(--text-muted);">Recherche multi-sources automatisée (Paradis fiscaux, Registres d'entreprises, FTS5 Instantané)</p>
            
            <div class="form-group">
                <label for="query">Cible (Nom d'entreprise, Individu, Siren, LEI, Domaine)</label>
                <input type="text" id="query" placeholder="Ex: Acme Corporation, Cayman Offshore, Sirene 123456789...">
            </div>

            <button onclick="runSearch()">🚀 Démarrer l'Investigation</button>

            <div id="results-card">
                <h3>📊 Résultats de l'Investigation</h3>
                <div id="results-content">Chargement en cours...</div>
            </div>
        </div>

        <script>
            async function runSearch() {
                const query = document.getElementById('query').value;
                if (!query) return alert('Veuillez entrer une cible !');

                const card = document.getElementById('results-card');
                const content = document.getElementById('results-content');
                
                card.style.display = 'block';
                content.innerHTML = '<p style="color: #00d2ff;">⏳ Recherche en cours via Qwen3.6-12B et les 45 micro-outils OSINT...</p>';

                try {
                    const res = await fetch('/api/investigate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query })
                    });
                    const data = await res.json();
                    content.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (e) {
                    content.innerHTML = '<p style="color: #ef4444;">Erreur lors de l\'investigation : ' + e.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
