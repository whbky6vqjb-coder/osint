import * as express from 'express';
import * as path from 'path';
import { updateKaggleLLMUrl, getKaggleLLMUrl } from './providers/kaggle-llm';

const app = express();
const PORT = process.env.PORT || 8000;

app.use(express.json());

// Servir l'interface utilisateur statique (Dashboard)
app.use(express.static(path.join(__dirname, '../../../../frontend')));

// Webhook pour mettre à jour dynamiquement l'URL du LLM hébergé sur Kaggle
app.post("/api/internal/update-llm-url", (req, res) => {
  const { url } = req.body;
  const secret = req.headers["x-secret"];
  
  const expectedSecret = process.env.LLM_URL_SECRET || "default_secret";
  
  if (secret !== expectedSecret) {
    console.warn("[SECURITY] Tentative de mise à jour de l'URL LLM non autorisée.");
    return res.status(403).json({ error: "Non autorisé" });
  }

  if (!url) {
    return res.status(400).json({ error: "Paramètre URL manquant" });
  }

  updateKaggleLLMUrl(url);
  res.json({ status: "success", message: "URL LLM mise à jour.", current_url: url });
});

// Endpoint pour vérifier l'état du serveur et de l'URL LLM
app.get("/api/health", (req, res) => {
  res.json({
    status: "healthy",
    framework: "OpenClaw + Hermes",
    llm_connected: getKaggleLLMUrl() !== "",
    llm_url: getKaggleLLMUrl()
  });
});

app.listen(PORT, () => {
  console.log(`[OSINT Server] Serveur démarré sur le port ${PORT}`);
  console.log(`[OSINT Server] En attente de la connexion du LLM de Kaggle...`);
});
