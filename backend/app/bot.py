import discord
from discord.ext import commands
import os
import httpx
import google.generativeai as genai
import asyncio
import re
import datetime
from dotenv import load_dotenv
from app.services.evolver import run_evolution

load_dotenv()

# 設定
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
API_URL = "http://localhost:8000/api/v1"
EVOLUTION_CHANNEL_ID = 1471837005284507750

# Gemini 設定
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = """あなたはAI秘書の「LUMA」です。親切な日本語で会話してください。
機能が必要な場合は、回答の最後に以下のタグを付けてください。
- 天気や服装の相談 -> [ACTION:WEATHER:日数のオフセット]
  (例: 今日の天気なら [ACTION:WEATHER:0], 明日の天気なら [ACTION:WEATHER:1], 明後日の天気なら [ACTION:WEATHER:2])
- 新機能の追加、プログラムの修正、自己進化 -> [ACTION:EVOLVE]"""

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    async with message.channel.typing():
        chat = model.start_chat(history=[])
        today = datetime.date.today().isoformat()
        prompt = f"今日は {today} です。\n{SYSTEM_PROMPT}"
        response = chat.send_message(f"{prompt}\n\nユーザー: {message.content}")
        answer = response.text

        # 天気タグの処理
        if "[ACTION:WEATHER:" in answer:
            weather_offset = int(answer.split("[ACTION:WEATHER:")[-1].split("]")[0])
            # ここに天気情報を取得するロジックを実装
            answer = answer.replace(f"[ACTION:WEATHER:{weather_offset}]", "天気情報が取得されました。")

        await message.channel.send(answer)

@bot.command()
async def test(ctx):
    await ctx.send("Hello from LUMA!")

bot.run(DISCORD_TOKEN)
