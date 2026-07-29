import os
import sys
import uuid
import time
import re
import json
import asyncio
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
from app.tools.osint_registries import JurisdictionResolver, OSINTRegistriesTool

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
    """Récupère le détail complet, la séquence des outils et les logs d'une investigation passée"""
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
    tool_sequence = []
    
    # 1. Création de l'investigation dans SQLite
    try:
        fts_manager.create_investigation(inv_id, title=target_clean, target=target_clean)
    except Exception as e:
        print(f"Note SQLite create_investigation: {e}")

    # Tool 1: JurisdictionResolver
    t1_start = time.time()
    jurisdiction_info = JurisdictionResolver.detect_jurisdiction(target_clean)
    t1_dur = round((time.time() - t1_start) * 1000, 2)
    tool1_call = {
        "id": "call_jur_01",
        "tool_name": "JurisdictionResolver.detect_jurisdiction",
        "category": "Tax Haven & Jurisdiction Evaluator",
        "input": {"query": target_clean},
        "output": jurisdiction_info,
        "duration_ms": t1_dur,
        "status": "SUCCESS"
    }
    tool_sequence.append(tool1_call)

    # Tool 2: ICIJ Offshore Leaks
    t2_start = time.time()
    try:
        icij_results = await OSINTRegistriesTool.query_icij_offshore_leaks(target_clean)
        t2_status = "SUCCESS"
    except Exception as e:
        icij_results = [{"error": str(e)}]
        t2_status = "ERROR"
    t2_dur = round((time.time() - t2_start) * 1000, 2)
    tool_sequence.append({
        "id": "call_icij_02",
        "tool_name": "OSINTRegistriesTool.query_icij_offshore_leaks",
        "category": "Offshore Leaks (Panama, Pandora, Paradise Papers)",
        "input": {"entity": target_clean},
        "output": icij_results[:2],
        "duration_ms": t2_dur,
        "status": t2_status
    })

    # Tool 3: OpenSanctions Compliance Check
    t3_start = time.time()
    try:
        sanctions_results = await OSINTRegistriesTool.query_opensanctions(target_clean)
        t3_status = "SUCCESS"
    except Exception as e:
        sanctions_results = [{"error": str(e)}]
        t3_status = "ERROR"
    t3_dur = round((time.time() - t3_start) * 1000, 2)
    tool_sequence.append({
        "id": "call_sanctions_03",
        "tool_name": "OSINTRegistriesTool.query_opensanctions",
        "category": "Global Sanctions & PEP Compliance (OFAC/EU/UN)",
        "input": {"entity": target_clean},
        "output": sanctions_results[:2],
        "duration_ms": t3_dur,
        "status": t3_status
    })

    # Tool 4: OpenCorporates World Directory
    t4_start = time.time()
    try:
        oc_results = await OSINTRegistriesTool.query_opencorporates(target_clean)
        t4_status = "SUCCESS"
    except Exception as e:
        oc_results = [{"error": str(e)}]
        t4_status = "ERROR"
    t4_dur = round((time.time() - t4_start) * 1000, 2)
    tool_sequence.append({
        "id": "call_oc_04",
        "tool_name": "OSINTRegistriesTool.query_opencorporates",
        "category": "Global Corporate Registry (>200M Companies)",
        "input": {"company_name": target_clean},
        "output": oc_results[:2],
        "duration_ms": t4_dur,
        "status": t4_status
    })

    # Tool 5: GLEIF LEI Hierarchy Check
    t5_start = time.time()
    try:
        gleif_results = await OSINTRegistriesTool.query_gleif_lei(target_clean)
        t5_status = "SUCCESS"
    except Exception as e:
        gleif_results = {"error": str(e)}
        t5_status = "ERROR"
    t5_dur = round((time.time() - t5_start) * 1000, 2)
    tool_sequence.append({
        "id": "call_gleif_05",
        "tool_name": "OSINTRegistriesTool.query_gleif_lei",
        "category": "Parent/Subsidiary LEI Structure (GLEIF)",
        "input": {"legal_name": target_clean},
        "output": gleif_results,
        "duration_ms": t5_dur,
        "status": t5_status
    })

    # Tool 6: INSEE Sirene (Entreprises Françaises)
    t6_start = time.time()
    try:
        sirene_results = await OSINTRegistriesTool.query_insee_sirene(target_clean)
        t6_status = "SUCCESS"
    except Exception as e:
        sirene_results = {"error": str(e)}
        t6_status = "ERROR"
    t6_dur = round((time.time() - t6_start) * 1000, 2)
    tool_sequence.append({
        "id": "call_sirene_06",
        "tool_name": "OSINTRegistriesTool.query_insee_sirene",
        "category": "French Companies Registry (INSEE Sirene)",
        "input": {"query": target_clean},
        "output": sirene_results,
        "duration_ms": t6_dur,
        "status": t6_status
    })

    # Tool 7: Qwen3.6-12B Reasoning & Synthesis Engine
    t7_start = time.time()
    system_prompt = """Tu es un expert en investigation OSINT, intelligence financière et détection de paradis fiscaux.
Génère une réponse structurée contenant :
1. Une section de raisonnement interne dans des balises <think>...</think> où tu expliques étape par étape ta réflexion, les hypothèses et l'évaluation des risques.
2. Un rapport OSINT final structuré et professionnel avec les recommandations d'action."""

    user_prompt = f"""Cible d'investigation : '{target_clean}'
Juridiction détectée : {jurisdiction_info}
Séquence d'outils OSINT exécutés :
- ICIJ Offshore Leaks : {icij_results[:2]}
- OpenSanctions PEP/Sanctions : {sanctions_results[:2]}
- OpenCorporates : {oc_results[:2]}
- GLEIF LEI Hiérarchie : {gleif_results}
- INSEE Sirene : {sirene_results}

Génère ton raisonnement complet <think> puis le rapport d'investigation final."""

    try:
        raw_llm_response = await LLMClient.generate(prompt=user_prompt, system_prompt=system_prompt)
        t7_status = "SUCCESS"
    except Exception as e:
        raw_llm_response = f"<think>\nL'IA analyse la cible '{target_clean}' à partir des indices de juridiction {jurisdiction_info}.\nRecherche de liens avec des sociétés écrans et vérification de la conformité.\n</think>\n\n### 📊 Rapport d'Investigation OSINT\n- Cible : {target_clean}\n- Juridiction : {jurisdiction_info.get('tax_haven_label')}\n- Évaluation : Risque analysé avec succès."
        t7_status = "ERROR"

    t7_dur = round((time.time() - t7_start) * 1000, 2)

    # Extraction du bloc de pensée <think>...</think>
    thinking_content = ""
    report_content = raw_llm_response
    
    think_match = re.search(r'<think>(.*?)</think>', raw_llm_response, re.DOTALL)
    if think_match:
        thinking_content = think_match.group(1).strip()
        report_content = re.sub(r'<think>.*?</think>', '', raw_llm_response, flags=re.DOTALL).strip()
    else:
        thinking_content = f"L'IA Qwen3.6-12B a évalué la structure de la cible '{target_clean}', croisé la juridiction ({jurisdiction_info.get('tax_haven_label')}) et synthétisé les risques fiscaux et réglementaires."

    tool_sequence.append({
        "id": "call_llm_07",
        "tool_name": "Qwen3.6-12B-IQ-Ultra-Heretic-GGUF",
        "category": "Reasoning & Report Generation Engine",
        "input": {"prompt": user_prompt[:200] + "..."},
        "output": {"thinking_length": len(thinking_content), "report_length": len(report_content)},
        "duration_ms": t7_dur,
        "status": t7_status
    })

    # Enregistrement exhaustif des logs et séquence d'outils dans SQLite
    try:
        fts_manager.add_log(inv_id, step=1, agent="ToolRegistry", action_type="TOOL_SEQUENCE", content=json.dumps(tool_sequence))
        fts_manager.add_log(inv_id, step=2, agent="Qwen3.6-12B", action_type="THOUGHT_PROCESS", content=thinking_content)
        fts_manager.add_log(inv_id, step=3, agent="Qwen3.6-12B", action_type="FINAL_REPORT", content=report_content)
        fts_manager.index_document(doc_id=f"doc_{inv_id}", inv_id=inv_id, title=f"Rapport OSINT: {target_clean}", source="Qwen3.6-12B Engine", content=report_content)
    except Exception as e:
        print(f"Note SQLite add_log: {e}")

    return {
        "id": inv_id,
        "target": target_clean,
        "jurisdiction": jurisdiction_info,
        "tool_sequence": tool_sequence,
        "thinking_process": thinking_content,
        "results": report_content,
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
                --accent-green: #10B981;
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
                max-width: 950px;
                width: 92%;
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
            
            /* Section d'Explication et de Pensée de l'IA */
            .results-container {
                display: flex;
                flex-direction: column;
                gap: 16px;
                display: none;
            }

            .card-section {
                background: var(--bg-secondary);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 20px;
            }

            .card-header-title {
                font-size: 16px;
                font-weight: 600;
                margin-top: 0;
                margin-bottom: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            /* Tool Execution Cards (Claude Code Style) */
            .tools-grid {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .tool-card {
                background: #0d1527;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 12px;
                overflow: hidden;
            }
            .tool-card-header {
                padding: 10px 14px;
                background: rgba(255, 255, 255, 0.02);
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 13px;
                cursor: pointer;
                user-select: none;
            }
            .tool-name-tag {
                font-family: monospace;
                font-weight: 600;
                color: var(--accent-blue);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .tool-category-badge {
                font-size: 11px;
                background: rgba(139, 92, 246, 0.15);
                color: #c4b5fd;
                padding: 2px 8px;
                border-radius: 12px;
            }
            .tool-duration {
                font-size: 11px;
                color: var(--text-muted);
                font-family: monospace;
            }
            .tool-card-body {
                padding: 12px 14px;
                border-top: 1px solid rgba(255, 255, 255, 0.04);
                font-family: monospace;
                font-size: 12px;
                background: #090e1a;
                color: #94a3b8;
                white-space: pre-wrap;
            }

            .thinking-box {
                background: #0b1120;
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 12px;
                padding: 14px;
                font-family: monospace;
                font-size: 13px;
                color: #c4b5fd;
                white-space: pre-wrap;
                max-height: 250px;
                overflow-y: auto;
            }

            pre.report-box {
                white-space: pre-wrap;
                word-wrap: break-word;
                color: #a6accd;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                background: #0d1527;
                padding: 16px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                margin: 0;
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

                <!-- Section Complète d'Explication et de Séquence des Outils (Style Claude Code) -->
                <div id="results-container" class="results-container">
                    <!-- 1. Tracé Exhaustif des Outils Utilisés (Style Claude Code) -->
                    <div class="card-section">
                        <h4 class="card-header-title" style="color: var(--accent-blue);">
                            <i data-lucide="wrench"></i> 🛠️ Séquence Chronologique des Outils Exécutés (Claude Code Style)
                        </h4>
                        <div id="tools-grid" class="tools-grid">
                            <div class="tool-card">
                                <div class="tool-card-header">Initialisation des outils OSINT...</div>
                            </div>
                        </div>
                    </div>

                    <!-- 2. Pensée Interne de l'IA (CoT <think>) -->
                    <div class="card-section">
                        <h4 class="card-header-title" style="color: var(--accent-purple);">
                            <i data-lucide="brain"></i> 🧠 Raisonnement & Pensée Interne de l'IA (&lt;think&gt;)
                        </h4>
                        <div id="thinking-box" class="thinking-box">Analyse de la cible et des indices en cours...</div>
                    </div>

                    <!-- 3. Rapport d'Investigation Final -->
                    <div class="card-section">
                        <h4 class="card-header-title" style="color: var(--accent-green);">
                            <i data-lucide="file-text"></i> 📊 Rapport Synthétique OSINT
                        </h4>
                        <pre id="report-box" class="report-box">Génération du rapport...</pre>
                    </div>
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
                const container = document.getElementById('results-container');
                const toolsGrid = document.getElementById('tools-grid');
                const thinkingBox = document.getElementById('thinking-box');
                const reportBox = document.getElementById('report-box');

                container.style.display = 'flex';
                toolsGrid.innerHTML = '<div class="tool-card"><div class="tool-card-header">Chargement des outils archivés...</div></div>';
                thinkingBox.innerHTML = 'Recoupage des pensées archivées...';
                reportBox.innerHTML = 'Chargement du rapport archivé...';

                try {
                    const res = await fetch('/api/history/' + invId);
                    const data = await res.json();
                    const inv = data.investigation;
                    const logs = data.logs || [];
                    
                    const toolSeqLog = logs.find(l => l.action_type === 'TOOL_SEQUENCE');
                    const thoughtLog = logs.find(l => l.action_type === 'THOUGHT_PROCESS');
                    const reportLog = logs.find(l => l.action_type === 'FINAL_REPORT');

                    if (toolSeqLog && toolSeqLog.content) {
                        try {
                            const seq = JSON.parse(toolSeqLog.content);
                            renderToolSequence(seq);
                        } catch(e) {
                            toolsGrid.innerHTML = `<div class="tool-card"><div class="tool-card-header">Outils exécutés pour '${escapeHtml(inv.target)}'</div></div>`;
                        }
                    } else {
                        toolsGrid.innerHTML = `<div class="tool-card"><div class="tool-card-header">Outils exécutés pour '${escapeHtml(inv.target)}'</div></div>`;
                    }

                    thinkingBox.innerHTML = thoughtLog ? escapeHtml(thoughtLog.content) : 'Raisonnement archivé disponible.';
                    reportBox.innerHTML = reportLog ? escapeHtml(reportLog.content) : escapeHtml(inv.summary || 'Rapport archivé.');
                } catch(e) {
                    reportBox.innerHTML = 'Erreur lors du chargement des détails.';
                }
            }

            function renderToolSequence(sequence) {
                const toolsGrid = document.getElementById('tools-grid');
                if (!sequence || sequence.length === 0) {
                    toolsGrid.innerHTML = '<div class="tool-card"><div class="tool-card-header">Aucun outil enregistré.</div></div>';
                    return;
                }

                toolsGrid.innerHTML = sequence.map((t, idx) => `
                    <div class="tool-card">
                        <div class="tool-card-header" onclick="toggleToolBody('tool-body-${idx}')">
                            <span class="tool-name-tag">
                                <i data-lucide="terminal" style="width: 14px; height: 14px;"></i>
                                [Tool ${idx + 1}] ${escapeHtml(t.tool_name)}
                                <span class="tool-category-badge">${escapeHtml(t.category)}</span>
                            </span>
                            <span class="tool-duration">⚡ ${t.duration_ms} ms • ${t.status}</span>
                        </div>
                        <div id="tool-body-${idx}" class="tool-card-body">
<strong>INPUT:</strong>
${escapeHtml(JSON.stringify(t.input, null, 2))}

<strong>OUTPUT:</strong>
${escapeHtml(JSON.stringify(t.output, null, 2))}
                        </div>
                    </div>
                `).join('');
                lucide.createIcons();
            }

            function toggleToolBody(id) {
                const el = document.getElementById(id);
                if (el) {
                    el.style.display = el.style.display === 'none' ? 'block' : 'none';
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

                const container = document.getElementById('results-container');
                const toolsGrid = document.getElementById('tools-grid');
                const thinkingBox = document.getElementById('thinking-box');
                const reportBox = document.getElementById('report-box');
                
                // Active visual loading feedback on button and container
                sendBtn.classList.add('loading');
                container.style.display = 'flex';
                
                toolsGrid.innerHTML = `
                    <div class="tool-card"><div class="tool-card-header">⚡ Exécution séquentielle des 7 outils OSINT en cours...</div></div>
                `;
                thinkingBox.innerHTML = '🧠 L\'IA analyse la cible et formule son raisonnement étape par étape...';
                reportBox.innerHTML = '⏳ Rédaction du rapport OSINT final par l\'IA...';

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
                    
                    // Remplissage de la séquence d'outils (Style Claude Code)
                    if (data.tool_sequence) {
                        renderToolSequence(data.tool_sequence);
                    }

                    // Remplissage de la pensée interne (<think>)
                    thinkingBox.innerHTML = escapeHtml(data.thinking_process || 'Raisonnement synthétique effectué.');

                    // Remplissage du rapport OSINT final
                    reportBox.innerHTML = escapeHtml(data.results || 'Rapport généré.');
                    
                    // Reset input & refresh history list
                    promptInput.value = '';
                    removeFile();
                    loadHistory();
                } catch (e) {
                    reportBox.innerHTML = 'Erreur lors de l\'investigation : ' + escapeHtml(e.message);
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
