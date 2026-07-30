import json
import hashlib
from datetime import datetime
import secrets

class ForensicEvidenceTracker:
    def __init__(self, investigation_id: str):
        self.investigation_id = investigation_id
        self.evidence_log = []
        self.chain_of_custody = []
        self.log_chain("Initialisation de l'investigation médico-légale numérique.")

    def log_chain(self, action: str):
        timestamp = datetime.utcnow().isoformat() + "Z"
        self.chain_of_custody.append(f"[{timestamp}] {action}")

    def register_evidence(self, tool_name: str, url: str, input_params: any, raw_output: any) -> dict:
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Normaliser le format de l'output brut pour le hachage
        if isinstance(raw_output, (dict, list)):
            raw_output_str = json.dumps(raw_output, sort_keys=True)
        else:
            raw_output_str = str(raw_output)
            
        sha256 = hashlib.sha256(raw_output_str.encode("utf-8")).hexdigest()
        
        # Générer un ID unique de preuve EV-YYYYMMDD-HEX
        date_str = datetime.utcnow().strftime("%Y%m%d")
        random_hex = secrets.token_hex(3)
        evidence_id = f"EV-{date_str}-{random_hex.upper()}"

        record = {
            "id": evidence_id,
            "timestamp": timestamp,
            "tool_name": tool_name,
            "source_url": url,
            "raw_input": input_params,
            "raw_output": raw_output_str,
            "sha256": sha256
        }

        self.evidence_log.append(record)
        self.log_chain(f"Preuve collectée par l'outil '{tool_name}' (ID: {evidence_id}, SHA-256: {sha256[:16]}...)")
        return record

    def get_manifest(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "evidence_count": len(self.evidence_log),
            "evidence": self.evidence_log,
            "chain_of_custody": self.chain_of_custody
        }
