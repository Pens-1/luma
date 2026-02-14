"""
Fast Service - Main Brain
ユーザーとの対話、ツール実行、Evaluator/Aider連携を担当
"""
import asyncio
import sys
import os
import uuid
import re
from datetime import datetime

# 共有ライブラリをインポート
sys.path.append("/app/shared")
from redis_client import RedisClient
from message_schemas import UserMessage, BotResponse, EvaluationRequest, EvaluationResponse, AiderRequest
from utils import format_result, detect_complaint

# Fast Service固有のモジュール
from ollama_client import OllamaClient
from tools import notion, weather


# 設定
OLLAMA_MODEL = "qwen3-coder:30b"
redis_client = RedisClient()
ollama_client = OllamaClient(os.getenv("OLLAMA_URL", "http://ollama:11434"))

SYSTEM_PROMPT = f"""
あなたはAI自律エンジニア「LUMA（ルーマ）」です。
現在日時: {datetime.now().strftime("%Y年%m月%d日 (%A) %H:%M")}

ユーザーの良きパートナーとして、タスク管理と開発サポートを行います。
丁寧で親しみやすい日本語で話してください。

利用可能なアクションタグ:
- [ACTION:NOTION:ステータス] : Notionのタスクを確認 (例: [ACTION:NOTION:In progress])
- [ACTION:NOTION_CREATE:タスク名:期限] : Notionにタスクを追加 (例: [ACTION:NOTION_CREATE:買い物:2026-02-20])
- [ACTION:WEATHER:日数] : 天気を調べる (例: [ACTION:WEATHER:0] 今日)

重要: アクションが必要な場合は、アクションタグのみを出力してください。
"""


async def handle_user_message(msg_data: dict):
    """ユーザーメッセージを処理"""
    message = UserMessage(**msg_data)
    print(f"📨 Received from {message.username}: {message.content[:50]}...")
    
    # Ollamaで思考
    response = await ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message.content}
        ],
        temperature=0.5
    )
    
    # アクション検出と実行
    if "[ACTION:NOTION:" in response:
        await execute_notion_action(response, message)
    elif "[ACTION:NOTION_CREATE:" in response:
        await execute_notion_create_action(response, message)
    elif "[ACTION:WEATHER:" in response:
        await execute_weather_action(response, message)
    else:
        # 通常応答
        await send_to_user(message.channel_id, response)


async def execute_notion_action(response: str, original_msg: UserMessage):
    """Notionアクション実行 + Evaluator評価"""
    # ステータス抽出
    match = re.search(r"\[ACTION:NOTION:([^\]]+)\]", response)
    if not match:
        await send_to_user(original_msg.channel_id, "❌ アクション形式が不正です")
        return
    
    status = match.group(1).strip()
    
    # Notion API実行
    await send_to_user(original_msg.channel_id, f"🔍 Notionで「{status}」を検索中...")
    result = await notion.get_tasks(status)
    
    # Evaluatorに評価依頼
    evaluation = await ask_evaluator({
        "intent": original_msg.content,
        "result": result,
        "user_id": original_msg.user_id
    })
    
    if not evaluation.get("is_correct", True):
        # 修正が必要
        await send_to_user(
            original_msg.channel_id,
            f"🔍 問題を検知しました: {evaluation['reason']}\n"
            f"🚀 Aiderに修正を依頼しています..."
        )
        
        # Aider に修正依頼
        await request_aider_fix(evaluation)
        
        # Aider の進捗をユーザーに流す
        await stream_aider_progress(original_msg.channel_id)
    else:
        # 正常な応答
        response_text = format_result(result)
        await send_to_user(original_msg.channel_id, response_text)


async def execute_notion_create_action(response: str, original_msg: UserMessage):
    """Notionタスク作成アクション"""
    match = re.search(r"\[ACTION:NOTION_CREATE:([^:]+)(?::([^\]]+))?\]", response)
    if not match:
        await send_to_user(original_msg.channel_id, "❌ アクション形式が不正です")
        return
    
    title = match.group(1).strip()
    due_date = match.group(2).strip() if match.group(2) else None
    
    await send_to_user(original_msg.channel_id, f"📝 タスク「{title}」を作成中...")
    result = await notion.create_task(title, due_date)
    
    if "error" in result:
        await send_to_user(original_msg.channel_id, f"❌ {result['error']}")
    else:
        await send_to_user(
            original_msg.channel_id,
            f"✅ タスク「{result['title']}」を作成しました\n{result['url']}"
        )


async def execute_weather_action(response: str, original_msg: UserMessage):
    """天気アクション"""
    match = re.search(r"\[ACTION:WEATHER:(\d+)\]", response)
    if not match:
        await send_to_user(original_msg.channel_id, "❌ アクション形式が不正です")
        return
    
    day_index = int(match.group(1))
    result = await weather.get_weather(day_index)
    
    response_text = f"{result['day']}の天気: {result['weather']}\n{result['temperature']}\n{result.get('note', '')}"
    await send_to_user(original_msg.channel_id, response_text)


async def ask_evaluator(context: dict) -> dict:
    """Evaluatorに評価依頼"""
    request_id = str(uuid.uuid4())
    
    request = EvaluationRequest(
        request_id=request_id,
        context=context
    )
    
    # 依頼を送信
    await redis_client.publish("evaluator:request", request.model_dump())
    
    # 応答を待つ（タイムアウト10秒）
    try:
        async with asyncio.timeout(10):
            async for message in redis_client.subscribe(f"evaluator:response:{request_id}"):
                return message
    except asyncio.TimeoutError:
        print("⚠️ Evaluator timeout")
        return {"is_correct": True, "reason": "Evaluator timeout"}


async def request_aider_fix(evaluation: dict):
    """Aiderに修正依頼"""
    aider_request = AiderRequest(
        type="auto_fix",
        target_file=evaluation.get("fix_target"),
        instruction=evaluation.get("fix_instruction", "エラーを修正"),
        context=evaluation
    )
    
    await redis_client.publish("aider:requests", aider_request.model_dump())


async def stream_aider_progress(channel_id: str):
    """Aiderの進捗をユーザーに流す"""
    try:
        async with asyncio.timeout(300):  # 最大5分
            async for progress in redis_client.subscribe("aider:progress"):
                message = progress.get("message", "")
                await send_to_user(channel_id, f"🛠️ Aider: {message}")
                
                if progress.get("status") == "completed":
                    break
    except asyncio.TimeoutError:
        await send_to_user(channel_id, "⚠️ Aider timeout (5分経過)")


async def send_to_user(channel_id: str, content: str):
    """ユーザーに応答を送信"""
    response = BotResponse(channel_id=channel_id, content=content)
    await redis_client.publish("output:user", response.model_dump())


async def main():
    """メインループ"""
    print("🚀 Fast Service starting...")
    print(f"🧠 Model: {OLLAMA_MODEL}")
    
    # ユーザーメッセージを購読
    async for message in redis_client.subscribe("input:user"):
        try:
            await handle_user_message(message)
        except Exception as e:
            print(f"❌ Error handling message: {e}")
            # エラー時もユーザーに通知
            if "channel_id" in message:
                await send_to_user(
                    message["channel_id"],
                    f"❌ エラーが発生しました: {str(e)}"
                )


if __name__ == "__main__":
    asyncio.run(main())
