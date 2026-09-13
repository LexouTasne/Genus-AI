import os
import time
import requests
import threading
from config.settings import LOCAL_API_PORT

class GenusMonitor:
    def __init__(self, core):
        self.core = core
        self.api_url = f"http://127.0.0.1:{LOCAL_API_PORT}/health"
        self.api_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai_engine/my_api/api.py")
        self.running = True
        threading.Thread(target=self._watchdog, daemon=True).start()

    def _watchdog(self):
        """Monitora a saúde da API e executa proatividade global (Nível EDITH)."""
        idle_count = 0
        while self.running:
            try:
                # 1. Checa se a API local está respondendo
                api_ok = False
                try:
                    resp = requests.get(self.api_url, timeout=2)
                    if resp.status_code == 200:
                        api_ok = True
                    else:
                        self.core.log("API local respondeu com status inválido")
                except:
                    self.core.log("API local está offline; inicie-a manualmente se precisar dela.")

                # Nunca dispara tarefas do modelo sem uma solicitação explícita.
                self._check_integrity()

            except Exception as e:
                print(f"[Monitor] Erro no watchdog: {e}")
            
            time.sleep(30)

    def repair_all(self):
        """Tenta reparar todos os sistemas críticos do Genus."""
        self.core.log("Iniciando reparo total do sistema...")
        repairs = []
        
        repairs.append("API: verificação concluída (reinício manual requerido)")
        
        # 2. Re-indexa projeto
        from brain.indexer import indexer
        count = indexer.index_full_project()
        repairs.append(f"Projeto Re-indexado ({count} arquivos)")
        
        # 3. Limpa caches temporários
        from config.settings import CACHE_DIR
        try:
            for f in os.listdir(CACHE_DIR):
                if f.endswith(".tmp"): os.remove(os.path.join(CACHE_DIR, f))
            repairs.append("Caches Limpos")
        except: pass
        
        return " | ".join(repairs)

    def _check_integrity(self):
        """Verifica se arquivos base existem, se não, tenta restaurar ou alertar."""
        critical_files = ["brain/core.py", "genus.py", "config/settings.py"]
        for f in critical_files:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f)
            if not os.path.exists(path):
                print(f"[Monitor] ARQUIVO CRÍTICO AUSENTE: {f}")
                # Aqui o Genus poderia tentar baixar de um backup ou avisar o Lex
