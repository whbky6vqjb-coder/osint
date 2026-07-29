import asyncio
import json
import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger("AutonomousOSINTDaemon")

class AutonomousOSINTDaemon:
    """
    Worker Daemon d'exécution perpétuelle non-stop (24/7 sur Kaggle / SQLite).
    Évalue le score de preuve (evidence_score) et relance les investigations
    sur les sous-pistes extraites tant que le seuil de certitude (95%) n'est pas atteint.
    """
    def __init__(self, fts_manager=None):
        self.fts_manager = fts_manager
        self.is_running = False
        self.target_queue: List[Dict[str, Any]] = []

    def add_investigation_target(self, target: str, initial_jurisdiction: str = "AUTO") -> str:
        inv_task = {
            "target": target,
            "jurisdiction": initial_jurisdiction,
            "evidence_score": 0,
            "iteration": 1,
            "unexplored_leads": [target],
            "status": "QUEUED",
            "created_at": time.time()
        }
        self.target_queue.append(inv_task)
        logger.info(f"⚡ Cible '{target}' ajoutée à la file d'attente du Daemon Non-Stop.")
        return target

    def evaluate_evidence_score(self, tool_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule la certitude des preuves récoltées et extrait les nouvelles pistes"""
        matched_records = sum(1 for t in tool_sequence if t.get("output", {}).get("records_matched", 0) > 0)
        total_tools = len(tool_sequence)
        
        # Base score calculation
        evidence_score = min(98, round((matched_records / max(1, total_tools)) * 100 + 45, 1))
        
        # Extraire nouvelles sous-pistes (e-mails, domaines, filiales)
        new_leads = []
        for tool in tool_sequence:
            output = tool.get("output", {})
            if isinstance(output, dict):
                if "breaches_list" in output:
                    new_leads.extend(output["breaches_list"][:2])
                if "nom_complet" in output and output["nom_complet"]:
                    new_leads.append(output["nom_complet"])

        return {
            "evidence_score": evidence_score,
            "certainty_reached": evidence_score >= 95,
            "matched_records_count": matched_records,
            "new_leads_extracted": list(set(new_leads)),
            "status": "CERTAINTY_REACHED" if evidence_score >= 95 else "CONTINUOUS_SEARCH_REQUIRED"
        }

    async def start_daemon_loop(self):
        """Boucle asynchrone non-stop"""
        self.is_running = True
        logger.info("🔄 Démarrage du Daemon OSINT Autonome Non-Stop 24/7...")
        while self.is_running:
            if self.target_queue:
                current_task = self.target_queue.pop(0)
                current_task["status"] = "PROCESSING"
                logger.info(f"🔍 Daemon en cours sur : {current_task['target']} (Passe #{current_task['iteration']})")
                await asyncio.sleep(0.5) # Traitement simulé
            else:
                await asyncio.sleep(2) # Pause d'attente si file vide
