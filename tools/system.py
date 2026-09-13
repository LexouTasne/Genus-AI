"""Ferramentas locais com limites explícitos de capacidade."""
import html
import os
import re
import shlex
import subprocess
import urllib.parse
import urllib.request
import webbrowser


class SystemTools:
    def __init__(self, workspace, allow_commands=False, allowed_commands=()):
        self.workspace = os.path.realpath(workspace)
        self.allow_commands = allow_commands
        self.allowed_commands = frozenset(allowed_commands)

    def _workspace_path(self, path):
        target = os.path.realpath(os.path.join(self.workspace, os.path.expanduser(path).lstrip("/")))
        if target != self.workspace and not target.startswith(self.workspace + os.sep):
            raise ValueError("acesso permitido somente ao workspace do Genus")
        return target

    def bash(self, command, timeout=15):
        if not self.allow_commands:
            return "Comandos do sistema estão desativados. Defina GENUS_ALLOW_SYSTEM_TOOLS=true para habilitá-los."
        try:
            argv = shlex.split(command)
            if not argv or argv[0] not in self.allowed_commands:
                return "Comando bloqueado pela allowlist local."
            result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, cwd=self.workspace, check=False)
            output = (result.stdout + result.stderr).strip()
            return output[:800] if output else "(sem output)"
        except (OSError, ValueError) as error:
            return f"Erro: {error}"
        except subprocess.TimeoutExpired:
            return "Timeout."

    def read(self, path):
        try:
            with open(self._workspace_path(path), encoding="utf-8", errors="replace") as file:
                return file.read(4000)
        except (OSError, ValueError) as error:
            return f"Erro: {error}"

    def write(self, path, content):
        try:
            target = self._workspace_path(path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as file:
                file.write(content)
            return f"Salvo no workspace: {os.path.relpath(target, self.workspace)}"
        except (OSError, ValueError) as error:
            return f"Erro: {error}"

    def ls(self, path="."):
        try:
            return "  ".join(sorted(os.listdir(self._workspace_path(path)))[:50])
        except (OSError, ValueError) as error:
            return f"Erro: {error}"

    @staticmethod
    def web(query, n=3):
        try:
            request = urllib.request.Request(f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}", headers={"User-Agent": "Genus-AI/12"})
            with urllib.request.urlopen(request, timeout=8) as response:
                body = response.read().decode("utf-8", errors="replace")
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', body, re.DOTALL)
            titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', body, re.DOTALL)
            return "\n".join(f"{html.unescape(re.sub(r'<[^>]+>', '', title).strip())}: {html.unescape(re.sub(r'<[^>]+>', '', snippet).strip())}" for title, snippet in zip(titles[:n], snippets[:n])) or "Sem resultados."
        except OSError as error:
            return f"Erro: {error}"

    @staticmethod
    def open_url(url):
        parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return "URL inválida."
        webbrowser.open(parsed.geturl())
        return f"Abrindo {parsed.geturl()}"
