import os
import json
import time
import re
import math
import threading
from collections import Counter
from config.settings import RAG_FILE

class RAG:
    MAX = 2000
    K = 5
    
    def __init__(self):
        self._docs = []
        self._idf = {}
        self._lock = threading.Lock()
        self._dirty = False
        self._load()
        threading.Thread(target=self._saver, daemon=True).start()

    def _tok(self, t):
        w = re.sub(r'[^\w\s]', ' ', t.lower()).split()
        return w + [f"{w[i]}_{w[i+1]}" for i in range(len(w)-1)]

    def _tf(self, t):
        c = Counter(t)
        n = len(t) or 1
        return {k: v/n for k, v in c.items()}

    def _rebuild(self):
        n = len(self._docs) or 1
        df = Counter()
        for d in self._docs:
            for t in set(self._tok(d["text"])):
                df[t] += 1
        self._idf = {t: math.log(n/(v+1)) for t, v in df.items()}

    def _tfidf(self, t):
        tf = self._tf(t)
        return {k: tf[k]*self._idf.get(k, 1.0) for k in tf}

    def _cos(self, a, b):
        k = set(a) & set(b)
        if not k:
            return 0.0
        d = sum(a[x]*b[x] for x in k)
        na = math.sqrt(sum(v*v for v in a.values())) or 1
        nb = math.sqrt(sum(v*v for v in b.values())) or 1
        return d/(na*nb)

    def add(self, text, meta=None):
        if not text or len(text) < 10:
            return
        with self._lock:
            self._docs.append({"text": text, "meta": meta or {}})
            if len(self._docs) > self.MAX:
                self._docs = self._docs[-self.MAX:]
            self._dirty = True
            if len(self._docs) % 50 == 0:
                self._rebuild()

    def search(self, q, k=None):
        k = k or self.K
        with self._lock:
            if not self._docs:
                return []
            if not self._idf:
                self._rebuild()
            qv = self._tfidf(self._tok(q))
            # Usando uma chave de ordenação que evita comparar dicionários
            s = sorted([(self._cos(qv, self._tfidf(self._tok(d["text"]))), i, d) 
                       for i, d in enumerate(self._docs)], reverse=True, key=lambda x: x[0])
            return [d for sc, i, d in s if sc > 0.05][:k]

    def ctx(self, q, n=500):
        r = self.search(q)
        return "\n".join(d["text"] for d in r)[:n] if r else ""

    def _load(self):
        if os.path.exists(RAG_FILE):
            try:
                with open(RAG_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                self._docs = data.get("docs", [])
                self._idf = data.get("idf", {})
            except:
                pass

    def _saver(self):
        while True:
            time.sleep(30)
            if self._dirty:
                try:
                    with self._lock:
                        data = {"docs": self._docs[-self.MAX:], "idf": self._idf}
                        self._dirty = False
                    with open(RAG_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                except:
                    pass

# Singleton
rag = RAG()
