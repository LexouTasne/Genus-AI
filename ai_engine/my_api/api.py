"""API local autenticada para o núcleo Genus."""
import hmac
import logging
import os
import sys

import requests
from flask import Flask, jsonify, request

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import API_KEY, FREE_MODELS, LOCAL_API_HOST, LOCAL_API_PORT, LOCAL_API_TOKEN

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@app.before_request
def require_local_token():
    if request.path == "/health":
        return None
    provided = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not LOCAL_API_TOKEN or not hmac.compare_digest(provided, LOCAL_API_TOKEN):
        return jsonify({"error": "unauthorized"}), 401
    return None


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages or len(messages) > 30:
        return jsonify({"error": "messages inválidas"}), 400
    if not API_KEY:
        return jsonify({"error": "OPENROUTER_API_KEY não configurada"}), 503
    max_tokens = data.get("max_tokens", 1000)
    if not isinstance(max_tokens, int) or not 1 <= max_tokens <= 2048:
        return jsonify({"error": "max_tokens deve estar entre 1 e 2048"}), 400
    models = [data["model"]] if isinstance(data.get("model"), str) else FREE_MODELS
    for model in models:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "X-Title": "Genus AI"},
                json={"model": model, "messages": messages, "max_tokens": max_tokens}, timeout=30,
            )
            if response.ok:
                return jsonify(response.json())
            logging.warning("Modelo %s falhou com HTTP %s", model, response.status_code)
        except requests.RequestException as error:
            logging.warning("Falha no provedor: %s", error)
    return jsonify({"error": "provedor indisponível"}), 502


if __name__ == "__main__":
    app.run(host=LOCAL_API_HOST, port=LOCAL_API_PORT, debug=False)
