"""
Weather Tool
天気情報取得（簡易実装）
"""
from typing import Dict, Any


async def get_weather(day_index: int = 0) -> Dict[str, Any]:
    """
    天気情報を取得（ダミー実装）
    
    Args:
        day_index: 日数オフセット (0=今日, 1=明日, ...)
    
    Returns:
        {"day": str, "weather": str, "temperature": str}
    """
    # TODO: 実際の天気APIと連携
    days = ["今日", "明日", "明後日"]
    
    return {
        "day": days[day_index] if day_index < len(days) else f"{day_index}日後",
        "weather": "晴れ ☀️",
        "temperature": "最高25°C / 最低18°C",
        "note": "（ダミーデータ）"
    }
