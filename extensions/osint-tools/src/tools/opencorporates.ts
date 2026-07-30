import { defineTool } from "openclaw/plugin-sdk";
import { ForensicEvidenceTracker } from "../forensics/tracker";

export const opencorporatesSearch = defineTool({
  name: "opencorporates_search",
  description: "Recherche une entreprise dans OpenCorporates et extrait son adresse légale et ses statuts.",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Nom de l'entreprise ou marque" },
      jurisdiction: { type: "string", description: "Optionnel: code juridiction (ex: fr, us, gb)" }
    },
    required: ["query"]
  },
  async execute({ query, jurisdiction }, context) {
    const url = `https://api.opencorporates.com/v0.4/companies/search?q=${encodeURIComponent(query)}${jurisdiction ? `&jurisdiction_code=${jurisdiction}` : ""}`;
    
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      
      const data = await res.json();
      const results = data?.results?.companies?.slice(0, 5) || [];
      
      const output = results.map((c: any) => ({
        name: c.company?.name,
        jurisdiction: c.company?.jurisdiction_code,
        company_number: c.company?.company_number,
        status: c.company?.current_status,
        registered_address: c.company?.registered_address_in_full,
        incorporation_date: c.company?.incorporation_date
      }));

      // Si un tracker médico-légal est actif dans la session, on certifie la preuve
      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("opencorporates_search", url, { query, jurisdiction }, output);
      }

      return { status: "success", count: output.length, data: output };
    } catch (e: any) {
      console.error(`[OpenCorporates Tool] Erreur : ${e.message}`);
      const errOut = { status: "error", message: e.message };
      
      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("opencorporates_search", url, { query, jurisdiction }, errOut);
      }
      
      return errOut;
    }
  }
});
