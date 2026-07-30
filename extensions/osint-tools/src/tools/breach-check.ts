import { defineTool } from "openclaw/plugin-sdk";
import { ForensicEvidenceTracker } from "../forensics/tracker";

export const breachCheck = defineTool({
  name: "breach_check",
  description: "Vérifie si une adresse e-mail ou un domaine a subi des fuites d'identifiants ou de mots de passe.",
  parameters: {
    type: "object",
    properties: {
      target: { type: "string", description: "Adresse e-mail ou nom de domaine à analyser" }
    },
    required: ["target"]
  },
  async execute({ target }, context) {
    const isEmail = target.includes("@");
    const endpoint = isEmail ? "breachedaccount" : "breacheddomain";
    const url = `https://api.xposedornot.com/v1/${endpoint}/${encodeURIComponent(target)}`;
    
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
      
      // L'API XposedOrNot renvoie une erreur 404 si aucune fuite n'est trouvée, ce qui est un résultat positif !
      if (res.status === 404) {
        const output = { status: "clean", message: "Aucune fuite d'identifiant détectée pour cette cible." };
        const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
        if (tracker) {
          tracker.registerEvidence("breach_check", url, { target }, output);
        }
        return output;
      }
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      
      const data = await res.json();
      const output = { status: "breached", data };

      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("breach_check", url, { target }, output);
      }

      return output;
    } catch (e: any) {
      console.error(`[BreachCheck Tool] Erreur : ${e.message}`);
      const errOut = { status: "error", message: e.message };
      
      const tracker = context.session?.state?.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.registerEvidence("breach_check", url, { target }, errOut);
      }
      
      return errOut;
    }
  }
});
