import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch

# 現在のディレクトリ（services/fast_service）をパスの先頭に追加して、
# site-packages の main よりも優先させる
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# shared も追加
shared_path = os.path.abspath(os.path.join(parent_dir, "../../shared"))
sys.path.insert(0, shared_path)

# main.py のモック化
import main
print(f"📦 Using main module from: {main.__file__}")

async def run_test():
    """『天気教えて』というメッセージに対してFORECASTアクションが呼ばれるかテスト"""
    print("🧪 Running integration test...")
    
    # ユーザーメッセージ
    msg_data = {
        "channel_id": "test_channel",
        "message_id": "test_msg_123",
        "user_id": "user_1",
        "username": "tester",
        "content": "東京の詳しい天気予報を教えて"
    }

    # Ollamaがタグを返すと仮定
    mock_response = "分かりました！[ACTION:FORECAST:Tokyo]"
    
    # オブジェクトを差し替え
    main.ollama_client = AsyncMock()
    main.ollama_client.chat = AsyncMock(return_value=mock_response)
    
    with (
        patch("main.send_reaction", new_callable=AsyncMock) as mock_react,
        patch("main.execute_forecast_action", new_callable=AsyncMock) as mock_exec,
        patch("main.send_to_user", new_callable=AsyncMock) as mock_send
    ):
        await main.handle_user_message(msg_data)
        
        # 検証
        try:
            main.ollama_client.chat.assert_called_once()
            mock_exec.assert_called_once()
            # 引数にタグが含まれているか
            args, _ = mock_exec.call_args
            assert "[ACTION:FORECAST:Tokyo]" in args[0]
            print("✅ Integration test passed!")
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_test())
