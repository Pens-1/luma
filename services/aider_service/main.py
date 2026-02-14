"""
Aider Service - コード修正職人
修正リクエストを受け取り、Aiderでコード修正を実行
進捗をリアルタイムで報告
"""
import asyncio
import sys
import os

# 共有ライブラリをインポート
sys.path.append("/app/shared")
from redis_client import RedisClient
from message_schemas import AiderRequest, AiderProgress

# Aider Service固有のモジュール
from aider_runner import AiderRunner


redis_client = RedisClient()
aider_runner = AiderRunner()


async def handle_fix_request(request_data: dict):
    """修正リクエストを処理"""
    request = AiderRequest(**request_data)
    
    print(f"🔧 Fix request: type={request.type}, target={request.target_file}")
    
    # 進捗報告: 開始
    await report_progress("starting", f"🔍 コード解析を開始...")
    
    # Aider実行（ストリーミング）
    try:
        async for output in aider_runner.run_stream(
            target_file=request.target_file,
            instruction=request.instruction
        ):
            await report_progress("running", output)
        
        # 完了報告
        target_display = request.target_file or "コード"
        await report_progress("completed", f"✅ {target_display} の修正が完了しました")
    
    except Exception as e:
        await report_progress("failed", f"❌ 修正失敗: {str(e)}")


async def report_progress(status: str, message: str):
    """進捗をRedisに報告"""
    progress = AiderProgress(status=status, message=message)
    await redis_client.publish("aider:progress", progress.model_dump())
    print(f"📢 Progress: [{status}] {message[:50]}...")


async def main():
    """メインループ"""
    print("🚀 Aider Service starting...")
    print("🛠️ Ready to fix code...")
    
    # 修正リクエストを購読
    async for message in redis_client.subscribe("aider:requests"):
        try:
            await handle_fix_request(message)
        except Exception as e:
            print(f"❌ Error handling fix request: {e}")
            await report_progress("failed", f"❌ エラー: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
