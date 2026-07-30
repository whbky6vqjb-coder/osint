import json

def generate_legal_report(manifest: dict, target: str, analysis_summary: str) -> str:
    md = f"# RAPPORT D'INVESTIGATION ET DE PRÉSERVATION DE PREUVES NUMÉRIQUES\n"
    md += f"**Dossier N° :** {manifest['investigation_id']}\n"
    md += f"**Date de génération :** {manifest['generated_at']} (UTC)\n"
    md += f"**Cible de l'investigation :** {target}\n"
    md += f"**Statut juridique :** Rapport de préservation numérique (Standard ISO/IEC 27037)\n\n"

    md += f"## 1. DÉCLARATION D'INTÉGRITÉ & MÉTHODOLOGIE\n"
    md += f"Le présent rapport a été généré de manière automatisée par un agent d'investigation autonome certifié.\n"
    md += f"Chaque élément de preuve listé ci-dessous a fait l'objet d'un calcul d'empreinte cryptographique SHA-256 immédiatement au moment de son acquisition. "
    md += f"Toute modification ultérieure du contenu altérerait l'empreinte, invalidant la preuve.\n\n"

    md += f"## 2. SYNTHÈSE DE L'INVESTIGATION\n"
    md += f"{analysis_summary}\n\n"

    md += f"## 3. INVENTAIRE DES PREUVES CONSERVÉES\n"
    md += f"| ID Preuve | Horodatage (UTC) | Source / Outil | Empreinte Numérique (SHA-256) |\n"
    md += f"| :--- | :--- | :--- | :--- |\n"
    for ev in manifest["evidence"]:
        md += f"| {ev['id']} | {ev['timestamp']} | {ev['tool_name']} | `{ev['sha256']}` |\n"
    md += f"\n"

    md += f"## 4. CHAÎNE DE CONTRÔLE (CHAIN OF CUSTODY LOG)\n"
    md += f"Ce journal retrace chronologiquement toutes les étapes d'acquisition et de traitement des données :\n"
    for step in manifest["chain_of_custody"]:
        md += f"- {step}\n"
    md += f"\n"

    md += f"## 5. ANNEXE TECHNIQUE (EXTRAITS BRUTS)\n"
    for ev in manifest["evidence"]:
        md += f"### Preuve {ev['id']} ({ev['tool_name']})\n"
        md += f"**URL source :** {ev['source_url']}\n"
        md += f"**Paramètres d'acquisition :** `{json.dumps(ev['raw_input'])}`\n"
        
        # Tronquer l'affichage si le contenu brut est extrêmement long
        raw_out = ev['raw_output']
        if len(raw_out) > 1500:
            truncated = raw_out[:1500] + "\n...[Tronqué pour la lisibilité de l'annexe papier]"
        else:
            truncated = raw_out
            
        md += f"```json\n{truncated}\n```\n\n"

    return md
