import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { kaggleLLMProvider, updateKaggleLLMUrl } from "./providers/kaggle-llm";
import { ForensicEvidenceTracker } from "./forensics/tracker";
import { generateLegalReport } from "./forensics/reporter";

// Outils OSINT individuels
import { opencorporatesSearch } from "./tools/opencorporates";
import { icijOffshoreLeaks } from "./tools/icij-leaks";
import { openSanctionsCheck } from "./tools/open-sanctions";
import { inseeSireneLookup } from "./tools/insee-sirene";
import { breachCheck } from "./tools/breach-check";

export default definePluginEntry({
  id: "osint-tools",
  
  async register(api) {
    console.log("[OSINT Plugin] Initialisation du plugin d'investigation légale...");

    // Enregistrer le provider LLM Kaggle custom
    api.registerModelProvider(kaggleLLMProvider);

    // Initialiser le tracker légal pour les sessions d'investigation
    api.on("sessionStart", (session) => {
      console.log(`[OSINT Plugin] Nouvelle session démarrée : ${session.id}`);
      session.state.forensics = new ForensicEvidenceTracker(session.id);
    });

    api.on("sessionEnd", async (session) => {
      const tracker = session.state.forensics as ForensicEvidenceTracker;
      if (tracker) {
        tracker.logChain("Fin de session d'investigation.");
        const manifest = tracker.getManifest();
        const report = generateLegalReport(manifest, session.target || "Inconnue", session.summary || "");
        
        // Exporter le rapport au format certifié SHA-256 dans le workspace de session
        session.addAttachment({
          name: `Rapport_Judiciaire_${session.id}.md`,
          type: "text/markdown",
          content: report
        });
        console.log(`[OSINT Plugin] Rapport de preuves cryptographiques généré pour la session ${session.id}`);
      }
    });

    // Enregistrer les outils OSINT
    api.registerTool("opencorporates_search", opencorporatesSearch);
    api.registerTool("icij_offshore_leaks", icijOffshoreLeaks);
    api.registerTool("open_sanctions_check", openSanctionsCheck);
    api.registerTool("insee_sirene_lookup", inseeSireneLookup);
    api.registerTool("breach_check", breachCheck);
  }
});
