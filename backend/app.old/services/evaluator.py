import httpx
import json
import os

OLLAMA_URL = "http://luma-ollama:11434/api/chat"
EVALUATOR_MODEL = "qwen3-coder:30b"

async def evaluate_execution(intent: str, result_text: str, context: str = "", chat_history: list = None) -> dict:
    """
    AIによる実行結果の評価を行う。履歴(chat_history)を考慮して、ユーザーの不満を読み取る。
    """
    
    # ユーザーの不満度をチェック
    dissatisfaction_note = ""
    if chat_history:
        # 直近のメッセージ数件を確認
        recent_messages = chat_history[-3:]
        for msg in recent_messages:
            content = msg.get("content", "").lower()
            if any(word in content for word in ["おかしい", "動かない", "ない", "違う", "bad", "wrong", "error", "fail"]):
                dissatisfaction_note += f"\n- User expressed potential frustration: '{msg.get('content')}'"

    system_prompt = f"""
    You are a Senior Software Engineer and Debugger. 
    Evaluate the execution result with a critical eye.
    
    CRITICAL RULES:
    1. If the User Intent is to find something (e.g. "In progress tasks") and the result is empty or inconsistent with the User's claim (e.g. "I have 100 tasks but you see 0"), mark this as a FAILURE.
    2. Even if the API returned 200 OK, if the LOGIC of data extraction seems wrong based on User's frustration, it is a FAILURE.
    3. In case of FAILURE, you MUST provide a 'fix_instruction' for Aider.
    4. Consider the Chat History: if the user is repeating the same complaint, the current code is definitely broken.
    
    {dissatisfaction_note}
    
    Respond ONLY in JSON format:
    {{
        "success": boolean,
        "reason": "Technical reason for success/failure",
        "fix_instruction": "Specific command for Aider like 'Fix the status mapping in app/plugins/notion_query.py to include X'"
    }}
    """
    
    user_prompt = f"[Intent] {intent}\n[Context] {context}\n[Result] {result_text}"
    
    payload = {
        "model": EVALUATOR_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "format": "json"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload)
            if response.status_code == 200:
                return json.loads(response.json().get("message", {}).get("content", "{}"))
            return {"success": False, "reason": "API Error", "fix_instruction": None}
        except Exception as e:
            return {"success": False, "reason": str(e), "fix_instruction": None}
