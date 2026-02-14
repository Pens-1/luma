import subprocess
import os

def run_evolution(prompt: str):
    """
    Aiderを使用して自律的にコードを生成・修正する。
    """
    # qwen3:30b を使用して Aider を起動
    command = [
        "aider",
        "--model", "ollama/qwen3:30b",
        "--yes",
        "--message", f"LUMAの自己進化プロトコルに従って、以下の機能をプラグインとして実装してください。既存のファイルを破壊せず、必要な関数やクラスを追加・修正してください: {prompt}"
    ]
    
    try:
        # Aiderを実行
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd="/home/user/repos/luma" # プロジェクトルートで実行
        )
        return result.stdout
    except Exception as e:
        return f"Evolution error: {str(e)}"
