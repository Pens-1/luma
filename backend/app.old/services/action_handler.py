import re
import httpx
import os
import asyncio
import json
import discord
from app.services.aider_evolver import run_aider_evolution, run_aider_evolution_auto
from app.services.evaluator import evaluate_execution

API_URL = "http://localhost:8000/api/v1"
EVOLUTION_CHANNEL_ID = 1471837005284507750

# Discord bot クライアントを保持（メッセージ送信用）
bot_client = None

def set_bot_client(bot):
    global bot_client
    bot_client = bot

def truncate_or_summarize(text: str, max_length: int = 1000) -> str:
    """出力を要約する（以前のロジックを復元）"""
    if len(text) <= max_length: return text
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "tasks" in data:
            count = data.get("count", 0)
            tasks = data.get("tasks", [])[:3]
            summary = [f"- {t.get('title')} ({t.get('status')})" for t in tasks]
            return f"Found {count} tasks:\n" + "\n".join(summary) + f"\n... and {count-3} more."
    except: pass
    return text[:max_length] + "..."

async def send_to_evolution_channel(msg: str):
    """進化チャンネルにログを送る"""
    if bot_client:
        channel = bot_client.get_channel(EVOLUTION_CHANNEL_ID)
        if channel:
            await channel.send(msg)

async def execute_actions(text: str, message_obj=None, chat_history: list = None) -> str:
    """アクションをパースして実行する（完全復旧版）"""
    results = []
    has_action = False

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Weather
        for match in re.finditer(r"\[ACTION:WEATHER:(\d+)\]", text):
            has_action = True
            day_index = int(match.group(1))
            try:
                res = await client.get(f"{API_URL}/plugins/weather-clothing/?day_index={day_index}")
                results.append(f"Tool Output [WEATHER]: {res.text}")
            except Exception as e:
                results.append(f"Tool Output [WEATHER]: Failed ({str(e)})")

        # 2. Notion List
        for match in re.finditer(r"\[ACTION:NOTION:([^\]]+)\]", text):
            has_action = True
            status = match.group(1).strip()
            try:
                if message_obj: await message_obj.channel.send(f"🔍 Notionで「{status}」を検索中...")
                res = await client.get(f"{API_URL}/plugins/notion/todos", params={"status": status})
                data = res.json()
                results.append(f"Tool Output [NOTION_LIST]: {truncate_or_summarize(json.dumps(data, ensure_ascii=False))}")
            except Exception as e:
                results.append(f"Tool Output [NOTION_LIST]: Failed ({str(e)})")

        # 3. Notion Create
        for match in re.finditer(r"\[ACTION:NOTION_CREATE:([^:\]]+)(?::([^\]]+))?\]", text):
            has_action = True
            title, due = match.group(1), match.group(2)
            try:
                res = await client.post(f"{API_URL}/plugins/notion/todos", params={"title": title, "due_date": due})
                results.append(f"Tool Output [NOTION_CREATE]: {res.text}")
            except Exception as e:
                results.append(f"Tool Output [NOTION_CREATE]: Failed ({str(e)})")

        # 4. Evolve
        for match in re.finditer(r"\[ACTION:EVOLVE(?::([^:]+):(.+))?\]", text):
            has_action = True
            target, instruction = match.group(1), match.group(2)
            await send_to_evolution_channel(f"🚀 **進化開始**\n対象: {target}\n指示: {instruction}")
            
            res_msg = await run_aider_evolution(instruction, target) if target else await run_aider_evolution_auto(instruction)
            
            await send_to_evolution_channel(f"✅ **進化完了**\n結果: {res_msg[:1000]}...")
            results.append(f"Tool Output [EVOLVE]: {res_msg}")

        # 5. Test
        if "[ACTION:TEST]" in text:
            has_action = True
            results.append("Tool Output [SELF_TEST]: OK")

    return "\n".join(results) if has_action else ""
