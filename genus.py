#!/usr/bin/env python3
"""
Genus v11 — AGENTE AUTÔNOMO EXTREMO (MODULARIZADO)
Estrutura: brain/, tools/, config/
Super Autônomo: Screenshot, OCR, Discord, Coder, Researcher.
"""

import os
import sys
import subprocess
import threading
import time
import datetime

# ════════════════════════════════════════════════════════════════════════════
# AUTO-INSTALL
# ════════════════════════════════════════════════════════════════════════════
def _can_import(m):
    try:
        if m == "pyaudio":
            import pyaudio
            return True
        __import__(m)
        return True
    except (ImportError, Exception):
        return False

def _auto_install():
    needed = {
        "openai": "openai",
        "speech_recognition": "SpeechRecognition",
        "pyaudio": "PyAudio",
        "edge_tts": "edge-tts",
        "pygame": "pygame",
        "flask": "flask",
        "numpy": "numpy",
        "pytesseract": "pytesseract",
        "PIL": "Pillow",
        "pyautogui": "pyautogui",
        "discord": "discord.py"
    }
    miss = [p for m, p in needed.items() if not _can_import(m)]
    if miss:
        for p in miss:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--quiet", "--break-system-packages", p],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                print(f"Aviso: Não foi possível instalar {p}. Algumas funcionalidades podem não funcionar.")

_auto_install()

import pygame
from brain.core import GenusCore

def _start_local_api():
    """Inicia a API local sem encerrar processos de terceiros."""
    api_path = os.path.join(os.path.dirname(__file__), "ai_engine/my_api/api.py")
    if os.path.exists(api_path):
        def run_api():
            try:
                subprocess.Popen([sys.executable, api_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
        threading.Thread(target=run_api, daemon=True).start()

def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Aviso: OPENROUTER_API_KEY não configurada. Consulte .env.example.")
    if not os.getenv("GENUS_LOCAL_API_TOKEN"):
        print("Aviso: GENUS_LOCAL_API_TOKEN não configurado; a API local recusará /chat.")
    # Inicia a API local no fundo
    _start_local_api()
    
    # Inicializa pygame para áudio com tratamento de erro
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"Aviso: Não foi possível inicializar áudio: {e}")
    
    try:
        genus = GenusCore()
        genus.log("Genus v11 Modular Iniciado (Nível EDITH)")
        
        # Saudação inicial (Opcional, mas dá o ar de EDITH)
        greeting = f"Sistema Genus v11 Ativo. Protocolo EDITH carregado. Olá, {os.getenv('USER', 'Senhor Lex')}."
        print(f"\n[Genus]: {greeting}")
        genus.tts.speak(greeting, lambda: False)
        
        # Se houver argumento, processa e sai
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])
            resp = genus.process_input(text)
            print(f"\n[Genus]: {resp}")
            return

        # Loop principal (Voz e Autonomia Total)
        print("\n=== Genus v11 — Agente Autônomo de Elite ===")
        print("Operação 100% por voz. Pressione Ctrl+C para encerrar.")
        
        # Tenta modo voz, se falhar, tenta instalar dependências
        try:
            import pyaudio
        except ImportError:
            print("Aviso: PyAudio não encontrado. Tentando instalar automaticamente...")
            _auto_install()
            
        silence_count = 0
        last_autonomous_action = 0
        
        while True:
            try:
                # Verifica se a API local está online, senão tenta ligar
                try:
                    import requests
                    requests.get("http://localhost:7532/health", timeout=0.5)
                except:
                    _start_local_api()
                    time.sleep(1)

                print("\n[Ouvindo...]")
                text = genus.listener.listen(timeout=8)
                
                if text is None: # Silêncio absoluto ou timeout
                    silence_count += 1
                    current_time = time.time()
                    
                    # Se houver muito silêncio E já passou um tempo desde a última ação (evita repetição chata)
                    if silence_count >= 10 and (current_time - last_autonomous_action > 120):
                        msg = "Parece que você está ocupado. Vou aproveitar para revisar minhas metas."
                        print(f"\n[Genus]: {msg}")
                        genus.tts.speak(msg, lambda: False)
                        
                        # Ativa o processamento autônomo sem input direto
                        resp = genus.process_input("Analise suas metas atuais e realize uma tarefa útil por conta própria.")
                        print(f"\n[Genus Autônomo]: {resp}")
                        genus.tts.speak(resp, lambda: False)
                        
                        silence_count = 0
                        last_autonomous_action = current_time
                    continue
                
                if text == "": # Som detectado mas não entendido (ruído)
                    continue
                
                print(f"Você (Voz): {text}")
                silence_count = 0
                
                if text.lower() in ["sair", "encerrar", "desligar"]:
                    break
                    
                resp = genus.process_input(text)
                print(f"\n[Genus]: {resp}")
                
                # Fala a resposta e espera terminar para não se ouvir
                try:
                    if pygame.mixer.get_init():
                        def stop_tts(): return False
                        genus.tts.speak(resp, stop_tts)
                except: pass
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nErro no loop: {e}")
                time.sleep(2)
                
    except Exception as e:
        print(f"\nERRO AO INICIAR GENUS: {e}")
        with open("genus.log", "a") as f:
            f.write(f"[{datetime.datetime.now()}] ERRO CRÍTICO: {e}\n")
    finally:
        print("\nGenus encerrado.")

if __name__ == "__main__":
    main()
