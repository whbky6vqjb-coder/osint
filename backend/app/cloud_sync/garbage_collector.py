import os
import shutil
import time

class GarbageCollectorManager:
    @staticmethod
    def cleanup_temp_storage():
        try:
            tmp_dirs = ["/tmp", "/kaggle/working/tmp"]
            cleaned_files_count = 0
            for tdir in tmp_dirs:
                if os.path.exists(tdir):
                    for item in os.listdir(tdir):
                        item_path = os.path.join(tdir, item)
                        try:
                            if os.path.isfile(item_path) or os.path.islink(item_path):
                                os.unlink(item_path)
                                cleaned_files_count += 1
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                                cleaned_files_count += 1
                        except Exception:
                            pass
            print(f"🟢 [Garbage Collector] Nettoyage réussi : {cleaned_files_count} éléments temporaires supprimés.")
        except Exception as e:
            print(f"⚠️ [Garbage Collector Error] : {e}")
