import os
import time
from brain.rag import rag
from config.settings import BASE_DIR

class ProjectIndexer:
    def __init__(self, root_dir=BASE_DIR):
        self.root_dir = root_dir
        self.ignored_dirs = [".git", ".venv", "__pycache__", "memory", "tts_cache", "node_modules"]
        self.allowed_extensions = [".py", ".sh", ".txt", ".json", ".js", ".md"]

    def index_full_project(self):
        print(f"[Indexer] Iniciando indexação total de {self.root_dir}...")
        count = 0
        for root, dirs, files in os.walk(self.root_dir):
            # Remove diretórios ignorados
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                if file.startswith(".") or file in {"apis.txt", ".env"}:
                    continue
                if any(file.endswith(ext) for ext in self.allowed_extensions):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if len(content.strip()) > 0:
                                # Adiciona ao RAG com metadados do arquivo
                                rag.add(f"ARQUIVO: {path}\nCONTEÚDO:\n{content}", {"type": "codebase", "path": path})
                                count += 1
                                # Pequena pausa para não travar a CPU se houver muitos arquivos
                                if count % 10 == 0: time.sleep(0.1)
                    except Exception as e:
                        print(f"[Indexer] Erro ao ler {path}: {e}")
        
        print(f"[Indexer] Concluído. {count} arquivos indexados na memória de longo prazo.")
        return count

# Singleton para uso no core
indexer = ProjectIndexer()
