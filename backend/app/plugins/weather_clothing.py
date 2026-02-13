from fastapi import APIRouter, Query
import httpx
from typing import Optional

router = APIRouter(
    prefix="/weather-clothing",
    tags=["Weather & Clothing"]
)

async def get_weather(lat: float, lon: float):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=Asia%2FTokyo"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

def suggest_clothing(max_temp: float, min_temp: float, weather_code: int) -> str:
    # 簡易的な服装提案ロジック
    advice = ""
    
    if max_temp >= 25:
        advice = "半袖で快適に過ごせます。"
    elif max_temp >= 20:
        advice = "長袖シャツや薄手のカーディガンがおすすめです。"
    elif max_temp >= 15:
        advice = "セーターやトレンチコートが必要な涼しさです。"
    elif max_temp >= 10:
        advice = "冬物のコートや厚手のジャケットを準備しましょう。"
    else:
        advice = "ダウンジャケットやマフラーなど、しっかりした防寒が必要です。"

    if min_temp < 10 and max_temp > 15:
        advice += " 朝晩は冷え込むので、脱ぎ着しやすい上着を持ち歩きましょう。"
        
    if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        advice += " 雨の予報があるため、傘を忘れずに。"
        
    return advice

@router.get("/")
async def get_weather_and_clothing(
    lat: float = Query(35.6895, description="緯度 (デフォルト: 東京)"),
    lon: float = Query(139.6917, description="経度 (デフォルト: 東京)")
):
    """
    指定された場所の天気を取得し、最適な服装を提案します。
    """
    try:
        weather_data = await get_weather(lat, lon)
        daily = weather_data["daily"]
        max_temp = daily["temperature_2m_max"][0]
        min_temp = daily["temperature_2m_min"][0]
        weather_code = daily["weathercode"][0]
        
        advice = suggest_clothing(max_temp, min_temp, weather_code)
        
        return {
            "location": {"lat": lat, "lon": lon},
            "today": {
                "max_temp": max_temp,
                "min_temp": min_temp,
                "weather_code": weather_code
            },
            "suggestion": advice
        }
    except Exception as e:
        return {"error": f"天気情報の取得に失敗しました: {str(e)}"}
