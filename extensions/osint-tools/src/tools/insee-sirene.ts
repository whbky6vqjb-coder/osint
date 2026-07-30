import { defineTool } from "openclaw/plugin-sdk";
import { ForensicEvidenceTracker } from "../forensics/tracker";

export const inseeSireneLookup = defineTool({
  name: "insee_sirene_lookup",
  description: "Interroge le registre légal français INSEE SIRENE pour identifier une entreprise (SIRET/SIREN).",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Numéro SIREN, SIRET ou Nom de l'entreprise" }
    },
    required: ["query"]
  },
  async execute({ query }, context) {
    const isNumber = /^\d+$/.test(query.replace(/\s/g, ""));
    const cleaned = query.replace(/\s/g, "");
    
    let url = "";
    if (isNumber) {
      url = cleaned.length === 9 
        ? `https://sirene.api.gouv.fr/v3/siren/${cleaned}`
        : `https://sirene.api.gouv.fr/v3/siret/${cleaned}`;
    } else {
      url = `https://sirene.api.gouv.fr/v3/siren?q=raisonSociale:${encodeURIComponent(query)}`;
    }
    
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      
      const data = await res.json();
      
      // Mettre en forme le résultat de manière lisible
      const output = data;

      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("insee_sirene_lookup", url, { query }, output);
      }

      return { status: "success", data: output };
    } catch (e: any) {
      console.error(`[SIRENE Tool] Erreur : ${e.message}`);
      const errOut = { status: "error", message: e.message };
      
      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("insee_sirene_lookup", url, { query }, errOut);
      }
      
      return errOut;
    }
  }
});
