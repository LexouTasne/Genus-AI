"""Configuração do Genus; segredos ficam exclusivamente no ambiente."""
import os


def env_flag(name, default=False):
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


CREATOR = os.getenv("GENUS_CREATOR", "Senhor Lex")
DEFAULT_ALIASES = ["genus", "genes", "genesis", "jenes", "jenis", "genis", "gênus", "gênesis", "gênes", "genius"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM_DIR = os.path.join(BASE_DIR, "memory")
CACHE_DIR = os.path.join(MEM_DIR, "tts_cache")
AI_DIR = os.path.join(BASE_DIR, "ai_engine")
WORK_DIR = os.path.join(AI_DIR, "workspace")
API_DIR = os.path.join(AI_DIR, "my_api")
for _directory in (MEM_DIR, CACHE_DIR, AI_DIR, WORK_DIR, API_DIR):
    os.makedirs(_directory, exist_ok=True)

# Nunca coloque chaves neste arquivo. A chave exposta em commits anteriores deve
# ser revogada no provedor.
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LOCAL_API_TOKEN = os.getenv("GENUS_LOCAL_API_TOKEN", "")
LOCAL_API_HOST = os.getenv("GENUS_LOCAL_API_HOST", "127.0.0.1")
LOCAL_API_PORT = int(os.getenv("GENUS_LOCAL_API_PORT", "7532"))

# Capacidades perigosas são opt-in, mesmo quando o modelo pede para executá-las.
ALLOW_SYSTEM_TOOLS = env_flag("GENUS_ALLOW_SYSTEM_TOOLS")
ALLOW_CODE_EXECUTION = env_flag("GENUS_ALLOW_CODE_EXECUTION")
AUTONOMY_ENABLED = env_flag("GENUS_ENABLE_AUTONOMY")
ALLOWED_COMMANDS = frozenset(item.strip() for item in os.getenv("GENUS_ALLOWED_COMMANDS", "pwd,ls,date,whoami").split(",") if item.strip())

FREE_MODELS = [
    "anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001", "openai/gpt-4o-mini",
    "meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-chat", "qwen/qwen-2.5-72b-instruct",
]
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it", "mixtral-8x7b-32768"]
VOICES = {"antonio": "pt-BR-AntonioNeural", "francisca": "pt-BR-FranciscaNeural", "thalita": "pt-BR-ThalitaMultilingualNeural", "giovanna": "pt-BR-GiovannaNeural", "donato": "pt-BR-DonatoNeural", "leila": "pt-BR-LeilaNeural", "yaritza": "pt-BR-YaritzaNeural", "adriana": "pt-BR-AdrianaNeural"}
VOICE_STYLES = {"normal": {"pitch": "+0Hz", "rate": "+5%", "volume": "+0%"}, "angry": {"pitch": "-5Hz", "rate": "+35%", "volume": "+25%"}, "happy": {"pitch": "+12Hz", "rate": "+20%", "volume": "+10%"}, "sad": {"pitch": "-12Hz", "rate": "-20%", "volume": "-15%"}, "serious": {"pitch": "-3Hz", "rate": "+0%", "volume": "+15%"}}
CUSTOM_VOICES_FILE = os.path.join(MEM_DIR, "custom_voices.json")
if os.path.exists(CUSTOM_VOICES_FILE):
    try:
        import json
        with open(CUSTOM_VOICES_FILE, encoding="utf-8") as file:
            VOICE_STYLES.update(json.load(file))
    except (OSError, ValueError):
        pass

LOG_FILE = os.path.join(BASE_DIR, "genus.log")
CFG_FILE = os.path.join(MEM_DIR, "config.json")
CONV_FILE = os.path.join(MEM_DIR, "conversation.jsonl")
STATS_FILE = os.path.join(MEM_DIR, "stats.json")
EVO_FILE = os.path.join(MEM_DIR, "evolution.json")
LEARN_FILE = os.path.join(MEM_DIR, "learned.json")
ID_FILE = os.path.join(MEM_DIR, "identity.json")
GOALS_FILE = os.path.join(MEM_DIR, "goals.json")
RAG_FILE = os.path.join(MEM_DIR, "rag_index.json")
MODEL_PERF_FILE = os.path.join(MEM_DIR, "model_perf.json")
RESP_CACHE_FILE = os.path.join(MEM_DIR, "resp_cache.json")
