import os
import json
import datetime
import urllib.parse
import urllib.request
import re
import html
from config.settings import MEM_DIR
from brain.rag import rag

class Researcher:
    def __init__(self, call_fn, tools):
        self._call = call_fn
        self._tools = tools
        self._kf = os.path.join(MEM_DIR, "research.json")
        self._k = {}
        self._load()

    def _load(self):
        if os.path.exists(self._kf):
            try:
                with open(self._kf, encoding="utf-8") as f:
                    self._k = json.load(f)
            except:
                pass

    def research(self, topic):
        web = self._tools.web(topic)
        synth = self._call([{"role": "user", "content": f"Pesquisei '{topic}':\n{web}\nSintetize 3-5 pontos práticos. Técnico e direto."}], max_tokens=400) or web
        rag.add(f"Pesquisa: {topic} — {synth[:300]}", {"type": "research"})
        self._k[topic] = {"synthesis": synth[:700], "t": datetime.datetime.now().isoformat()}
        try:
            with open(self._kf, "w", encoding="utf-8") as f:
                json.dump(self._k, f, indent=2, ensure_ascii=False)
        except:
            pass
        return synth

    def know(self, topic):
        for k, v in self._k.items():
            if topic.lower() in k.lower():
                return v.get("synthesis", "")
        return rag.ctx(topic, 400)
