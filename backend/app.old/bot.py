import discord
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# Dify API設定
DIFY_API_URL = "http://luma-dify-api:5001/v1/chat-messages"
# .env に DIFY_APP_API_KEY を設定してください
DIFY_API_KEY = os.getenv("DIFY_APP_API_KEY")

client = discord.Client(intents=discord.Intents.default())
conversations = {}

@client.event
async def on_ready():
    print(f'✅ Dify Bridge Bot (Ollama Backend) Logged in as {client.user}')
    if not DIFY_API_KEY:
        print("⚠️ WARNING: DIFY_APP_API_KEY is not set in .env!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not DIFY_API_KEY:
        await message.channel.send("⚠️ Dify API Keyが設定されていません。.envを確認してください。")
        return

    # リセット
    if message.content == "!reset":
        conversations[str(message.channel.id)] = ""
        await message.channel.send("🧹 会話をリセットしました（Dify）")
        return

    async with message.channel.typing():
        user_input = message.content
        channel_id = str(message.channel.id)
        conversation_id = conversations.get(channel_id, "")

        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {},
            "query": user_input,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": str(message.author.id)
        }

        async with httpx.AsyncClient(timeout=120.0) as http:
            try:
                # Dify API (Backend: Ollama) を叩く
                res = await http.post(DIFY_API_URL, headers=headers, json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "（空の回答）")
                    conversations[channel_id] = data.get("conversation_id", "")
                    await message.channel.send(answer)
                else:
                    await message.channel.send(f"⚠️ Dify Error: {res.status_code} - {res.text}")
            
            except Exception as e:
                await message.channel.send(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    client.run(TOKEN)
