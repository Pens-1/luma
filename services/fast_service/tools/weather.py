"""
Weather Tool
Open-Meteo APIを使用して天気情報を取得
"""
import httpx
from typing import Dict, Any

# 京都の座標
KYOTO_LAT = 35.0116
KYOTO_LON = 135.7681

async def get_weather(day_index: int = 0) -> Dict[str, Any]:
    """
    指定した日数の天気情報を取得 (デフォルト: 京都)
    
    Args:
        day_index: 日数オフセット (0=今日, 1=明日, ...)
    
    Returns:
        {"day": str, "weather": str, "temperature": str, "note": str}
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": KYOTO_LAT,
            "longitude": KYOTO_LON,
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"],
            "timezone": "Asia/Tokyo",
            "forecast_days": day_index + 1
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        daily = data.get("daily", {})
        if not daily or len(daily.get("time", [])) <= day_index:
             return {"error": "天気情報の取得に失敗しました (日付範囲外)"}

        # WMO Weather interpretation codes (WW)
        # https://open-meteo.com/en/docs
        weather_code = daily["weather_code"][day_index]
        weather_str = parse_weather_code(weather_code)
        
        date_str = daily["time"][day_index]
        max_temp = daily["temperature_2m_max"][day_index]
        min_temp = daily["temperature_2m_min"][day_index]
        
        day_label = "今日" if day_index == 0 else "明日" if day_index == 1 else f"{day_index}日後"

        return {
            "day": f"{day_label} ({date_str})",
            "weather": weather_str,
            "temperature": f"最高 {max_temp}°C / 最低 {min_temp}°C",
            "note": "📍 京都の天気"
        }

    except Exception as e:
        return {"error": f"天気APIエラー: {str(e)}"}


def parse_weather_code(code: int) -> str:
    """WMOコードを文字列に変換"""
    if code == 0: return "快晴 ☀️"
    if code in [1, 2, 3]: return "晴れ時々曇り 🌤️"
    if code in [45, 48]: return "霧 🌫️"
    if code in [51, 53, 55]: return "霧雨 🌧️"
    if code in [61, 63, 65]: return "雨 ☔"
    if code in [71, 73, 75]: return "雪 ☃️"
    if code in [80, 81, 82]: return "にわか雨 ☂️"
    if code in [95, 96, 99]: return "雷雨 ⚡"
    return f"不明 ({code})"
