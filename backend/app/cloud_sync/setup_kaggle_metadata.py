import json
import os
import sys

def setup_metadata():
    username = os.environ.get("KAGGLE_USERNAME", "").strip().replace("\r", "").replace("\n", "")
    repo_name = os.environ.get("GITHUB_REPOSITORY", "").strip()
    gh_token = os.environ.get("GH_TOKEN", "").strip()
    
    if not username:
        raise ValueError("KAGGLE_USERNAME environment variable is missing")
        
    metadata_path = "./kaggle_runtime/kernel-metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["id"] = f"{username}/osint-agent-247-runner"
        data["title"] = "osint-agent-247-runner"
        data["enable_gpu"] = "false"  # Mode CPU 100% Gratuit & Illimité
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Metadata configurée avec id: {data['id']} (Mode CPU Pure Illimité)")

    # Injection automatique de la réponse HTTP 200 Ping Test & du Token GitHub dans le Notebook
    notebook_path = "./kaggle_runtime/kaggle_osint_runner.ipynb"
    if os.path.exists(notebook_path):
        with open(notebook_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if repo_name and gh_token:
            tokenized_url = f"https://x-access-token:{gh_token}@github.com/{repo_name}.git"
            content = content.replace("https://github.com/your-repo/projet_osint.git", tokenized_url)
            content = content.replace("https://github.com/whbky6vqjb-coder/osint.git", tokenized_url)
            print(f"Notebook mis à jour avec le jeton d'accès privé GitHub pour : {repo_name}")
        elif repo_name:
            public_git_url = f"https://github.com/{repo_name}.git"
            content = content.replace("https://github.com/your-repo/projet_osint.git", public_git_url)
            content = content.replace("https://github.com/whbky6vqjb-coder/osint.git", public_git_url)
            print(f"Notebook mis à jour avec l'URL publique Git : {public_git_url}")

        with open(notebook_path, "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    setup_metadata()
