"""
Evaluator Service - 監視Ollama
Fast Serviceの実行結果を評価し、修正要否を判定
"""
import asyncio
import sys
import os
import json

# 共有ライブラリをインポート
sys.path.append("/app/shared")
from redis_client import RedisClient
from message_schemas import EvaluationRequest, EvaluationResponse, AiderRequest

# Evaluator Service固有のモジュール
from llm_evaluator import LLMEvaluator


redis_client = RedisClient()
llm_evaluator = LLMEvaluator(os.getenv("OLLAMA_URL", "http://ollama:11434"))


async def handle_evaluation_request(request_data: dict):
    """Fast Serviceからの評価依頼を処理"""
    request = EvaluationRequest(**request_data)
    context = request.context
    
    print(f"🔍 Evaluating: intent='{context.get('intent', 'N/A')}'")
    
    # LLMで評価
    evaluation = await llm_evaluator.evaluate(context)
    
    # Fast Serviceに返答
    response = EvaluationResponse(**evaluation)
    await redis_client.publish(
        f"evaluator:response:{request.request_id}",
        response.model_dump()
    )
    
    print(f"✅ Evaluation: is_correct={evaluation['is_correct']}, should_fix={evaluation.get('should_fix', False)}")
    
    # 修正が必要ならAiderにも通知
    if evaluation.get("should_fix"):
        aider_request = AiderRequest(
            type="auto_fix",
            target_file=evaluation.get("fix_target"),
            instruction=evaluation.get("fix_instruction", "エラーを修正"),
            context=context
        )
        await redis_client.publish("aider:requests", aider_request.model_dump())
        print(f"🚀 Sent fix request to Aider: {aider_request.target_file}")


async def main():
    """メインループ"""
    print("🚀 Evaluator Service starting...")
    print("👁️ Monitoring execution logs...")
    
    # 評価リクエストを購読
    async for message in redis_client.subscribe("evaluator:request"):
        try:
            await handle_evaluation_request(message)
        except Exception as e:
            print(f"❌ Error handling evaluation: {e}")


if __name__ == "__main__":
    asyncio.run(main())
