"""
Discord Bot Service
Discord ↔ Redis の薄いゲートウェイ
思考・判断は一切せず、メッセージの入出力のみを担当
"""
import discord
import asyncio
import sys
import os

# 共有ライブラリをインポート
sys.path.append("/app/shared")
from redis_client import RedisClient
from message_schemas import UserMessage, BotResponse

# Discord設定
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("❌ DISCORD_BOT_TOKEN is not set!")
    exit(1)

# Discord Client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Redis Client
redis_client = RedisClient()


@client.event
async def on_ready():
    """Bot起動時"""
    print(f"✅ Discord Bot Ready: {client.user}")
    print(f"🔗 Connected to Redis")
    
    # 応答監視タスクを開始
    client.loop.create_task(listen_for_bot_responses())


@client.event
async def on_message(message):
    """メッセージ受信時"""
    # 自分のメッセージは無視
    if message.author == client.user:
        return
    
    # Botメンションまたは通常メッセージ
    content = message.content.replace(f"<@{client.user.id}>", "").strip()
    if not content:
        return
    
    # ユーザーメッセージをRedis経由でFast Serviceへ送信
    user_msg = UserMessage(
        user_id=str(message.author.id),
        username=str(message.author),
        content=content,
        channel_id=str(message.channel.id),
        timestamp=message.created_at.isoformat()
    )
    
    await redis_client.publish("input:user", user_msg.model_dump())
    print(f"📨 Forwarded message from {message.author}: {content[:50]}...")


async def listen_for_bot_responses():
    """
    Fast Serviceからの応答を購読し、Discordへ送信
    """
    print("👂 Listening for bot responses...")
    
    try:
        async for message in redis_client.subscribe("output:user"):
            # メッセージをパース
            response = BotResponse(**message)
            
            # Discord チャンネルを取得
            channel = client.get_channel(int(response.channel_id))
            if not channel:
                print(f"⚠️ Channel not found: {response.channel_id}")
                continue
            
            # メッセージ送信（2000文字制限対応）
            content = response.content
            if len(content) <= 2000:
                await channel.send(content)
            else:
                # 分割送信
                chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
                for chunk in chunks:
                    await channel.send(chunk)
            
            print(f"💬 Sent response to channel {response.channel_id}")
    
    except Exception as e:
        print(f"❌ Error in listen_for_bot_responses: {e}")
        # 再接続
        await asyncio.sleep(5)
        client.loop.create_task(listen_for_bot_responses())


if __name__ == "__main__":
    print("🚀 Starting Discord Bot...")
    client.run(TOKEN)
