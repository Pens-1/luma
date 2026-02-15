import sys
import os
import pytest

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import forecast

def test_get_forecast_tokyo():
    """東京の予報が正しく取得できるかテスト"""
    result = forecast.get_forecast("Tokyo")
    assert "city" in result
    assert result["city"] == "Tokyo"
    assert "forecast" in result
    assert len(result["forecast"]) == 3
    assert "temperature" in result["forecast"][0]

def test_get_forecast_invalid_city():
    """未対応の都市でエラーが返るかテスト"""
    result = forecast.get_forecast("UnknownCity")
    assert "error" in result
    assert "not supported" in result["error"]
