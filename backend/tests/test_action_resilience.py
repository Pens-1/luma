
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.action_handler import execute_actions

@pytest.mark.asyncio
async def test_multiple_actions_in_single_response():
    """
    AIが1回の発言で複数のアクション（例：Notionタスク作成x2）を要求した場合、
    すべてが実行されることを検証する。
    """
    text = "[ACTION:NOTION_CREATE:タスク1][ACTION:NOTION_CREATE:タスク2:2026-02-15]"
    
    with patch("httpx.AsyncClient.post") as mock_post:
        # Mock responses for two calls
        mock_res1 = MagicMock()
        mock_res1.status_code = 200
        mock_res1.json.return_value = {"title": "タスク1", "url": "http://url1"}
        
        mock_res2 = MagicMock()
        mock_res2.status_code = 200
        mock_res2.json.return_value = {"title": "タスク2", "url": "http://url2"}
        
        mock_post.side_effect = [mock_res1, mock_res2]
        
        output = await execute_actions(text)
        
        # 検証: 2つのタスク作成結果が含まれていること
        assert "タスク1" in output
        assert "タスク2" in output
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_unsupported_action_tag_graceful_handling():
    """
    未定義のアクションタグが含まれていた場合、クラッシュせずに無視、
    あるいは適切なメッセージを返すことを検証する。
    """
    text = "未知のタグです [ACTION:UNKNOWN:DATA]"
    output = await execute_actions(text)
    
    # 現状の実装では空文字が返るはず（あるいはエラーにならない）
    assert "UNKNOWN" not in output

@pytest.mark.asyncio
async def test_api_timeout_handling():
    """
    外部APIがタイムアウトした場合に、適切なエラーログを返すことを検証する。
    """
    text = "[ACTION:WEATHER:0]"
    
    # タイムアウトをシミュレート
    with patch("httpx.AsyncClient.get", side_effect=asyncio.TimeoutError()):
        output = await execute_actions(text)
        
        # 検証: タイムアウトエラーが含まれていること
        assert "WEATHER" in output
        assert "Failed" in output

@pytest.mark.asyncio
async def test_invalid_json_response_handling():
    """
    APIが壊れたJSONを返してきた場合に、適切にエラーハンドリングされることを検証する。
    """
    text = "[ACTION:NOTION:Not started]"
    
    # 不正なJSONレスポンス
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    
    with patch("httpx.AsyncClient.get", return_value=mock_res):
        output = await execute_actions(text)
        assert "NOTION_LIST" in output
        assert "Failed" in output or "Error" in output

@pytest.mark.asyncio
async def test_mixed_multiple_actions_handling():
    """
    異なる種類のアクション（天気 + Notion作成）が混在していても
    すべて漏れなく実行されることを検証する。
    """
    text = "かしこまりました。まずは天気を確認します。[ACTION:WEATHER:0] その後、タスクを登録しますね。[ACTION:NOTION_CREATE:雨の日タスク]"
    
    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("httpx.AsyncClient.post") as mock_post:
        
        # Weather Mock
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"suggestion": "傘"})
        # Notion Mock
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"title": "雨の日タスク", "url": "http://notion"})
        
        output = await execute_actions(text)
        
        # 両方の結果が含まれているか
        assert "Tool Output [WEATHER]" in output
        assert "Tool Output [NOTION_CREATE]" in output
        assert "雨の日タスク" in output
        assert mock_get.call_count == 1
        assert mock_post.call_count == 1
