FROM node:22-slim

# Installer les dépendances système requises (pour la compilation de SQLite FTS5 si nécessaire)
RUN apt-get update && apt-get install -y python3 make g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copier les configurations d'espace de travail npm
COPY package*.json ./
COPY tsconfig.json ./

# Installer toutes les dépendances
RUN npm install

# Copier le code source de l'application
COPY extensions/ ./extensions/
COPY workspace/ ./workspace/

# Exposer le port par défaut utilisé par Render
EXPOSE 8000

# Lancer la Gateway OpenClaw avec ts-node pour simplifier le développement
CMD ["npx", "ts-node", "extensions/osint-tools/src/server.ts"]
