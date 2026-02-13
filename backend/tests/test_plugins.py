import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from app.main import app
import httpx

client = TestClient(app)

# --- Weather Plugin Tests ---

@pytest.mark.asyncio
async def test_weather_plugin_success():
    """天気予報プラグインが正常にデータを返すかテスト"""
    mock_weather_data = {
        "daily": {
            "time": ["2026-02-14", "2026-02-15"],
            "temperature_2m_max": [20.0, 22.0],
            "temperature_2m_min": [10.0, 12.0],
            "weathercode": [0, 1]
        }
    }

    mock_response = httpx.Response(200, json=mock_weather_data)
    mock_response._request = httpx.Request("GET", "http://test") # request属性をセット
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        response = client.get("/api/v1/plugins/weather-clothing/?day_index=0")
        assert response.status_code == 200
        data = response.json()
        assert data["day_label"] == "今日"
        assert data["today"]["max_temp"] == 20.0
        assert "suggestion" in data

@pytest.mark.asyncio
async def test_weather_plugin_day_out_of_range():
    """存在しない日数を指定した場合のエラーハンドリング"""
    mock_weather_data = {
        "daily": {
            "time": ["2026-02-14"],
            "temperature_2m_max": [15.0],
            "temperature_2m_min": [5.0],
            "weathercode": [0]
        }
    }
    
    mock_response = httpx.Response(200, json=mock_weather_data)
    mock_response._request = httpx.Request("GET", "http://test")
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        response = client.get("/api/v1/plugins/weather-clothing/?day_index=5")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert "データがありません" in data["error"]

# --- Notion Plugin Tests ---

@pytest.mark.asyncio
async def test_notion_plugin_success():
    """NotionプラグインがToDoリストを正常に返すかテスト"""
    mock_notion_response = {
        "results": [
            {
                "id": "page-1",
                "url": "https://notion.so/page-1",
                "properties": {
                    "Task name": {"title": [{"text": {"content": "Test Task"}}]},
                    "Status": {"status": {"name": "Not started"}},
                    "Priority": {"select": {"name": "High"}},
                    "Due Date": {"date": {"start": "2026-02-20"}}
                }
            }
        ]
    }

    # 環境変数が設定されていると仮定（またはモック）
    with patch.dict("os.environ", {"NOTION_API_SECRET": "secret", "NOTION_TODO_DATABASE_ID": "db_id"}):
        with patch("httpx.AsyncClient.post", return_value=AsyncMock(status_code=200, json=lambda: mock_notion_response)):
            response = client.get("/api/v1/plugins/notion/todos?status=Not started")
            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["title"] == "Test Task"
            assert data["tasks"][0]["priority"] == "High"

@pytest.mark.asyncio
async def test_notion_plugin_api_error():
    """Notion API エラー時のハンドリング"""
    with patch.dict("os.environ", {"NOTION_API_SECRET": "secret", "NOTION_TODO_DATABASE_ID": "db_id"}):
        with patch("httpx.AsyncClient.post", return_value=AsyncMock(status_code=400, text="Bad Request")):
            response = client.get("/api/v1/plugins/notion/todos")
            assert response.status_code == 200 # エラーメッセージをJSONで返す仕様
            data = response.json()
            assert "error" in data
            assert "Notion API Error" in data["error"]
