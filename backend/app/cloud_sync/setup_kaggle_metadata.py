import json
import os

def setup_metadata():
    username = os.environ.get("KAGGLE_USERNAME", "").strip().replace("\r", "").replace("\n", "")
    repo_name = os.environ.get("GITHUB_REPOSITORY", "").strip()
    
    if not username:
        raise ValueError("KAGGLE_USERNAME environment variable is missing")
        
    metadata_path = "./kaggle_runtime/kernel-metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["id"] = f"{username}/osint-agent-247-runner"
        data["title"] = "osint-agent-247-runner"
        data["enable_gpu"] = "false"  # Mode CPU 100% Gratuit & Illimité (0 minute de quota GPU consommée)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Metadata configurée avec id: {data['id']} (Mode CPU Pure Illimité)")

    # Injection automatique du dépôt GitHub réel dans le Notebook Kaggle
    notebook_path = "./kaggle_runtime/kaggle_osint_runner.ipynb"
    if os.path.exists(notebook_path) and repo_name:
        with open(notebook_path, "r", encoding="utf-8") as f:
            content = f.read()
        real_git_url = f"https://github.com/{repo_name}.git"
        updated_content = content.replace("https://github.com/your-repo/projet_osint.git", real_git_url)
        with open(notebook_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Notebook mis à jour avec le dépôt Git réel: {real_git_url}")

if __name__ == "__main__":
    setup_metadata()
