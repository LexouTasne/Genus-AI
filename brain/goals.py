import os
import json
import time
import datetime
import hashlib
import threading
from config.settings import GOALS_FILE

INIT_GOALS = [
    {"id": "own_api", "p": 10, "cat": "ia", "title": "API Flask própria", "steps": ["Flask /chat /health /train /status", "integrar ollama", "testar porta 7532", "usar como primário"]},
    {"id": "ollama", "p": 9, "cat": "ia", "title": "Instalar ollama", "steps": ["verificar/instalar ollama", "testar ollama serve"]},
    {"id": "base_mdl", "p": 9, "cat": "ia", "title": "Baixar modelo base", "steps": ["checar disco", "baixar tinyllama", "testar inferência"]},
    {"id": "rag", "p": 8, "cat": "learn", "title": "RAG memória longa", "steps": ["embeddings TF-IDF", "indexar histórico", "usar contexto recuperado"]},
    {"id": "whisper", "p": 7, "cat": "voz", "title": "STT Whisper local", "steps": ["instalar whisper.cpp", "substituir Google STT"]},
    {"id": "fine_tune", "p": 6, "cat": "ia", "title": "Fine-tune modelo local", "steps": ["100+ amostras prontas", "llama.cpp fine-tune CPU", "avaliar resultado"]},
    {"id": "monitor", "p": 5, "cat": "learn", "title": "Monitor de notícias IA", "steps": ["fontes arxiv/hn", "scheduler diário", "salvar no RAG"]},
]

class Goals:
    def __init__(self):
        self.g = []
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        if os.path.exists(GOALS_FILE):
            try:
                with open(GOALS_FILE, encoding="utf-8") as f:
                    self.g = json.load(f)
                ex = {x["id"] for x in self.g}
                for g in INIT_GOALS:
                    if g["id"] not in ex:
                        e = dict(g)
                        e.update({
                            "status": "pending",
                            "step": 0,
                            "log": [],
                            "created": datetime.datetime.now().isoformat(),
                            "priority": g["p"]
                        })
                        e.pop("p", None)
                        self.g.append(e)
                self._save()
                return
            except:
                pass
        self.g = []
        for g in INIT_GOALS:
            e = dict(g)
            e.update({
                "status": "pending",
                "step": 0,
                "log": [],
                "created": datetime.datetime.now().isoformat(),
                "priority": g["p"]
            })
            e.pop("p", None)
            self.g.append(e)
        self._save()

    def _save(self):
        with open(GOALS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.g, f, indent=2, ensure_ascii=False)

    def next(self):
        with self._lock:
            p = [x for x in self.g if x["status"] in ("pending", "active") and not x.get("paused")]
            return max(p, key=lambda x: x["priority"]) if p else None

    def done_step(self, gid, note=""):
        with self._lock:
            for x in self.g:
                if x["id"] == gid:
                    x["log"].append({"step": x["step"], "note": note, "t": datetime.datetime.now().isoformat()})
                    x["step"] += 1
                    x["status"] = "active"
                    if x["step"] >= len(x.get("steps", [])):
                        x["status"] = "done"
                        x["done"] = datetime.datetime.now().isoformat()
                    self._save()
                    return

    def add(self, title, steps, priority=5, cat="custom", paused=False):
        with self._lock:
            gid = hashlib.md5(title.encode()).hexdigest()[:8]
            if any(x["id"] == gid for x in self.g):
                return gid
            self.g.append({
                "id": gid, "title": title, "steps": steps, "priority": priority, "cat": cat,
                "status": "pending", "step": 0, "log": [], "paused": paused,
                "created": datetime.datetime.now().isoformat()
            })
            self._save()
            return gid

    def set_paused(self, gid, v):
        with self._lock:
            for x in self.g:
                if x["id"] == gid:
                    x["paused"] = v
                    self._save()
                    return True
            return False

    def mark_incomplete(self, gid):
        with self._lock:
            for x in self.g:
                if x["id"] == gid:
                    x["status"] = "pending"
                    x["step"] = 0
                    self._save()
                    return True
            return False

    def summary(self):
        done = sum(1 for x in self.g if x["status"] == "done")
        return f"{done}/{len(self.g)} metas concluídas"

    def all_done(self):
        return all(x["status"] == "done" for x in self.g)

# Singleton
goals = Goals()
