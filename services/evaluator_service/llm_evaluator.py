"""
LLM Evaluator
OllamaのLLMを使って実行結果を評価
"""
import httpx
import json
from typing import Dict, Any


class LLMEvaluator:
    """LLMベースの評価エンジン"""
    
    def __init__(self, ollama_url: str):
        self.ollama_url = ollama_url
        self.chat_url = f"{ollama_url}/api/chat"
        self.model = "qwen3-coder:30b"
    
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        実行結果を評価
        
        Args:
            context: {
                "intent": ユーザーの意図,
                "result": 実行結果,
                "user_id": ユーザーID (optional)
            }
        
        Returns:
            {
                "is_correct": bool,
                "reason": str,
                "should_fix": bool,
                "fix_target": str,
                "fix_instruction": str
            }
        """
        intent = context.get("intent", "")
        result = context.get("result", {})
        
        # 評価プロンプト
        prompt = f"""
あなたは品質保証エンジニアです。
以下の実行結果が正しいか評価してください。

【ユーザーの意図】
{intent}

【実行結果】
{json.dumps(result, ensure_ascii=False, indent=2)}

【評価基準】
1. APIエラーがないか？
2. データ量が不自然でないか？
   - 例：ユーザーが「たくさんある」と言っているのに0件
3. ステータスやフィルタが正しく解釈されているか？

JSON形式で回答してください：
{{
    "is_correct": true or false,
    "reason": "判断理由（簡潔に）",
    "should_fix": true or false,
    "fix_target": "修正すべきファイル（例: tools/notion.py）",
    "fix_instruction": "Aiderへの具体的な修正指示"
}}
"""
        
        # Ollama呼び出し
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2}  # 評価は厳格に
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.chat_url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                content = data.get("message", {}).get("content", "{}")

                evaluation = json.loads(content)
                
                # デフォルト値設定
                evaluation.setdefault("is_correct", True)
                evaluation.setdefault("reason", "No specific issues found")
                evaluation.setdefault("should_fix", False)
                evaluation.setdefault("fix_target", None)
                evaluation.setdefault("fix_instruction", None)
                
                return evaluation
            
            except Exception as e:
                print(f"❌ Evaluation error: {e}")
                # エラー時はフォールバック（修正不要と判断）
                return {
                    "is_correct": True,
                    "reason": f"Evaluation failed: {str(e)}",
                    "should_fix": False,
                    "fix_target": None,
                    "fix_instruction": None
                }
