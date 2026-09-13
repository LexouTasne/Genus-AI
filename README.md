# Genus AI

Assistente local por voz com pesquisa, memória RAG simples e modelos via OpenRouter.

## Início rápido

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# preencha OPENROUTER_API_KEY e GENUS_LOCAL_API_TOKEN em .env
./run.sh "olá, Genus"
```

A API local escuta somente em `127.0.0.1` e exige `Authorization: Bearer <GENUS_LOCAL_API_TOKEN>` em `/chat`. O endpoint `/health` é público apenas para monitoramento local.

## Segurança

- Nunca versione `.env`, conversas, áudios, logs ou cache RAG.
- `BASH` e execução de código gerado ficam desativados por padrão. Quando inevitável, use uma máquina isolada e uma allowlist curta.
- Rotacione qualquer chave que já tenha sido commitada: removê-la de um commit novo não a remove do histórico público.

## Testes

```bash
python3 -m unittest discover -s tests -v
```
