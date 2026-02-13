import httpx
import os
import re
import subprocess
import json
from typing import Optional, Dict

OLLAMA_URL = "http://luma-ollama:11434/api/generate"
MODEL_NAME = "qwen3-coder:30b"
PROJECT_ROOT = "/app" # Docker内でのパス

async def generate_code_change(prompt: str, file_content: str, file_path: str) -> str:
    """
    Ollamaに指示とファイル内容を渡し、変更後のコード（または差分）を生成させる
    """
    system_prompt = f"""
    あなたは熟練したPythonエンジニアです。
    ユーザーの指示に従って、指定されたファイルのコードを修正してください。
    
    【ルール】
    1. 出力は変更後の **ファイル全体** のコードのみを ```python ブロックで囲んで返してください。
    2. 説明や会話は不要です。コードのみを出力してください。
    3. 既存の機能を壊さないように注意してください。
    
    【対象ファイル】: {file_path}
    
    【現在のコード】:
    ```python
    {file_content}
    ```
    """
    
    user_prompt = f"指示: {prompt}"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 8192}
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload)
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return f"Error: {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

def extract_code_block(text: str) -> Optional[str]:
    """Markdownのコードブロックからコードを抽出"""
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # python指定がない場合
    match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
        
    return None

async def run_evolution_task(instruction: str, target_file_rel: str):
    """
    自律進化タスクの実行フロー
    1. 対象ファイルの読み込み
    2. AIによるコード修正生成
    3. ファイル書き込み
    4. 構文チェック / テスト実行
    """
    target_path = os.path.join(PROJECT_ROOT, target_file_rel)
    
    if not os.path.exists(target_path):
        return f"❌ エラー: 対象ファイルが見つかりません: {target_file_rel}"
        
    try:
        with open(target_path, "r") as f:
            current_code = f.read()
            
        # AIに修正を依頼
        generated_text = await generate_code_change(instruction, current_code, target_file_rel)
        
        if "Error:" in generated_text:
            return f"❌ AI生成エラー: {generated_text}"
            
        new_code = extract_code_block(generated_text)
        if not new_code:
            return "❌ エラー: 有効なコードブロックが生成されませんでした。"
            
        # ファイル書き込み（バックアップを取るのが理想だが今回は直接上書き）
        with open(target_path, "w") as f:
            f.write(new_code)
            
        # 構文チェック
        try:
            subprocess.run(["python3", "-m", "py_compile", target_path], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # 失敗したら元に戻す（簡易ロールバック）
            with open(target_path, "w") as f:
                f.write(current_code)
            return f"❌ 構文エラーによりロールバックしました:\n{e.stderr.decode()}"
            
        return f"✅ **進化成功**: `{target_file_rel}` を更新しました！\n（構文チェックOK）"

    except Exception as e:
        return f"❌ 予期せぬエラー: {str(e)}"
