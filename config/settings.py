import os
import sys

# ── IDENTIDADE ──────────────────────────────────────────────────────────────
CREATOR    = "Senhor Lex"
DEFAULT_ALIASES = ["genus", "genes", "genesis", "jenes", "jenis", "genis", "gênus", "gênesis", "gênes", "genius"]

# ── DIRETÓRIOS ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM_DIR    = os.path.join(BASE_DIR, "memory")
CACHE_DIR  = os.path.join(MEM_DIR, "tts_cache")
AI_DIR     = os.path.join(BASE_DIR, "ai_engine")
WORK_DIR   = os.path.join(AI_DIR, "workspace")   # onde Genus cria código
API_DIR    = os.path.join(AI_DIR, "my_api")       # API própria do Genus

# Garantir que diretórios existem
for _d in (MEM_DIR, CACHE_DIR, AI_DIR, WORK_DIR, API_DIR):
    os.makedirs(_d, exist_ok=True)

# ── API E MODELOS ────────────────────────────────────────────────────────────
API_KEY    = "***REMOVED***"
FREE_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.0-flash-001",
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat",
    "qwen/qwen-2.5-72b-instruct",
    "google/gemini-2.0-pro-exp-02-05:free",
    "google/gemini-2.0-flash-exp:free",
]
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it", "mixtral-8x7b-32768"]

OLLAMA_MODEL = "genus-local"
OLLAMA_BASE_MDLS = ["tinyllama", "phi3:mini", "llama3.2:3b"]

# ── VOZ ─────────────────────────────────────────────────────────────────────
MIC_DEVICE = "" # Deixe vazio para usar o padrão do sistema

# Vozes Edge-TTS (Principais e Multilinguagem)
VOICES = {
    "antonio":   "pt-BR-AntonioNeural",
    "francisca": "pt-BR-FranciscaNeural",
    "thalita":   "pt-BR-ThalitaMultilingualNeural",
    "giovanna":  "pt-BR-GiovannaNeural",
    "donato":    "pt-BR-DonatoNeural",
    "leila":     "pt-BR-LeilaNeural",
    "yaritza":   "pt-BR-YaritzaNeural",
    "adriana":   "pt-BR-AdrianaNeural",
}

# Estilos de Voz (Simulados via Prosody)
VOICE_STYLES = {
    "normal":   {"pitch": "+0Hz",   "rate": "+5%",   "volume": "+0%"},
    "angry":    {"pitch": "-5Hz",   "rate": "+35%",  "volume": "+25%"},
    "happy":    {"pitch": "+12Hz",  "rate": "+20%",  "volume": "+10%"},
    "sad":      {"pitch": "-12Hz",  "rate": "-20%",  "volume": "-15%"},
    "serious":  {"pitch": "-3Hz",   "rate": "+0%",   "volume": "+15%"},
    "excited":  {"pitch": "+18Hz",  "rate": "+40%",  "volume": "+20%"},
    "whisper":  {"pitch": "+0Hz",   "rate": "-25%",  "volume": "-50%"},
    "heroic":   {"pitch": "-2Hz",   "rate": "+5%",   "volume": "+20%"},
}

# Carregar vozes customizadas se existirem
CUSTOM_VOICES_FILE = os.path.join(MEM_DIR, "custom_voices.json")
if os.path.exists(CUSTOM_VOICES_FILE):
    try:
        import json
        with open(CUSTOM_VOICES_FILE, 'r', encoding="utf-8") as f:
            VOICE_STYLES.update(json.load(f))
    except: pass

# ── ARQUIVOS ────────────────────────────────────────────────────────────────
LOG_FILE    = os.path.join(BASE_DIR,  "genus.log")
CFG_FILE    = os.path.join(MEM_DIR,   "config.json")
CONV_FILE   = os.path.join(MEM_DIR,   "conversation.jsonl")
STATS_FILE  = os.path.join(MEM_DIR,   "stats.json")
EVO_FILE    = os.path.join(MEM_DIR,   "evolution.json")
LEARN_FILE  = os.path.join(MEM_DIR,   "learned.json")
ID_FILE     = os.path.join(MEM_DIR,   "identity.json")
GOALS_FILE  = os.path.join(MEM_DIR,   "goals.json")
RAG_FILE    = os.path.join(MEM_DIR,   "rag_index.json")
APIS_FILE   = os.path.join(BASE_DIR,  "apis.txt")
MODEL_PERF_FILE = os.path.join(MEM_DIR, "model_perf.json")
RESP_CACHE_FILE = os.path.join(MEM_DIR, "resp_cache.json")
