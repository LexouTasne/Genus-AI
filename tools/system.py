import os
import subprocess
import urllib.parse
import urllib.request
import re
import html
import webbrowser

class SystemTools:
    @staticmethod
    def bash(cmd, timeout=15):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=os.path.expanduser("~"))
            out = (r.stdout + r.stderr).strip()
            return out[:800] if out else "(sem output)"
        except subprocess.TimeoutExpired:
            return "Timeout."
        except Exception as e:
            return f"Erro: {e}"

    @staticmethod
    def read(path):
        try:
            with open(os.path.expanduser(path), encoding="utf-8", errors="replace") as f:
                return f.read(4000)
        except Exception as e:
            return f"Erro: {e}"

    @staticmethod
    def write(path, content):
        try:
            p = os.path.expanduser(path)
            os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Salvo: {p}"
        except Exception as e:
            return f"Erro: {e}"

    @staticmethod
    def ls(path="~"):
        try:
            return "  ".join(sorted(os.listdir(os.path.expanduser(path)))[:50])
        except Exception as e:
            return f"Erro: {e}"

    @staticmethod
    def web(query, n=3):
        try:
            q = urllib.parse.quote(query)
            req = urllib.request.Request(f"https://html.duckduckgo.com/html/?q={q}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                body = r.read().decode("utf-8", errors="replace")
            sn = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', body, re.DOTALL)
            ti = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', body, re.DOTALL)
            out = []
            for t, s in zip(ti[:n], sn[:n]):
                tc = html.unescape(re.sub(r'<[^>]+>', '', t).strip())
                sc = html.unescape(re.sub(r'<[^>]+>', '', s).strip())
                if tc or sc:
                    out.append(f"{tc}: {sc}")
            return "\n".join(out) if out else "Sem resultados."
        except Exception as e:
            return f"Erro: {e}"

    @staticmethod
    def open_url(url):
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Abrindo {url}"

    @staticmethod
    def volume(pct):
        pct = max(0, min(100, int(pct)))
        subprocess.run(f"pactl set-sink-volume @DEFAULT_SINK@ {pct}%", shell=True)
        return f"Volume {pct}%"
