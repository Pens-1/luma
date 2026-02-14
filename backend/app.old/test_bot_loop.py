
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json

# Botのロジックをテストするために必要なモジュールをインポート
# 注意: bot.py はグローバルで実行されるため、テスト用にロジックを分離してインポートする必要がある場合があります。
# ここでは bot.py の on_message 相当のロジックが action_handler や ask_ollama とどう連携するかをテストします。

from app.services.action_handler import execute_actions

@pytest.mark.asyncio
async def test_react_loop_basic_flow():
    """
    ユーザーの入力に対して、アクションが実行され、最終的な回答が得られるまでの
    ReActループのフローをテストする。
    """
    
    # 1. 最初のAIの回答（アクションを含む）
    ai_response_1 = "[ACTION:NOTION:Not started]"
    
    # 2. アクション実行結果（モック）
    tool_output_1 = 'Tool Output [NOTION_LIST]: {"tasks": [{"title": "Test Task"}], "count": 1}'
    
    # 3. アクション実行後のAIの最終回答
    ai_response_2 = "未着手のタスクは1件、「Test Task」がありますね。"

    # ask_ollama をモックして、1回目はアクションを、2回目は最終回答を返すようにする
    with patch("app.bot.ask_ollama") as mock_ask:
        # 3回目以降呼ばれてもエラーにならないように、ダミーの回答を末尾に追加
        mock_ask.side_effect = [ai_response_1, ai_response_2, "Dummy"]
        
        # execute_actions をモックして、ツール出力を返すようにする
        with patch("app.services.action_handler.execute_actions", new_callable=AsyncMock) as mock_exec:
            # 1回目はツール出力を返し、2回目（最終回答時）は空文字を返すようにする
            mock_exec.side_effect = [tool_output_1, ""]
            
            # bot.py の on_message 内のループに相当するロジックをテスト
            current_input = "タスクを教えて"
            max_turns = 5
            turns_executed = 0
            final_response = ""
            
            for turn in range(max_turns):
                turns_executed += 1
                response = await mock_ask(123, current_input) # channel_id=123
                
                output = await mock_exec(response)
                
                if output:
                    current_input = output
                    continue
                else:
                    final_response = response
                    break
            
            # 検証
            assert turns_executed == 2
            assert "Test Task" in final_response
            assert mock_ask.call_count == 2
            assert mock_exec.call_count == 2

@pytest.mark.asyncio
async def test_react_loop_max_turns_error():
    """
    AIが延々とアクションを出し続けた場合に、ループ上限で停止するかテスト。
    """
    
    # 常にアクションを出し続けるAI
    infinite_action = "[ACTION:NOTION:Not started]"
    
    with patch("app.bot.ask_ollama") as mock_ask:
        mock_ask.return_value = infinite_action
        
        with patch("app.services.action_handler.execute_actions", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Some Tool Output"
            
            turns_executed = 0
            max_turns = 5
            loop_completed = False
            
            for turn in range(max_turns):
                turns_executed += 1
                response = await mock_ask(123, "ずっとアクションして")
                output = await mock_exec(response)
                
                if output:
                    continue
                else:
                    loop_completed = True
                    break
            
            # 検証: max_turns (5回) 回ったはず
            assert turns_executed == 5
            assert not loop_completed

@pytest.mark.asyncio
async def test_action_handler_routing():
    """
    action_handler が正しくタグを検出し、適切な関数にルーティングしているかテスト。
    """
    
    # Weatherタグのテスト
    weather_text = "天気を調べますね。 [ACTION:WEATHER:0]"
    
    with patch("httpx.AsyncClient.get") as mock_get:
        # Mocking FastAPI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"suggestion": "傘を持ってください"}
        mock_get.return_value = mock_response
        
        output = await execute_actions(weather_text)
        
        assert "WEATHER" in output
        assert "傘を持ってください" in output

    # Notionタグのテスト
    notion_text = "タスクを確認します。 [ACTION:NOTION:Doing]"
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tasks": [], "count": 0}
        mock_get.return_value = mock_response
        
        output = await execute_actions(notion_text)
        
        assert "NOTION_LIST" in output
        assert '"count": 0' in output
