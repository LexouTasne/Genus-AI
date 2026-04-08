import os
import sys
import subprocess
import time
import re
from config.settings import WORK_DIR

class Coder:
    MAX_RETRY = 4
    
    def __init__(self, call_fn):
        self._call = call_fn

    def run(self, code, timeout=30, filename=None):
        fname = filename or f"tmp_{int(time.time()*1000)}.py"
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            return "", f"SyntaxError:{e.lineno}:{e.msg}", False
            
        tf = os.path.join(WORK_DIR, fname)
        try:
            with open(tf, "w", encoding="utf-8") as f:
                f.write(code)
            r = subprocess.run([sys.executable, tf], capture_output=True, text=True, timeout=timeout, cwd=WORK_DIR)
            out = r.stdout.strip()
            err = r.stderr.strip()
            return out, err, r.returncode == 0
        except subprocess.TimeoutExpired:
            return "", "timeout", False
        except Exception as e:
            return "", str(e), False
        finally:
            if not filename:
                try:
                    os.unlink(tf)
                except:
                    pass

    def write_fix(self, task, save_as=None):
        prompt = (f"Python 3 COMPLETO para: {task}\n"
                f"Só stdlib+pip, roda Ubuntu sem sudo\n"
                f"print() final confirmando sucesso\n"
                f"APENAS código puro sem markdown sem ```")
        code = self._call([{"role": "user", "content": prompt}], max_tokens=1500)
        if not code:
            return "", False, "IA indisponível"
            
        code = re.sub(r'^```python\s*\n?', '', code.strip())
        code = re.sub(r'\n?```\s*$', '', code).strip()
        
        last_err = ""
        for att in range(self.MAX_RETRY):
            out, err, ok = self.run(code, filename=save_as)
            if ok:
                if save_as:
                    dest = save_as if save_as.startswith("/") else os.path.join(WORK_DIR, save_as)
                    with open(dest, "w", encoding="utf-8") as f:
                        f.write(code)
                return code, True, out
            last_err = err
            fix = self._call([{"role": "user", "content": f"Corrija este Python:\n{code}\nErro:{err[:300]}\nRetorne APENAS código corrigido sem markdown."}], max_tokens=1500)
            if not fix:
                break
            code = re.sub(r'^```python\s*\n?', '', fix.strip())
            code = re.sub(r'\n?```\s*$', '', code).strip()
        return code, False, last_err
