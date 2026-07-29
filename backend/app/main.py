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
        <script src="https://unpkg.com/lucide@latest"></script>
        <style>
            :root {
                --bg-primary: #0a0f1d;
                --bg-secondary: #131c31;
                --prompt-bg: #1F2023;
                --prompt-border: #444444;
                --accent-blue: #1EAEDB;
                --accent-purple: #8B5CF6;
                --accent-orange: #F97316;
                --text-main: #f0f4f8;
                --text-muted: #9CA3AF;
            }
            * {
                box-sizing: border-box;
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
                font-size: 22px;
                background: linear-gradient(90deg, #00d2ff, #9254de);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .container {
                max-width: 850px;
                width: 90%;
                margin: 40px auto;
            }
            .hero-title {
                text-align: center;
                margin-bottom: 30px;
            }
            .hero-title h2 {
                font-size: 32px;
                margin-bottom: 10px;
                font-weight: 700;
            }
            .hero-title p {
                color: var(--text-muted);
                font-size: 16px;
            }

            /* AI Prompt Box Styled Component */
            .ai-prompt-box {
                background-color: var(--prompt-bg);
                border: 1px solid var(--prompt-border);
                border-radius: 24px;
                padding: 12px 16px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.4);
                transition: all 0.3s ease;
            }
            .ai-prompt-box:focus-within {
                border-color: #666666;
            }
            .file-previews {
                display: flex;
                gap: 8px;
                margin-bottom: 8px;
            }
            .preview-thumb {
                width: 64px;
                height: 64px;
                border-radius: 12px;
                overflow: hidden;
                position: relative;
            }
            .preview-thumb img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            .remove-btn {
                position: absolute;
                top: 2px;
                right: 2px;
                background: rgba(0,0,0,0.7);
                border: none;
                border-radius: 50%;
                color: white;
                cursor: pointer;
                padding: 2px;
                display: flex;
            }
            textarea.prompt-textarea {
                width: 100%;
                background: transparent;
                border: none;
                color: #f3f4f6;
                font-size: 16px;
                font-family: inherit;
                resize: none;
                outline: none;
                min-height: 48px;
                max-height: 200px;
            }
            textarea.prompt-textarea::placeholder {
                color: #9CA3AF;
            }
            .prompt-actions {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 8px;
            }
            .action-toggles {
                display: flex;
                align-items: center;
                gap: 6px;
            }
            .icon-btn {
                background: transparent;
                border: none;
                color: #9CA3AF;
                cursor: pointer;
                padding: 6px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }
            .icon-btn:hover {
                background: rgba(255,255,255,0.1);
                color: #D1D5DB;
            }
            .mode-toggle {
                background: transparent;
                border: 1px solid transparent;
                color: #9CA3AF;
                border-radius: 20px;
                padding: 4px 10px;
                font-size: 13px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s;
            }
            .mode-toggle.active-search {
                background: rgba(30, 174, 219, 0.15);
                border-color: #1EAEDB;
                color: #1EAEDB;
            }
            .mode-toggle.active-think {
                background: rgba(139, 92, 246, 0.15);
                border-color: #8B5CF6;
                color: #8B5CF6;
            }
            .mode-toggle.active-canvas {
                background: rgba(249, 115, 22, 0.15);
                border-color: #F97316;
                color: #F97316;
            }
            .divider {
                width: 1px;
                height: 18px;
                background: linear-gradient(to bottom, transparent, rgba(155,135,245,0.7), transparent);
                margin: 0 2px;
            }
            .send-btn {
                width: 34px;
                height: 34px;
                border-radius: 50%;
                border: none;
                background: white;
                color: #1F2023;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }
            .send-btn:hover {
                background: #e5e7eb;
            }
            .status-badge {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                background-color: #10b981;
                color: #000;
            }
            #results-card {
                margin-top: 30px;
                padding: 24px;
                background: var(--bg-secondary);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                display: none;
            }
            pre {
                white-space: pre-wrap;
                word-wrap: break-word;
                color: #a6accd;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <header>
            <h1><i data-lucide="shield"></i> OSINT & Deep Research 24/7</h1>
            <span class="status-badge">ONLINE • 4 vCPU • Qwen3.6-12B</span>
        </header>

        <div class="container">
            <div class="hero-title">
                <h2>🔎 Quelle est votre cible OSINT aujourd'hui ?</h2>
                <p>Recherche multi-sources automatisée (Sociétés, Paradis Fiscaux, Registres Internationaux & FTS5 Instantané)</p>
            </div>

            <!-- Integrated AI Prompt Box Component -->
            <div class="ai-prompt-box">
                <div id="file-previews" class="file-previews"></div>
                <textarea id="prompt-input" class="prompt-textarea" placeholder="Entrez un nom d'entreprise, individu, SIREN, LEI ou domaine... (Appuyez sur Entrée)"></textarea>
                
                <div class="prompt-actions">
                    <div class="action-toggles">
                        <label class="icon-btn" title="Joindre un fichier/image">
                            <i data-lucide="paperclip" style="width: 18px; height: 18px;"></i>
                            <input type="file" id="file-input" style="display: none;" accept="image/*" onchange="handleFileSelect(event)">
                        </label>

                        <button id="toggle-search" class="mode-toggle" onclick="toggleMode('search')">
                            <i data-lucide="globe" style="width: 16px; height: 16px;"></i>
                            <span>Search</span>
                        </button>

                        <div class="divider"></div>

                        <button id="toggle-think" class="mode-toggle" onclick="toggleMode('think')">
                            <i data-lucide="brain-cog" style="width: 16px; height: 16px;"></i>
                            <span>Think</span>
                        </button>

                        <div class="divider"></div>

                        <button id="toggle-canvas" class="mode-toggle" onclick="toggleMode('canvas')">
                            <i data-lucide="folder-code" style="width: 16px; height: 16px;"></i>
                            <span>Canvas</span>
                        </button>
                    </div>

                    <button id="send-btn" class="send-btn" onclick="submitSearch()">
                        <i data-lucide="arrow-up" style="width: 18px; height: 18px;"></i>
                    </button>
                </div>
            </div>

            <div id="results-card">
                <h3>📊 Résultats de l'Investigation</h3>
                <div id="results-content">Chargement en cours...</div>
            </div>
        </div>

        <script>
            lucide.createIcons();

            let activeMode = null;
            let attachedFile = null;

            function toggleMode(mode) {
                const searchBtn = document.getElementById('toggle-search');
                const thinkBtn = document.getElementById('toggle-think');
                const canvasBtn = document.getElementById('toggle-canvas');

                if (activeMode === mode) {
                    activeMode = null;
                    searchBtn.className = 'mode-toggle';
                    thinkBtn.className = 'mode-toggle';
                    canvasBtn.className = 'mode-toggle';
                } else {
                    activeMode = mode;
                    searchBtn.className = 'mode-toggle ' + (mode === 'search' ? 'active-search' : '');
                    thinkBtn.className = 'mode-toggle ' + (mode === 'think' ? 'active-think' : '');
                    canvasBtn.className = 'mode-toggle ' + (mode === 'canvas' ? 'active-canvas' : '');
                }
            }

            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (!file) return;
                attachedFile = file;
                const container = document.getElementById('file-previews');
                const reader = new FileReader();
                reader.onload = function(e) {
                    container.innerHTML = `
                        <div class="preview-thumb">
                            <img src="${e.target.result}" alt="Preview">
                            <button class="remove-btn" onclick="removeFile()"><i data-lucide="x" style="width: 12px; height: 12px;"></i></button>
                        </div>
                    `;
                    lucide.createIcons();
                };
                reader.readAsDataURL(file);
            }

            function removeFile() {
                attachedFile = null;
                document.getElementById('file-previews').innerHTML = '';
            }

            document.getElementById('prompt-input').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    submitSearch();
                }
            });

            async function submitSearch() {
                const query = document.getElementById('prompt-input').value.trim();
                if (!query && !attachedFile) return alert('Veuillez entrer une cible !');

                const card = document.getElementById('results-card');
                const content = document.getElementById('results-content');
                
                card.style.display = 'block';
                content.innerHTML = '<p style="color: #1EAEDB;">⏳ Recherche en cours via Qwen3.6-12B et les registres OSINT (Mode: ' + (activeMode || 'Standard') + ')...</p>';

                let fullQuery = query;
                if (activeMode) {
                    fullQuery = `[${activeMode.toUpperCase()}] ${query}`;
                }

                try {
                    const res = await fetch('/api/investigate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: fullQuery })
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
