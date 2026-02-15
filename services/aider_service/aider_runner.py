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
        instruction: str,
        test_command: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Aiderをストリーミング実行
        
        Args:
            target_file: 修正対象ファイル（Noneの場合は自動選択）
            instruction: 修正指示
            test_command: 実行するテストコマンド（TDD用）
        
        Yields:
            Aiderの出力行（リアルタイム）
        """
        # Git初期化チェック
        await self._ensure_git_initialized()
        
        # Aiderコマンド構築
        cmd = [
            "aider",
            "--model", f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen3-coder:30b')}",
            "--yes",  # 自動承認
            "--no-auto-commits",  # コミットは手動で
            "--map-tokens", "1024",  # アーキテクチャマップを強化
            "--message", instruction
        ]

        # テスト駆動開発 (TDD) のための設定
        if test_command:
            cmd.extend(["--test-cmd", test_command])
        
        # リンター設定
        cmd.extend(["--lint-cmd", "flake8 --select=E9,F63,F7,F82 --show-source"])
        
        # Files to edit/read
        # Always include main.py (to register tools) and the guide
        cmd.extend(["main.py", "TOOL_CREATION_GUIDE.md"])
        
        if target_file:
            cmd.append(target_file)
        else:
            # If no specific target, give it the whole tools directory so it sees existing patterns
            cmd.append("tools")
        
        # 環境変数設定
        env = os.environ.copy()
        env["OLLAMA_API_BASE"] = self.ollama_url
        # PYTHONPATHにワークスペースを追加して、テスト実行時のインポートエラーを防ぐ
        env["PYTHONPATH"] = f"{self.workspace}:{env.get('PYTHONPATH', '')}"
        
        print(f"🚀 Running Aider CMD: {' '.join(cmd)}")
        
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
            subprocess.run(["git", "init"], cwd=self.workspace, check=True)
            subprocess.run(["git", "config", "user.email", "bot@luma.ai"], cwd=self.workspace, check=True)
            subprocess.run(["git", "config", "user.name", "LUMA Bot"], cwd=self.workspace, check=True)

        # Always ensure current state is committed so Aider sees a clean state
        # EXCEPT for the file we want it to edit? No, Aider edits clean files too.
        # But if main.py is dirty (modified by me), Aider might complain.
        # Let's commit everything.
        subprocess.run(["git", "add", "."], cwd=self.workspace, check=False)
        subprocess.run(["git", "commit", "-m", "Auto sync before run", "--allow-empty"], cwd=self.workspace, check=False)
            
        # ensure Clean state
        subprocess.run(["git", "add", "."], cwd=self.workspace, check=False)
        subprocess.run(["git", "commit", "-m", "Auto sync before run", "--allow-empty"], cwd=self.workspace, check=False)
