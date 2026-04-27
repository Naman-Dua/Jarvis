import os
import time
import threading
from ingest_docs import ingest_file

class KnowledgeWatcher(threading.Thread):
    def __init__(self, ui_log_callback):
        super().__init__(daemon=True)
        self.ui_log = ui_log_callback
        self.knowledge_dir = os.path.join(os.getcwd(), "knowledge")
        self.processed_files = set()
        os.makedirs(self.knowledge_dir, exist_ok=True)

    def run(self):
        self.ui_log("SYSTEM", f"Knowledge Watcher active. Monitoring: {self.knowledge_dir}")
        
        # Initial scan to skip existing files or decide if we should ingest them
        # For now, let's just watch for NEW files while running
        self.processed_files = set(os.listdir(self.knowledge_dir))

        while True:
            try:
                current_files = set(os.listdir(self.knowledge_dir))
                new_files = current_files - self.processed_files
                
                for filename in new_files:
                    if filename.endswith((".pdf", ".txt", ".md")):
                        path = os.path.join(self.knowledge_dir, filename)
                        self.ui_log("SYSTEM", f"Auto-ingesting new knowledge: {filename}")
                        try:
                            # Wait a moment to ensure file is fully written
                            time.sleep(1) 
                            count = ingest_file(path)
                            self.ui_log("KORA", f"Learned {count} sections from {filename} automatically.")
                        except Exception as e:
                            self.ui_log("SYSTEM", f"Failed to auto-ingest {filename}: {e}")
                
                self.processed_files = current_files
            except Exception as e:
                print(f"[WATCHER ERROR] {e}")
            
            time.sleep(5)
