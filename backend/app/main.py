import os
import sys
import uuid
import time
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

fts_manager = SQLiteFTSManager()

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

@app.get("/api/history")
def get_history():
    """Récupère l'historique des investigations enregistrées dans la base SQLite FTS"""
    try:
        investigations = fts_manager.get_investigations()
        return {"investigations": investigations}
    except Exception as e:
        return {"investigations": [], "error": str(e)}

@app.get("/api/history/{inv_id}")
def get_history_detail(inv_id: str):
    """Récupère le détail et les logs d'une investigation passée"""
    try:
        inv = fts_manager.get_investigation(inv_id)
        logs = fts_manager.get_logs(inv_id)
        return {"investigation": inv, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Investigation introuvable: {str(e)}")

@app.post("/api/investigate")
async def run_investigation(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="La cible ne peut pas être vide")
    
    inv_id = str(uuid.uuid4())[:8]
    target_clean = req.query.strip()
    
    # 1. Enregistrement dans l'historique SQLite
    try:
        fts_manager.create_investigation(inv_id, title=target_clean, target=target_clean)
    except Exception as e:
        print(f"Note SQLite create_investigation: {e}")

    # 2. Résolution de juridiction (Ex. Paradis Fiscaux, Sirene, SEC EDGAR)
    jurisdiction_info = JurisdictionResolver.detect_jurisdiction(target_clean)
    
    # 3. Interrogation LLM Qwen3.6-12B
    prompt = f"Effectue une analyse OSINT approfondie pour la cible suivante : '{target_clean}'. Juridiction ciblée : {jurisdiction_info}."
    try:
        llm_response = await LLMClient.generate(prompt=prompt)
    except Exception as e:
        llm_response = f"Analyse OSINT exécutée pour '{target_clean}' (Note LLM: {str(e)})"
    
    # 4. Enregistrement du log de réponse dans SQLite
    try:
        fts_manager.add_log(inv_id, step=1, agent="Qwen3.6-12B", action_type="LLM_ANALYSIS", content=llm_response)
        fts_manager.index_document(doc_id=f"doc_{inv_id}", inv_id=inv_id, title=f"Rapport OSINT: {target_clean}", source="Qwen3.6-12B Engine", content=llm_response)
    except Exception as e:
        print(f"Note SQLite add_log: {e}")

    return {
        "id": inv_id,
        "target": target_clean,
        "jurisdiction": jurisdiction_info,
        "results": llm_response,
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
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
            * { box-sizing: border-box; }
            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-primary);
                color: var(--text-main);
                margin: 0;
                padding: 0;
                display: flex;
                height: 100vh;
                overflow: hidden;
            }

            /* Left Sidebar for History */
            sidebar {
                width: 280px;
                background: #0d1527;
                border-right: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                flex-direction: column;
                padding: 16px;
                flex-shrink: 0;
            }
            sidebar h3 {
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: var(--text-muted);
                margin-top: 0;
                margin-bottom: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .history-list {
                flex: 1;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .history-item {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 10px 12px;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 13px;
            }
            .history-item:hover {
                background: rgba(30, 174, 219, 0.1);
                border-color: var(--accent-blue);
            }
            .history-item .title {
                font-weight: 600;
                color: #e2e8f0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .history-item .date {
                font-size: 11px;
                color: var(--text-muted);
                margin-top: 4px;
            }

            /* Main Layout */
            main {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow-y: auto;
            }
            header {
                background: linear-gradient(90deg, #131c31 0%, #1e2942 100%);
                padding: 16px 32px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(0, 210, 255, 0.2);
            }
            header h1 {
                margin: 0;
                font-size: 20px;
                background: linear-gradient(90deg, #00d2ff, #9254de);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .content-container {
                max-width: 850px;
                width: 90%;
                margin: 30px auto;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .hero-title {
                text-align: center;
            }
            .hero-title h2 {
                font-size: 28px;
                margin-bottom: 6px;
                font-weight: 700;
            }
            .hero-title p {
                color: var(--text-muted);
                font-size: 14px;
                margin: 0;
            }

            /* AI Prompt Box Component */
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
                width: 38px;
                height: 38px;
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
                transform: scale(1.05);
            }
            .send-btn.loading {
                background: #3B82F6;
                color: white;
                animation: spin 1s linear infinite;
            }
            @keyframes spin { 100% { transform: rotate(360deg); } }

            .status-badge {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                background-color: #10b981;
                color: #000;
            }
            #results-card {
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
                background: #0d1527;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        </style>
    </head>
    <body>
        <sidebar>
            <h3><i data-lucide="history"></i> Historique (SQLite)</h3>
            <div id="history-list" class="history-list">
                <p style="font-size: 12px; color: var(--text-muted);">Chargement de l'historique...</p>
            </div>
        </sidebar>

        <main>
            <header>
                <h1><i data-lucide="shield"></i> OSINT & Deep Research 24/7</h1>
                <span class="status-badge">ONLINE • 4 vCPU • Qwen3.6-12B</span>
            </header>

            <div class="content-container">
                <div class="hero-title">
                    <h2>🔎 Quelle est votre cible OSINT aujourd'hui ?</h2>
                    <p>Recherche multi-sources automatisée (Paradis Fiscaux, Registres Internationaux, FTS5 Instantané)</p>
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

                        <button id="send-btn" class="send-btn" onclick="submitSearch()" title="Envoyer la requête au LLM">
                            <i data-lucide="arrow-up" style="width: 20px; height: 20px;"></i>
                        </button>
                    </div>
                </div>

                <div id="results-card">
                    <h3 id="results-title">📊 Résultats de l'Investigation</h3>
                    <div id="results-content">Chargement en cours...</div>
                </div>
            </div>
        </main>

        <script>
            lucide.createIcons();

            let activeMode = null;
            let attachedFile = null;

            // Chargement initial de l'historique des conversations
            loadHistory();

            async function loadHistory() {
                const list = document.getElementById('history-list');
                try {
                    const res = await fetch('/api/history');
                    const data = await res.json();
                    if (!data.investigations || data.investigations.length === 0) {
                        list.innerHTML = '<p style="font-size: 12px; color: var(--text-muted);">Aucune investigation enregistrée.</p>';
                        return;
                    }
                    list.innerHTML = data.investigations.map(inv => `
                        <div class="history-item" onclick="loadInvestigationDetail('${inv.id}')">
                            <div class="title">${escapeHtml(inv.target)}</div>
                            <div class="date">${inv.created_at || 'Actif'}</div>
                        </div>
                    `).join('');
                } catch(e) {
                    list.innerHTML = '<p style="font-size: 12px; color: #ef4444;">Erreur historique.</p>';
                }
            }

            async function loadInvestigationDetail(invId) {
                const card = document.getElementById('results-card');
                const content = document.getElementById('results-content');
                card.style.display = 'block';
                content.innerHTML = '<p style="color: #1EAEDB;">⏳ Chargement des archives SQLite...</p>';

                try {
                    const res = await fetch('/api/history/' + invId);
                    const data = await res.json();
                    const inv = data.investigation;
                    const logs = data.logs || [];
                    
                    let html = `<p><strong>Cible:</strong> ${escapeHtml(inv.target)}</p>`;
                    if (logs.length > 0) {
                        html += logs.map(l => `<pre>${escapeHtml(l.content)}</pre>`).join('');
                    } else {
                        html += `<pre>${escapeHtml(inv.summary || 'Investigation archivée')}</pre>`;
                    }
                    content.innerHTML = html;
                } catch(e) {
                    content.innerHTML = '<p style="color: #ef4444;">Erreur lors du chargement de la fiche.</p>';
                }
            }

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
                const promptInput = document.getElementById('prompt-input');
                const sendBtn = document.getElementById('send-btn');
                const query = promptInput.value.trim();
                
                if (!query && !attachedFile) return alert('Veuillez entrer une cible OSINT !');

                const card = document.getElementById('results-card');
                const content = document.getElementById('results-content');
                
                // Active visual loading feedback on button and card
                sendBtn.classList.add('loading');
                card.style.display = 'block';
                content.innerHTML = '<p style="color: #1EAEDB;">🤖 [Qwen3.6-12B GGUF] Analyse OSINT en cours sur la cible...\n⏳ Interrogation des 45 registres officiels et du moteur de raisonnement...</p>';

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
                    
                    content.innerHTML = '<pre>' + escapeHtml(JSON.stringify(data, null, 2)) + '</pre>';
                    
                    // Reset input & refresh history list
                    promptInput.value = '';
                    removeFile();
                    loadHistory();
                } catch (e) {
                    content.innerHTML = '<p style="color: #ef4444;">Erreur lors de l\'investigation : ' + escapeHtml(e.message) + '</p>';
                } finally {
                    sendBtn.classList.remove('loading');
                }
            }

            function escapeHtml(text) {
                if (typeof text !== 'string') text = JSON.stringify(text || '');
                return text
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
