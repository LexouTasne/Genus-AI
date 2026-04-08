import os
import re
import time
import json
import hashlib
import tempfile
import shutil
import threading
import asyncio
import struct
import math
import pygame
import edge_tts
import speech_recognition as sr
from config.settings import CACHE_DIR, VOICES, VOICE_STYLES

class TTS:
    PAUSE_DOT   = 0.38
    PAUSE_COMMA = 0.18

    def __init__(self, voice_key="antonio", style="normal"):
        self.voice = VOICES.get(voice_key, VOICES["antonio"])
        self.style = VOICE_STYLES.get(style, VOICE_STYLES["normal"])
        self._cache = {}
        self._lock = threading.Lock()

    def _sentences(self, text):
        # Remove tags de estilo [STYLE: angry] antes de processar frases
        text = re.sub(r'\[STYLE:[^\]]+\]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        parts = re.split(r'(?<=[.!?…])\s+', text)
        out = []
        buf = ""
        for p in parts:
            buf = (buf + " " + p).strip() if buf else p
            wc = len(buf.split())
            if wc >= 6 or (wc >= 3 and buf[-1] in ".!?…"):
                out.append(buf)
                buf = ""
        if buf:
            out.append(buf)
        return out or [text]

    def _audio(self, text, style_cfg=None):
        style_cfg = style_cfg or self.style
        # Gera chave de cache baseada no texto e nos parâmetros de voz/estilo
        style_str = json.dumps(style_cfg, sort_keys=True)
        key = hashlib.md5(f"{self.voice}::{style_str}::{text}".encode()).hexdigest()[:14]
        
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        
        path = os.path.join(CACHE_DIR, key + ".mp3")
        if os.path.exists(path):
            with self._lock:
                self._cache[key] = path
            return path
            
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()
            
            # Parâmetros de prosódia
            pitch = style_cfg.get("pitch", "+0Hz")
            rate = style_cfg.get("rate", "+0%")
            volume = style_cfg.get("volume", "+0%")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            communicate = edge_tts.Communicate(text, self.voice, pitch=pitch, rate=rate, volume=volume)
            loop.run_until_complete(communicate.save(tmp.name))
            loop.close()
            
            if len(text) < 200:
                shutil.copy2(tmp.name, path)
                os.unlink(tmp.name)
                final = path
            else:
                final = tmp.name
                
            with self._lock:
                self._cache[key] = final
            return final
        except Exception as e:
            return None

    def speak(self, text, stop_fn):
        # Detecta mudança de estilo dinâmica na resposta [STYLE: angry]
        current_style = self.style
        style_match = re.search(r'\[STYLE:(\w+)\]', text)
        if style_match:
            style_name = style_match.group(1).lower()
            if style_name in VOICE_STYLES:
                current_style = VOICE_STYLES[style_name]
        
        clean = self._clean(text)
        sents = self._sentences(clean)
        for i, sent in enumerate(sents):
            if stop_fn():
                return False
            path = self._audio(sent, style_cfg=current_style)
            if not path:
                continue
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                clk = pygame.time.Clock()
                while pygame.mixer.music.get_busy():
                    clk.tick(30)
                    if stop_fn():
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                        return False
                pygame.mixer.music.unload()
                if sent and sent[-1] in ".!?…":
                    time.sleep(self.PAUSE_DOT)
                elif sent and sent[-1] == ",":
                    time.sleep(self.PAUSE_COMMA)
            except:
                pass
        return True

    @staticmethod
    def _clean(t):
        t = re.sub(r'\[TOOL:[^\]]+\][^\n]*\n?', '', t)
        t = re.sub(r'```[\s\S]*?```', '', t)
        t = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', t)
        t = re.sub(r'`(.*?)`', r'\1', t)
        t = re.sub(r'^\s*[-*#\d.]\s+', '', t, flags=re.MULTILINE)
        t = re.sub(r'#{1,6}\s+', '', t)
        t = re.sub(r'\n{2,}', '. ', t)
        t = re.sub(r'\n', ' ', t)
        return re.sub(r'\s+', ' ', t).strip()

class VAD:
    @staticmethod
    def analyze(raw):
        n = len(raw) // 2
        if n == 0:
            return {"rms": 0, "zcr": 0, "voiced": False}
        s = struct.unpack(f"<{n}h", raw[:n*2])
        rms = math.sqrt(sum(x*x for x in s) / n)
        zcr = sum(1 for i in range(1, n) if (s[i] >= 0) != (s[i-1] >= 0)) / n
        voiced = (0.02 <= zcr <= 0.42 and rms > 120 and not (rms > 3000 and zcr > 0.45))
        return {"rms": rms, "zcr": zcr, "voiced": voiced}

    @classmethod
    def is_speech(cls, chunks):
        if not chunks:
            return False
        a = [cls.analyze(c) for c in chunks]
        nv = sum(1 for x in a if x["voiced"])
        if nv < 8 or nv / len(a) < 0.28:
            return False
        rv = [x["rms"] for x in a]
        peak = max(rv)
        if peak > 1500:
            pi = rv.index(peak)
            nb = rv[max(0, pi-2):pi+3]
            if sum(1 for r in nb if r > peak * 0.35) <= 2:
                return False
        return True

class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Nível Sensível: Limiar inicial equilibrado
        self.recognizer.energy_threshold = 200 
        self.recognizer.dynamic_energy_threshold = True 
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.5 
        self.recognizer.non_speaking_duration = 0.2
        self.device_index = self._get_mic_index()
        self._calibrated = False

    def _get_mic_index(self):
        try:
            from config.settings import MIC_DEVICE
            import speech_recognition as sr
            import pyaudio
            
            p = pyaudio.PyAudio()
            mics = []
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels') > 0:
                    mics.append((i, info.get('name')))
            p.terminate()
            
            # 1. Tenta o dispositivo configurado (GM7)
            for i, name in mics:
                if "GM7" in name or "USB Audio" in name:
                    print(f"[Listener] Microfone USB GM7 detectado no Index {i}")
                    return i
            
            # 2. Tenta "pulse" ou "default" como fallback
            for i, name in mics:
                if "pulse" in name.lower() or "default" in name.lower():
                    print(f"[Listener] Usando fallback: {name} (Index {i})")
                    return i
            
            return None 
        except Exception as e:
            print(f"[Listener] Erro ao buscar microfones: {e}")
        return None

    def listen(self, timeout=3, phrase_time_limit=10):
        """Escuta o microfone e retorna o texto reconhecido (Otimizado)."""
        import os
        import sys

        # Redireciona stderr para /dev/null em nível de sistema (Solução Nuclear)
        stderr_fd = sys.stderr.fileno()
        null_fd = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(stderr_fd)
        os.dup2(null_fd, stderr_fd)

        try:
            import speech_recognition as sr
            try:
                import pyaudio
            except ImportError:
                return None
                
            with sr.Microphone(device_index=self.device_index) as source:
                # Calibração rápida apenas se necessário
                if not self._calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.15)
                    self._calibrated = True
                
                # Garante que o threshold não fique absurdamente alto (evita "surdez")
                if self.recognizer.energy_threshold > 800:
                    self.recognizer.energy_threshold = 500
                elif self.recognizer.energy_threshold < 50:
                    self.recognizer.energy_threshold = 150
                
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                # Restaura stderr logo após a escuta
                os.dup2(old_stderr, stderr_fd)
                os.close(null_fd)
                os.close(old_stderr)
                
                try:
                    # Tenta Google (melhor qualidade)
                    text = self.recognizer.recognize_google(audio, language="pt-BR")
                    if text:
                        # Normalização Fonética Extrema (Melhorada para QI 190)
                        words = text.split()
                        normalized = []
                        genus_phonetics = [
                            "genus", "jesus", "jogos", "gemeos", "janius", "jenos", "janice", "genes", 
                            "jenis", "genis", "gênus", "gênesis", "gênes", "genius", "genios", "genios",
                            "jênus", "jênios", "jênes", "gêmeos", "gêmeo", "gêmeas", "gêmea",
                            "venus", "vênus", "denis", "dênis", "janis", "janice", "jênice",
                            "genus.", "genus!", "genus?", "genus,", "jesus.", "jesus!", "jesus?", "jesus,",
                            "genes.", "genes!", "genes?", "genes,"
                        ]
                        oi_phonetics = ["oi", "ou", "olá", "hoje", "ei", "ow", "ei!", "oi!", "ey"]
                        
                        for word in words:
                            w_low = word.lower().strip(".,!?")
                            if w_low in genus_phonetics: normalized.append("Genus")
                            elif w_low in oi_phonetics: normalized.append("Oi")
                            else: normalized.append(word)
                        
                        text = " ".join(normalized)
                        print(f"[Ouvido] {text} (Energia: {self.recognizer.energy_threshold:.1f})")
                    return text.strip()
                except sr.RequestError: return None
                except sr.UnknownValueError: return ""
        except Exception as e:
            # Garante restauração do stderr em caso de erro
            try:
                os.dup2(old_stderr, stderr_fd)
                os.close(null_fd)
                os.close(old_stderr)
            except: pass
            return None
