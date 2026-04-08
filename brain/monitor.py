import os
import subprocess
import time
import requests
import threading

class GenusMonitor:
    def __init__(self, core):
        self.core = core
        self.api_url = "http://localhost:7532/health"
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
                        self._fix_api("Status inválido")
                except:
                    self._fix_api("API offline")

                # 2. Proatividade Global (EDITH Protocol)
                if api_ok:
                    idle_count += 1
                    # A cada 5 minutos de idle, realiza uma varredura de melhoria
                    if idle_count >= 10: 
                        print("[Monitor] Protocolo EDITH: Iniciando varredura de otimização em background...")
                        self.core.process_input("Realize uma varredura de otimização no seu próprio código e sugira melhorias.")
                        idle_count = 0

                # 3. Checa integridade
                self._check_integrity()

            except Exception as e:
                print(f"[Monitor] Erro no watchdog: {e}")
            
            time.sleep(30)

    def repair_all(self):
        """Tenta reparar todos os sistemas críticos do Genus."""
        self.core.log("Iniciando reparo total do sistema...")
        repairs = []
        
        # 1. Repara API
        self._fix_api("Reparo manual solicitado")
        repairs.append("API Reiniciada")
        
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

    def _fix_api(self, reason):
        print(f"[Monitor] Reparando API local ({reason})...")
        try:
            # Mata processos antigos na porta 7532
            subprocess.run("fuser -k 7532/tcp", shell=True, stderr=subprocess.DEVNULL)
            # Inicia a API novamente
            subprocess.Popen([os.sys.executable, self.api_path], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(2)
            print("[Monitor] API reiniciada com sucesso.")
        except Exception as e:
            print(f"[Monitor] Falha ao reparar API: {e}")

    def _check_integrity(self):
        """Verifica se arquivos base existem, se não, tenta restaurar ou alertar."""
        critical_files = ["brain/core.py", "genus.py", "config/settings.py"]
        for f in critical_files:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f)
            if not os.path.exists(path):
                print(f"[Monitor] ARQUIVO CRÍTICO AUSENTE: {f}")
                # Aqui o Genus poderia tentar baixar de um backup ou avisar o Lex
