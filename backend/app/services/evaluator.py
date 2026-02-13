import httpx
import json
import os

OLLAMA_URL = "http://luma-ollama:11434/api/chat"
EVALUATOR_MODEL = "qwen3-coder:30b"  # 判断力と指示生成能力が高いモデル

async def evaluate_execution(intent: str, result_text: str, context: str = "") -> dict:
    """
    AIによる実行結果の評価を行う。
    
    Args:
        intent (str): ユーザーの意図またはBotの目的
        result_text (str): 実行結果（APIレスポンス、エラーログ、Botの回答など）
        context (str): 追加のコンテキスト（関連ファイルパスなど）
        
    Returns:
        dict: {
            "success": bool,
            "reason": str,
            "fix_instruction": str (or None)
        }
    """
    
    system_prompt = """
    You are an expert AI debugger and quality assurance engineer.
    Your task is to evaluate whether a code execution or API call was successful based on the User Intent and the Execution Result.
    
    If the result indicates an error (status code != 200, exception, error message) OR if the result does not match the user's intent, you must mark it as FAILURE.
    If it is a FAILURE, provide a concise but specific instruction for an AI coder (Aider) to fix the code.
    
    Respond ONLY in JSON format:
    {
        "success": boolean,
        "reason": "Short explanation of why it succeeded or failed",
        "fix_instruction": "Instruction for Aider to fix the issue (e.g. 'Modify app/bot.py to handle X...') or null if success"
    }
    """
    
    user_prompt = f"""
    [User Intent]
    {intent}
    
    [Context]
    {context}
    
    [Execution Result]
    {result_text}
    """
    
    payload = {
        "model": EVALUATOR_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "format": "json", # OllamaのJSONモードを有効化
        "options": {
            "temperature": 0.2 # 判定は厳格に
        }
    }
    
    print(f"🧐 Evaluating result with {EVALUATOR_MODEL}...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload)
            if response.status_code == 200:
                body = response.json()
                content = body.get("message", {}).get("content", "{}")
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    print(f"❌ JSON Decode Error: {content}")
                    # JSONデコード失敗時は、内容から推測するか、エラーとして返す
                    if "true" in content.lower() and "success" in content.lower():
                        return {"success": True, "reason": "JSON decode failed but output seems positive", "fix_instruction": None}
                    else:
                        return {"success": False, "reason": "Failed to parse AI evaluation", "fix_instruction": "Check the code manually."}
            else:
                return {"success": False, "reason": f"Ollama API Error: {response.text}", "fix_instruction": None}
                
        except Exception as e:
            return {"success": False, "reason": f"Connection Error: {str(e)}", "fix_instruction": None}
