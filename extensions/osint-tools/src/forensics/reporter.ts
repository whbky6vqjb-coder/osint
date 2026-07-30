export function generateLegalReport(manifest: any, target: string, analysisSummary: string): string {
  let md = `# RAPPORT D'INVESTIGATION ET DE PRÉSERVATION DE PREUVES NUMÉRIQUES\n`;
  md += `**Dossier N° :** ${manifest.investigationId}\n`;
  md += `**Date de génération :** ${manifest.generatedAt} (UTC)\n`;
  md += `**Cible de l'investigation :** ${target}\n`;
  md += `**Statut juridique :** Rapport de préservation numérique (Standard ISO/IEC 27037)\n\n`;

  md += `## 1. DÉCLARATION D'INTÉGRITÉ & MÉTHODOLOGIE\n`;
  md += `Le présent rapport a été généré de manière automatisée par un agent d'investigation autonome certifié.\n`;
  md += `Chaque élément de preuve listé ci-dessous a fait l'objet d'un calcul d'empreinte cryptographique SHA-256 immédiatement au moment de son acquisition. `;
  md += `Toute modification ultérieure du contenu altérerait l'empreinte, invalidant la preuve.\n\n`;

  md += `## 2. SYNTHÈSE DE L'INVESTIGATION\n`;
  md += `${analysisSummary}\n\n`;

  md += `## 3. INVENTAIRE DES PREUVES CONSERVÉES\n`;
  md += `| ID Preuve | Horodatage (UTC) | Source / Outil | Empreinte Numérique (SHA-256) |\n`;
  md += `| :--- | :--- | :--- | :--- |\n`;
  for (const ev of manifest.evidence) {
    md += `| ${ev.id} | ${ev.timestamp} | ${ev.toolName} | \`${ev.sha256}\` |\n`;
  }
  md += `\n`;

  md += `## 4. CHAÎNE DE CONTRÔLE (CHAIN OF CUSTODY LOG)\n`;
  md += `Ce journal retrace chronologiquement toutes les étapes d'acquisition et de traitement des données :\n`;
  for (const step of manifest.chainOfCustody) {
    md += `- ${step}\n`;
  }
  md += `\n`;

  md += `## 5. ANNEXE TECHNIQUE (EXTRAITS BRUTS)\n`;
  for (const ev of manifest.evidence) {
    md += `### Preuve ${ev.id} (${ev.toolName})\n`;
    md += `**URL source :** ${ev.sourceUrl}\n`;
    md += `**Paramètres d'acquisition :** \`${JSON.stringify(ev.rawInput)}\`\n`;
    md += `\`\`\`json\n${ev.rawOutput.slice(0, 1500)}${ev.rawOutput.length > 1500 ? '\n...[Tronqué pour la lisibilité de l\'annexe]' : ''}\n\`\`\`\n\n`;
  }

  return md;
}
