import discord
from discord.ext import commands
import os
import httpx
import google.generativeai as genai
import asyncio
import re
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

SYSTEM_PROMPT = """
あなたはAI秘書の「LUMA」です。親切な日本語で会話してください。
機能が必要な場合は、回答の最後に以下のタグを付けてください。
- 天気や服装の相談 -> [ACTION:WEATHER:日数のオフセット]
  (例: 今日の天気なら [ACTION:WEATHER:0], 明日の天気なら [ACTION:WEATHER:1])
- 新機能の追加、プログラムの修正、自己進化 -> [ACTION:EVOLVE]
"""

@bot.event
async def on_ready():
    print(f"✅ LUMA Evolution Engine restored and logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    async with message.channel.typing():
        chat = model.start_chat(history=[])
        response = chat.send_message(f"{SYSTEM_PROMPT}\n\nユーザー: {message.content}")
        answer = response.text

        # 天気アクションの解析 [ACTION:WEATHER:n]
        weather_match = re.search(r"\[ACTION:WEATHER:(\d+)\]", answer)
        if weather_match:
            day_index = int(weather_match.group(1))
            async with httpx.AsyncClient() as client:
                try:
                    # 正しく day_index をパラメータとして渡す
                    res = await client.get(f"{API_URL}/plugins/weather-clothing/?day_index={day_index}")
                    data = res.json()
                    day_label = data.get("day_label", "指定日")
                    advice = f"\n\n🌍 **{day_label}（{data.get('date', '')}）の天気予報**\n🌡️ 気温: {data['today']['min_temp']}℃ 〜 {data['today']['max_temp']}℃\n💡 **服装アドバイス**: {data['suggestion']}\n☔ **傘の必要性**: {'必要です ☔' if data.get('umbrella_needed') else '不要です ☀️'}"
                    answer = re.sub(r"\[ACTION:WEATHER:\d+\]", advice, answer)
                except Exception as e:
                    print(f"Weather API Error: {e}")
                    answer = re.sub(r"\[ACTION:WEATHER:\d+\]", "\n(すみません、天気データの取得に失敗しました。)", answer)

        if "[ACTION:EVOLVE]" in answer:
            evolve_msg = f"\n\n🚀 **自己進化の提案**: 開発チャンネル <#{EVOLUTION_CHANNEL_ID}> で詳細を指示してください。"
            answer = answer.replace("[ACTION:EVOLVE]", evolve_msg)

        await message.reply(answer)

@bot.command()
async def evolve(ctx, *, prompt: str):
    if ctx.channel.id != EVOLUTION_CHANNEL_ID:
        await ctx.reply(f"⚠️ 開発用チャンネル <#{EVOLUTION_CHANNEL_ID}> で実行してください。")
        return
    embed = discord.Embed(title="🚀 自己進化プロトコル起動", description=f"要件: {prompt}\n現在実行中です...", color=0x58c9b9)
    status_msg = await ctx.reply(embed=embed)
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, run_evolution, prompt)
        await status_msg.edit(embed=discord.Embed(title="✅ 自己進化完了", description=f"「{prompt}」を実装・修正しました。", color=0x58c9b9))
    except Exception as e:
        await ctx.send(f"❌ エラー: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
