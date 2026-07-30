import { defineTool } from "openclaw/plugin-sdk";
import { ForensicEvidenceTracker } from "../forensics/tracker";

export const icijOffshoreLeaks = defineTool({
  name: "icij_offshore_leaks",
  description: "Recherche des entités offshore ou bénéficiaires dans la base ICIJ (Panama Papers, Paradise Papers...).",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Nom de l'entité ou personne" }
    },
    required: ["query"]
  },
  async execute({ query }, context) {
    const url = `https://offshoreleaks.icij.org/api/v1/search?q=${encodeURIComponent(query)}`;
    
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      
      const data = await res.json();
      const output = data?.results?.slice(0, 5) || [];

      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("icij_offshore_leaks", url, { query }, output);
      }

      return { status: "success", count: output.length, data: output };
    } catch (e: any) {
      console.error(`[ICIJ Tool] Erreur : ${e.message}`);
      const errOut = { status: "error", message: e.message };
      
      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("icij_offshore_leaks", url, { query }, errOut);
      }
      
      return errOut;
    }
  }
});
