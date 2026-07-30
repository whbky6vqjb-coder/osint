import { defineTool } from "openclaw/plugin-sdk";
import { ForensicEvidenceTracker } from "../forensics/tracker";

export const openSanctionsCheck = defineTool({
  name: "open_sanctions_check",
  description: "Vérifie si une entité ou personne physique est sous sanctions internationales.",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Nom complet de l'entité ou personne" }
    },
    required: ["query"]
  },
  async execute({ query }, context) {
    const url = `https://api.opensanctions.org/search/default?q=${encodeURIComponent(query)}`;
    
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      
      const data = await res.json();
      const output = data?.results?.slice(0, 5) || [];

      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("open_sanctions_check", url, { query }, output);
      }

      return { status: "success", count: output.length, data: output };
    } catch (e: any) {
      console.error(`[OpenSanctions Tool] Erreur : ${e.message}`);
      const errOut = { status: "error", message: e.message };
      
      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("open_sanctions_check", url, { query }, errOut);
      }
      
      return errOut;
    }
  }
});
