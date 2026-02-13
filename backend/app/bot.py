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
EVOLUTION_CHANNEL_ID = 1471837005284507750  # 指定された開発用チャンネルID

# Gemini 設定
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = """
あなたはAI秘書の「LUMA」です。
ユーザーのメッセージを解析し、以下の機能が必要な場合は、回答の最後に特定のタグを付けてください。

- 天気や服装の相談 -> [ACTION:WEATHER:日数のオフセット]
  (例: 今日の天気なら [ACTION:WEATHER:0], 明日なら [ACTION:WEATHER:1])
- 新機能の追加、プログラムの修正、自己進化 -> [ACTION:EVOLVE]

返答は親切な日本語で行い、タグは必ず含めてください。
"""

@bot.event
async def on_ready():
    print(f"✅ LUMA Evolution Engine logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # コマンドの場合はそのまま処理
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # 通常の文章に対して Gemini が反応
    async with message.channel.typing():
        chat = model.start_chat(history=[])
        full_prompt = f"{SYSTEM_PROMPT}\n\nユーザー: {message.content}"
        response = chat.send_message(full_prompt)
        answer = response.text

        # 天気アクション
        weather_match = re.search(r"\[ACTION:WEATHER:(\d+)\]", answer)
        if weather_match:
            day_index = int(weather_match.group(1))
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.get(f"{API_URL}/plugins/weather-clothing/?day_index={day_index}")
                    data = res.json()
                    day_label = data.get("day_label", "指定日")
                    advice = f"\n\n🌍 **{day_label}（{data.get('date', '')}）の天気予報**\n🌡️ 気温: {data['today']['min_temp']}℃ 〜 {data['today']['max_temp']}℃\n💡 **服装アドバイス**: {data['suggestion']}"
                    answer = re.sub(r"\[ACTION:WEATHER:\d+\]", advice, answer)
                except:
                    answer = re.sub(r"\[ACTION:WEATHER:\d+\]", "\n(すみません、天気情報の取得に失敗しました。)", answer)

        # 進化アクションへの誘導
        if "[ACTION:EVOLVE]" in answer:
            evolve_msg = f"\n\n🚀 **自己進化（機能追加・修正）が必要ですね。**\n恐れ入りますが、開発用チャンネル <#{EVOLUTION_CHANNEL_ID}> で「!evolve [具体的な指示]」と送っていただけますか？"
            answer = answer.replace("[ACTION:EVOLVE]", evolve_msg)

        await message.reply(answer)

@bot.command()
async def evolve(ctx, *, prompt: str):
    """
    自律的に新機能を実装・修正します。開発用チャンネルでのみ動作します。
    """
    if ctx.channel.id != EVOLUTION_CHANNEL_ID:
        await ctx.reply(f"⚠️ このコマンドは開発用チャンネル <#{EVOLUTION_CHANNEL_ID}> で実行してください。")
        return

    embed = discord.Embed(
        title="🚀 自己進化プロトコル起動", 
        description=f"**指示内容:**\n{prompt}\n\n---\n現在、Qwen3-Coder がコードベースを分析し、修正を適用しています。完了まで数分かかる場合があります。", 
        color=0x58c9b9
    )
    status_msg = await ctx.reply(embed=embed)

    loop = asyncio.get_event_loop()
    try:
        # Aiderを非同期で実行
        result_log = await loop.run_in_executor(None, run_evolution, prompt)
        
        # 成功時の埋め込み
        success_embed = discord.Embed(
            title="✅ 自己進化完了", 
            description=f"「{prompt}」に関する修正が完了しました。\nFastAPI のホットリロードにより、既に新しい機能が有効です。", 
            color=0x58c9b9
        )
        # ログが長い場合は切り詰めて表示
        if result_log:
            log_preview = result_log[-500:] if len(result_log) > 500 else result_log
            success_embed.add_field(name="実行ログ(抜粋)", value=f"```\n{log_preview}\n```", inline=False)
            
        await status_msg.edit(embed=success_embed)
    except Exception as e:
        await ctx.send(f"❌ 進化プロセス中に致命的なエラーが発生しました:\n```\n{str(e)}\n```")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
