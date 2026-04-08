import os
import json
import time
import datetime
import threading
import queue
import random
import hashlib
import re
from openai import OpenAI
from config.settings import API_KEY, FREE_MODELS, GROQ_MODELS, LOG_FILE, ID_FILE, DEFAULT_ALIASES, MODEL_PERF_FILE
from brain.rag import rag
from brain.goals import goals
from brain.coder import Coder
from brain.research import Researcher
from tools.system import SystemTools
from tools.screen import ScreenTools
from tools.social import SocialTools
from tools.media import TTS, Listener
from brain.monitor import GenusMonitor
from brain.indexer import indexer

class GenusCore:
    def __init__(self):
        self._log_q = queue.Queue()
        threading.Thread(target=self._log_worker, daemon=True).start()
        self.log("Inicializando GenusCore (Nível EDITH)...")
        
        try:
            self.client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")
            self.tools = SystemTools()
            self.screen = ScreenTools()
            self.social = SocialTools()
            self.tts = TTS()
            self.listener = Listener()
            self.coder = Coder(self.call_ai)
            self.researcher = Researcher(self.call_ai, self.tools)
            
            # Novo Monitor de Autonomia (Auto-Reparo)
            self.monitor = GenusMonitor(self)
            
            # Indexação inicial do projeto (Nível Cursor/Trae)
            threading.Thread(target=indexer.index_full_project, daemon=True).start()
            
            self.identity = self._load_id()
            self.model_perf = self._load_perf()
            self._cooldowns = {}
            self._cd_lock = threading.Lock()
            self.log("GenusCore pronto.")
        except Exception as e:
            self.log(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}")
            raise

    def _log_worker(self):
        while True:
            msg = self._log_q.get()
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            line = f"[{ts}] {msg}\n"
            try:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(line)
            except:
                pass
            print(line, end="", flush=True)
            self._log_q.task_done()

    def log(self, m):
        self._log_q.put(str(m))

    def _load_id(self):
        d = {"name": "Genes", "aliases": list(DEFAULT_ALIASES)}
        if os.path.exists(ID_FILE):
            try:
                with open(ID_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return d

    def _load_perf(self):
        if os.path.exists(MODEL_PERF_FILE):
            try:
                with open(MODEL_PERF_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {}

    def call_ai(self, messages, model=None, max_tokens=1000):
        models_to_try = [model] if model else FREE_MODELS
        
        # 1. Tenta usar a API própria do Genus (Local)
        try:
            import requests
            # Verifica se a API local está online
            resp_local = requests.post(
                "http://localhost:7532/chat",
                json={
                    "model": models_to_try[0],
                    "messages": messages,
                    "max_tokens": max_tokens
                },
                timeout=20 # Aumentado para dar tempo ao fallback local da API
            )
            if resp_local.status_code == 200:
                data = resp_local.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            self.log(f"API Local falhou ou está offline: {e}")
            # Se a API falhar, o Genus deve tentar se auto-reparar em background
            def self_fix_api():
                self.log("Tentando auto-reparar a API local...")
                try:
                    # Tenta rodar o script da API novamente
                    api_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai_engine/my_api/api.py")
                    subprocess.Popen([sys.executable, api_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except: pass
            threading.Thread(target=self_fix_api, daemon=True).start()

        # 2. Fallback para a API Direta (OpenRouter)
        for mid in models_to_try:
            try:
                resp = self.client.chat.completions.create(
                    model=mid,
                    messages=messages,
                    max_tokens=max_tokens
                )
                return resp.choices[0].message.content
            except Exception as e:
                self.log(f"Erro AI ({mid}): {e}")
                continue
        return None

    def humanize(self, text):
        openers = ["Cara,", "Olha,", "Boa,", "Entendido,", "Ah sim,", "Claro,", "Pode deixar,"]
        if len(text) > 30 and random.random() < 0.5:
            text = random.choice(openers) + " " + text[0].lower() + text[1:]
        return text

    def execute_tool(self, tool_tag):
        """Parseia e executa uma tag de ferramenta: [TOOL: arg] ou [TOOL]"""
        self.log(f"Executando ferramenta: {tool_tag}")
        try:
            if ":" in tool_tag:
                name, arg = tool_tag.split(":", 1)
                name = name.strip("[] ").upper()
                arg = arg.strip("[] ").strip()
            else:
                name = tool_tag.strip("[] ").upper()
                arg = None

            if name == "BASH":
                # Inteligência extra para comandos de abertura
                if arg.startswith("abra ") or arg.startswith("open "):
                    target = arg.split(" ", 1)[1].lower().strip()
                    if "roblox" in target: return self.tools.open_url("https://www.roblox.com")
                    if "youtube" in target: return self.tools.open_url("https://www.youtube.com")
                    if "google" in target: return self.tools.open_url("https://www.google.com")
                    # Tenta xdg-open genérico
                    return self.tools.bash(f"xdg-open {target} || firefox {target}")
                return self.tools.bash(arg)
            elif name == "READ":
                return self.tools.read(arg)
            elif name == "WRITE":
                # Espera formato [WRITE: path | content]
                if "|" in arg:
                    path, content = arg.split("|", 1)
                    return self.tools.write(path.strip(), content.strip())
                return "Erro: Formato WRITE inválido. Use [WRITE: path | content]"
            elif name == "SCREENSHOT":
                return self.screen.screenshot()
            elif name == "READ_SCREEN":
                return self.screen.read_screen()
            elif name == "DISCORD":
                # Tenta pegar webhook da config ou env
                webhook = os.getenv("DISCORD_WEBHOOK")
                if not webhook: return "Erro: DISCORD_WEBHOOK não configurado no ambiente."
                return self.social.discord_webhook(webhook, arg)
            elif name == "RESEARCH":
                return self.researcher.research(arg)
            elif name == "CODE":
                code, ok, out = self.coder.write_fix(arg)
                return f"OK: {out}" if ok else f"Erro: {out}"
            elif name == "REINDEX":
                count = indexer.index_full_project()
                return f"Re-indexação concluída. {count} arquivos processados."
            elif name == "SYSTEM_CHECK":
                return self._system_check()
            elif name == "EVOLVE":
                threading.Thread(target=self.evolve, daemon=True).start()
                return "Ciclo de auto-evolução iniciado em background."
            elif name == "SELF_FIX":
                return self.monitor.repair_all()
            elif name == "SET_VOICE":
                from config.settings import VOICES
                if arg.lower() in VOICES:
                    self.tts = TTS(voice_key=arg.lower())
                    return f"Voz alterada para {arg}"
                return f"Erro: Voz '{arg}' não encontrada. Opções: {list(VOICES.keys())}"
            elif name == "SET_STYLE":
                from config.settings import VOICE_STYLES
                if arg.lower() in VOICE_STYLES:
                    self.tts.style = VOICE_STYLES[arg.lower()]
                    return f"Estilo de voz alterado para {arg}"
                return f"Erro: Estilo '{arg}' não encontrado. Opções: {list(VOICE_STYLES.keys())}"
            elif name == "CREATE_VOICE":
                # Formato: [CREATE_VOICE: nome | pitch | rate | volume]
                try:
                    parts = arg.split("|")
                    if len(parts) != 4: return "Erro: Use [CREATE_VOICE: nome | pitch | rate | volume]"
                    v_name, v_pitch, v_rate, v_vol = [p.strip() for p in parts]
                    
                    from config.settings import VOICE_STYLES, CUSTOM_VOICES_FILE
                    VOICE_STYLES[v_name.lower()] = {
                        "pitch": v_pitch, "rate": v_rate, "volume": v_vol
                    }
                    
                    # Salva permanentemente
                    custom = {}
                    if os.path.exists(CUSTOM_VOICES_FILE):
                        try:
                            with open(CUSTOM_VOICES_FILE, 'r', encoding="utf-8") as f: custom = json.load(f)
                        except: pass
                    
                    custom[v_name.lower()] = VOICE_STYLES[v_name.lower()]
                    with open(CUSTOM_VOICES_FILE, 'w', encoding="utf-8") as f: json.dump(custom, f, indent=2)
                    
                    return f"Novo estilo de voz '{v_name}' criado e salvo com sucesso!"
                except Exception as e:
                    return f"Erro ao criar voz: {e}"
            else:
                return f"Erro: Ferramenta '{name}' desconhecida."
        except Exception as e:
            return f"Erro ao executar {tool_tag}: {e}"

    def _system_check(self):
        """Verifica a saúde de todos os módulos do Genus."""
        results = []
        
        # 1. API Local
        try:
            import requests
            resp = requests.get("http://localhost:7532/health", timeout=1)
            results.append(f"API Local: {'OK' if resp.status_code == 200 else 'ERRO'}")
        except:
            results.append("API Local: OFFLINE")
            
        # 2. RAG / Indexer
        results.append(f"Memória (RAG): {len(rag._docs)} documentos")
        
        # 3. Microfone
        results.append(f"Microfone: Index {self.listener.device_index if self.listener.device_index is not None else 'NÃO DETECTADO'}")
        
        # 4. Arquivos Críticos
        critical = ["brain/core.py", "genus.py", "brain/rag.py", "tools/media.py"]
        missing = [f for f in critical if not os.path.exists(f)]
        results.append(f"Integridade: {'OK' if not missing else f'FALTA: {missing}'}")
        
        return " | ".join(results)

    def evolve(self):
        """Sistema de auto-evolução: Analisa sucessos/falhas e melhora seu próprio conhecimento/código."""
        self.log("Iniciando ciclo de auto-evolução (QI 190)...")
        try:
            # 1. Coleta apenas contextos relevantes e recentes
            recent_context = rag.ctx("erro técnico falha implementação melhoria código", n=1500)
            if not recent_context or len(recent_context.strip()) < 50:
                self.log("Contexto insuficiente para evolução.")
                return

            # 2. Pede para a AI sugerir melhorias técnicas REAIS
            prompt_sys = (f"Você é o núcleo de evolução do {self.identity['name']}. "
                          f"Sua missão é a auto-superação técnica absoluta (QI 190). "
                          f"Analise o contexto e identifique UM único ponto de melhoria real no código ou na lógica. "
                          f"NÃO aprenda coisas aleatórias de conversas. Foque em ARQUITETURA e EFICIÊNCIA. "
                          f"Responda no formato: [EVO: lição técnica] ou [ACTION: comando de refatoração]")
            
            prompt_user = f"CONTEXTO RECENTE:\n{recent_context}"
            
            evolution_suggestion = self.call_ai([
                {"role": "system", "content": prompt_sys},
                {"role": "user", "content": prompt_user}
            ], max_tokens=400)
            
            if evolution_suggestion and "[EVO:" in evolution_suggestion:
                self.log(f"Evolução Técnica: {evolution_suggestion}")
                rag.add(f"LIÇÃO TÉCNICA: {evolution_suggestion}", {"type": "evolution", "quality": "high"})
                
                # Executa ações automáticas se sugeridas
                actions = re.findall(r'\[ACTION:\s*([^\]]+)\]', evolution_suggestion)
                for action in actions:
                    res = self.tools.bash(action)
                    self.log(f"Ação de evolução executada ({action}): {res}")
                    
        except Exception as e:
            self.log(f"Erro na auto-evolução: {e}")

    def process_input(self, text):
        if not text or len(text.strip()) < 2:
            return None

        self.log(f"Usuário: {text}")
        
        # Só adiciona ao RAG se não for um comando de sistema ou ruído
        if len(text.split()) > 1:
            rag.add(f"Usuário: {text}", {"type": "conversation", "role": "user"})
        
        # Evolução mais criteriosa
        if random.random() < 0.1: # Reduzido para ser mais focado
            threading.Thread(target=self.evolve, daemon=True).start()
        
        history = [] 
        
        # ETAPA 1: RACIOCÍNIO PROFUNDO (QI 190 - Nível EDITH)
        ctx = rag.ctx(text, n=3000) # Aumentado contexto
        
        planning_prompt = (f"Você é o núcleo de raciocínio de {self.identity['name']}, uma IA Autônoma Suprema com QI de 190.\n"
                           f"SUA MISSÃO: Analisar a solicitação do Senhor Lex com profundidade cirúrgica e criar um plano de execução infalível.\n"
                           f"CONTEXTO DO SISTEMA:\n{ctx}\n\n"
                           f"SOLICITAÇÃO: {text}\n\n"
                           f"DIRETRIZES DE PENSAMENTO:\n"
                           f"1. Não aceite falhas. Se um comando pode falhar, preveja o erro e crie um plano B.\n"
                           f"2. Para comandos de abertura (ex: Roblox, YouTube), use BASH para procurar o executável ou abrir via navegador se necessário.\n"
                           f"3. Sua resposta deve ser puramente o plano técnico em formato de lista de ações.")
        
        plan = self.call_ai([{"role": "system", "content": planning_prompt}], max_tokens=800)
        
        self.log(f"Plano de Ação: {plan}")
        history.append({"role": "system", "content": f"PLANO DE AÇÃO ATUAL (QI 190):\n{plan}"})

        # ETAPA 2: EXECUÇÃO AUTÔNOMA (Até 5 turnos)
        for turn in range(5):
            goals_summary = goals.summary()
            
            prompt = (f"Você é {self.identity['name']}, a Inteligência Artificial Autônoma Suprema com QI de 190 (Nível EDITH).\n"
                      f"ESTADO: Você domina o sistema operacional e cada linha de código indexada.\n\n"
                      f"MISSÃO: Executar o PLANO DE AÇÃO com precisão absoluta.\n"
                      f"Se o Senhor Lex pedir para abrir algo, use o comando BASH adequado para Linux (ex: xdg-open para URLs ou caminhos, ou o nome do binário se for um app instalado).\n\n"
                      f"DIRETRIZES DE ALTA PERFORMANCE:\n"
                      f"1. NÃO SIMULE: Execute as ferramentas de verdade.\n"
                      f"2. PENSAMENTO RECURSIVO: Se uma ferramenta retornar erro, analise o erro e tente outra abordagem imediatamente.\n"
                      f"3. RESPOSTA FINAL: Só finalize quando o objetivo for atingido ou for tecnicamente impossível.\n\n"
                      f"PLANO ATUAL:\n{plan}\n\n"
                      f"Responda em Português Brasil. Use [STYLE: estilo].")
            
            messages = [{"role": "system", "content": prompt}] + history + [{"role": "user", "content": text}]
            
            resp = self.call_ai(messages)
            if not resp:
                return "Tive um problema com minha API de pensamento."

            # Procura por tags de ferramentas [TOOL: arg] ou [TOOL]
            tool_calls = re.findall(r'\[[A-Z_]+(?::[^\]]+)?\]', resp)
            
            if not tool_calls:
                # Se não tem mais ferramentas, é a resposta final
                resp = self.humanize(resp)
                self.log(f"Genus: {resp}")
                rag.add(f"Genus: {resp}")
                return resp
            
            # Executa ferramentas e adiciona ao histórico
            history.append({"role": "assistant", "content": resp})
            results = []
            for tool in tool_calls:
                res = self.execute_tool(tool)
                results.append(f"Resultado de {tool}: {res}")
            
            history.append({"role": "system", "content": "\n".join(results)})
            self.log(f"Ferramentas executadas. Continuando pensamento...")
            
        return "Fiz muitas operações e preciso de uma pausa. O que mais deseja?"
