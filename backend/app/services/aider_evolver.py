import subprocess
import os
import asyncio

async def run_aider_evolution(instruction: str, target_file: str = "app/bot.py") -> str:
    """
    Aiderを使ってコードを修正する。
    
    Args:
        instruction (str): 修正指示
        target_file (str): 対象ファイルパス
    
    Returns:
        str: 実行結果のログ
    """
    
    # ワークディレクトリ (コンテナ内の /app は backend/app がマウントされている場所ではなく、
    # Dockerfileで COPY . /app されている場所。
    # しかし docker-compose で ./backend/app:/app/app されているので、
    # /app 直下で git init すれば全体をカバーできるはず。
    cwd = "/app"
    
    # Git初期化チェック
    if not os.path.exists(os.path.join(cwd, ".git")):
        print("🔧 Initializing Git repository for Aider...")
        try:
            subprocess.run(["git", "init"], cwd=cwd, check=True)
            subprocess.run(["git", "config", "user.email", "bot@luma.ai"], cwd=cwd, check=True)
            subprocess.run(["git", "config", "user.name", "LUMA Bot"], cwd=cwd, check=True)
            # とりあえず現状をコミット
            subprocess.run(["git", "add", "."], cwd=cwd, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=cwd, check=False) # 何も変更がない場合はエラーになるのでcheck=False
        except Exception as e:
            return f"❌ Git initialization failed: {str(e)}"

    max_retries = 3
    current_instruction = instruction
    
    for attempt in range(max_retries):
        print(f"🚀 Running Aider (Attempt {attempt+1}/{max_retries})...")
        
        # Aider実行
        # --no-git-anchor: リポジトリルートを検索しない（カレントディレクトリを使用）
        cmd = [
            "aider",
            "--model", "ollama/qwen3-coder:30b",
            "--yes", # 常にyesで応答
            "--no-auto-commits", # コミットはさせない（コンテナ内Gitなので意味が薄い＆競合回避）
            "--message", current_instruction,
            target_file
        ]
        
        env = os.environ.copy()
        env["OLLAMA_API_BASE"] = "http://luma-ollama:11434"
        
        try:
            # Aider実行 (asyncio.to_thread)
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True
            )
            
            output = result.stdout + "\n" + result.stderr
            
            # Aider自体の実行エラーチェック
            if result.returncode != 0:
                return f"⚠️ Aider failed with exit code {result.returncode}:\n\n```\n{output[-1000:]}\n```"

            # --- 構文チェック ---
            # Pythonファイルの場合のみチェック
            if target_file.endswith(".py"):
                file_path = os.path.join(cwd, target_file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        source = f.read()
                    compile(source, file_path, "exec")
                    
                    # 構文OKなら成功として終了
                    return f"✅ Aider Evolution Completed (Attempt {attempt+1})!\nSyntax Check Passed.\n\n```\n{output[-800:]}\n```"
                    
                except SyntaxError as e:
                    print(f"❌ Syntax Error detected: {e}")
                    error_msg = f"SyntaxError: {e.msg} (Line {e.lineno})"
                    
                    # エラー情報を次回の指示に追加
                    current_instruction = f"Previous fix resulted in a Syntax Error. Please fix it:\n{error_msg}\n\nOriginal Request: {instruction}"
                    
                    if attempt == max_retries - 1:
                        return f"❌ Evolution Failed: Syntax Error persisted after {max_retries} attempts.\n{error_msg}"
                    
                    continue # 次の試行へ
                except Exception as e:
                     # その他のエラー（ファイルがない等）
                     return f"⚠️ Verification Error: {str(e)}"

            # Python以外はチェックせずに終了
            return f"✅ Aider Evolution Completed!\n\n```\n{output[-800:]}\n```"
            
        except Exception as e:
            return f"❌ Aider execution error: {str(e)}"
