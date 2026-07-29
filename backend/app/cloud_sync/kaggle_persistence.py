import os
import shutil
import time

class KagglePersistenceManager:
    @staticmethod
    def checkpoint_state():
        try:
            storage_dir = "/kaggle/working/storage"
            backup_dir = "/kaggle/working/storage_backups"
            os.makedirs(storage_dir, exist_ok=True)
            os.makedirs(backup_dir, exist_ok=True)
            
            db_file = os.path.join(storage_dir, "database.sqlite")
            if os.path.exists(db_file):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(backup_dir, f"database_checkpoint_{timestamp}.sqlite")
                shutil.copy2(db_file, backup_file)
                print(f"🟢 [Checkpoint State] Base SQLite sauvegardée avec succès : {backup_file}")
            else:
                print("ℹ️ [Checkpoint State] Base SQLite initialisée et prête.")
        except Exception as e:
            print(f"⚠️ [Checkpoint State Error] : {e}")
