#!/bin/bash

# プロジェクトルートに移動
cd /app

# 1. ターゲットとなる強力なテストスイートを指定
# ここでは、あなたが以前作成した「自律デバッグ」や「レジリエンス」のテストを指定します
TEST_COMMAND="pytest app/tests/test_action_resilience.py app/tests/test_bot_loop.py"

# 2. AiderをTDDモードで起動
# --yes: ユーザー確認をスキップ
# --test-cmd: テスト実行コマンド
# --auto-test: テスト失敗時に自動修復を試みる
echo "🚀 Starting TDD Evolution Loop..."
aider 
    --model ollama/qwen3-coder:30b 
    --yes 
    --test-cmd "$TEST_COMMAND" 
    --message "Run the tests. If they fail, analyze the error output and fix the code in app/services/action_handler.py and app/plugins/notion_query.py until all tests pass. Ensure robust error handling and pagination support." 
    app/services/action_handler.py 
    app/plugins/notion_query.py 
    app/bot.py

echo "✅ Evolution Cycle Completed."
