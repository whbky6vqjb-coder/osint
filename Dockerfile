FROM node:22-slim

# Installer les dépendances : Python 3, pip, Git, curl, make et procps
RUN apt-get update && apt-get install -y python3 python3-pip git curl make procps && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# 1. Cloner et installer OpenClaw (Node.js)
RUN git clone https://github.com/openclaw/openclaw.git openclaw-gateway
RUN cd openclaw-gateway && corepack enable && pnpm install

# 2. Cloner et installer Hermes Agent (Python)
RUN git clone https://github.com/NousResearch/hermes-agent.git hermes-agent
RUN cd hermes-agent && pip install -r requirements.txt --break-system-packages

# 3. Cloner et configurer openclaw-hermes-watcher
RUN git clone https://github.com/teddashh/openclaw-hermes-watcher.git watcher
RUN cd watcher && cp config/machine.env.example config/machine.env

# 4. Copier nos outils OSINT et le moteur Forensics existants vers le dossier Hermes
COPY backend/app/tools/ /usr/src/app/hermes-agent/tools/
COPY backend/app/forensics/ /usr/src/app/hermes-agent/forensics/
COPY backend/app/main.py /usr/src/app/hermes-agent/main.py

# Exposer le port par défaut utilisé par le Dashboard OpenClaw
EXPOSE 8000

# Lancement des daemons géré par le Watcher
CMD ["bash", "watcher/scripts/all.sh"]
