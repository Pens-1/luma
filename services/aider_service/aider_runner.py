"""
Aider Runner
Aiderのストリーミング実行とGit統合
"""
import asyncio
import subprocess
import os
from typing import AsyncIterator, Optional


class AiderRunner:
    """Aider実行ランナー"""
    
    def __init__(self, workspace: str = "/workspace"):
        self.workspace = workspace
        self.ollama_url = os.getenv("OLLAMA_API_BASE", "http://ollama:11434")
    
    async def run_stream(
        self,
        target_file: Optional[str],
        instruction: str
    ) -> AsyncIterator[str]:
        """
        Aiderをストリーミング実行
        
        Args:
            target_file: 修正対象ファイル（Noneの場合は自動選択）
            instruction: 修正指示
        
        Yields:
            Aiderの出力行（リアルタイム）
        """
        # Git初期化チェック
        await self._ensure_git_initialized()
        
        # Aiderコマンド構築
        cmd = [
            "aider",
            "--model", f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b')}",
            "--yes",  # 自動承認
            "--no-auto-commits",  # コミットは手動で
            "--message", instruction
        ]
        
        if target_file:
            cmd.append(target_file)
        else:
            # ファイル指定なしの場合、ワイルドカードで候補を渡す
            cmd.extend(["tools/*.py", "*.py"])
        
        # 環境変数設定
        env = os.environ.copy()
        env["OLLAMA_API_BASE"] = self.ollama_url
        
        # プロセス起動
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.workspace,
            env=env
        )
        
        # 出力をストリーミング
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            
            line = line_bytes.decode().strip()
            if line:
                yield line
        
        # プロセス完了を待つ
        await process.wait()
        
        if process.returncode != 0:
            raise Exception(f"Aider failed with exit code {process.returncode}")
    
    async def _ensure_git_initialized(self):
        """Git初期化を確認（なければ初期化）"""
        git_dir = os.path.join(self.workspace, ".git")
        
        if not os.path.exists(git_dir):
            print("🔧 Initializing Git repository...")
            
            commands = [
                ["git", "init"],
                ["git", "config", "user.email", "bot@luma.ai"],
                ["git", "config", "user.name", "LUMA Bot"],
                ["git", "add", "."],
                ["git", "commit", "-m", "Initial commit", "--allow-empty"]
            ]
            
            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0 and "nothing to commit" not in result.stdout:
                    print(f"⚠️ Git command warning: {result.stderr}")
