import os
import json
import urllib.request
import urllib.parse

class SocialTools:
    @staticmethod
    def discord_webhook(webhook_url, content):
        """Envia uma mensagem para um canal do Discord via Webhook."""
        if not webhook_url or not webhook_url.startswith("https://discord.com/api/webhooks/"):
            return "Erro: URL de Webhook do Discord inválida."
        
        data = json.dumps({"content": content}).encode("utf-8")
        req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json", "User-Agent": "Genus-AI"})
        
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return "Mensagem enviada para o Discord."
        except Exception as e:
            return f"Erro ao enviar mensagem para o Discord: {e}"

    @staticmethod
    def discord_bot(token, channel_id, message):
        """Envia mensagem usando um bot token (requer discord.py)."""
        # Como genes roda autonomamente, podemos tentar usar o discord.py se instalado
        try:
            import discord
            import asyncio
            
            async def send():
                client = discord.Client(intents=discord.Intents.default())
                await client.login(token)
                channel = await client.fetch_channel(int(channel_id))
                await channel.send(message)
                await client.close()
            
            asyncio.run(send())
            return "Mensagem enviada via bot Discord."
        except ImportError:
            return "Erro: 'discord.py' não instalado. Use pip install discord.py."
        except Exception as e:
            return f"Erro: {e}"
