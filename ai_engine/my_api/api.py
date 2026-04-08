from flask import Flask, request, jsonify
import os
import json
import requests
import sys

# Adiciona o diretório base ao sys.path para importar configurações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import API_KEY, FREE_MODELS

import logging
import random
from brain.rag import rag

# Configuração de Logs da API
LOG_API_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "api_debug.log")
logging.basicConfig(filename=LOG_API_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Genus API está online"}), 200

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'messages' not in data:
        logging.error("Requisição inválida: mensagens ausentes")
        return jsonify({"error": "Mensagens não fornecidas"}), 400
    
    messages = data.get('messages')
    user_query = ""
    for m in reversed(messages):
        if m['role'] == 'user':
            user_query = m['content']
            break

    # Tenta usar os modelos configurados em ordem se um falhar
    models_to_try = [data.get('model')] if data.get('model') else FREE_MODELS
    max_tokens = data.get('max_tokens', 1000)
    
    # RAPID LOCAL CHECK: Removido para priorizar inteligência real
    
    last_error = ""
    for model in models_to_try:
        try:
            logging.info(f"Tentando modelo: {model}")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://genus.ai", # Opcional para OpenRouter
                    "X-Title": "Genus AI"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens
                },
                timeout=15 # Reduzido para fallback mais rápido
            )
            if response.status_code == 200:
                logging.info(f"Sucesso com modelo: {model}")
                return jsonify(response.json()), 200
            else:
                last_error = f"Erro {response.status_code}: {response.text}"
                logging.warning(f"Falha com {model}: {last_error}")
        except Exception as e:
            last_error = str(e)
            logging.error(f"Exceção com {model}: {last_error}")
            continue

    # FALLBACK: CÉREBRO LOCAL (Nível EDITH Local)
    logging.info("Fallback para Cérebro Local Inteligente ativado.")
    local_context = rag.ctx(user_query, n=1500)
    
    # Processamento de comandos básicos locais (Sem IA externa)
    query_low = user_query.lower()
    if any(k in query_low for k in ["abra", "abrir", "youtube", "roblox", "firefox"]):
        # Tenta extrair o que abrir
        target = "site ou aplicativo"
        if "youtube" in query_low: target = "YouTube"
        elif "roblox" in query_low: target = "Roblox"
        elif "firefox" in query_low: target = "Firefox"
        answer = f"[STYLE: sério] Minha conexão externa falhou, mas como sou uma IA autônoma, vou tentar executar o comando '{user_query}' via BASH local agora mesmo. [BASH: xdg-open https://www.{target.lower()}.com]"
    elif "quem é você" in query_low or "quem e voce" in query_low:
        answer = "Eu sou Genus, sua IA Autônoma Suprema. No momento estou operando com meu núcleo local (Protocolo EDITH) devido a falhas na rede externa."
    elif local_context:
        # Tenta resumir ou extrair a parte mais relevante em vez de apenas dar o dump
        relevant_lines = [line for line in local_context.split("\n") if len(line.strip()) > 20][:3]
        summary = " ".join(relevant_lines)
        answer = f"Estou operando em modo local. Sobre o que você perguntou, lembro disso: {summary}. Como posso agir nos arquivos do projeto?"
    else:
        answer = "Minha conexão com os modelos externos falhou e não encontrei contexto local suficiente. Posso realizar tarefas de sistema ou leitura de arquivos por conta própria."

    return jsonify({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": answer
            }
        }],
        "model": "genus-local-brain",
        "usage": {"total_tokens": 0}
    }), 200

if __name__ == '__main__':
    # Porta padrão do Genus
    app.run(host='0.0.0.0', port=7532, debug=False)
