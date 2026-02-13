from fastapi import APIRouter, Query
import httpx
from typing import Optional

router = APIRouter(
    prefix="/weather-clothing",
    tags=["Weather & Clothing"]
)

async def get_weather(lat: float, lon: float):
    # 7日分の予報を取得
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=Asia%2FTokyo"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

def suggest_clothing(max_temp: float, min_temp: float, weather_code: int) -> str:
    advice = ""
    if max_temp >= 25: advice = "半袖で快適に過ごせます。"
    elif max_temp >= 20: advice = "長袖シャツや薄手のカーディガンがおすすめです。"
    elif max_temp >= 15: advice = "セーターやトレンチコートが必要な涼しさです。"
    elif max_temp >= 10: advice = "冬物のコートや厚手のジャケットを準備しましょう。"
    else: advice = "ダウンジャケットやマフラーなど、しっかりした防寒が必要です。"

    if min_temp < 10 and max_temp > 15:
        advice += " 朝晩は冷え込むので、脱ぎ着しやすい上着を持ち歩きましょう。"
    if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        advice += " 雨の予報があるため、傘を忘れずに。"
    return advice

@router.get("/")
async def get_weather_and_clothing(
    lat: float = Query(35.6895, description="緯度"),
    lon: float = Query(139.6917, description="経度"),
    day_index: int = Query(0, description="0:今日, 1:明日, 2:明後日")
):
    """
    指定された日(day_index)の天気を取得し、服装を提案します。
    """
    try:
        weather_data = await get_weather(lat, lon)
        daily = weather_data["daily"]
        
        # 指定された日のインデックスが範囲内か確認
        if day_index >= len(daily["temperature_2m_max"]):
            return {"error": "その日の予報データがありません。"}

        max_temp = daily["temperature_2m_max"][day_index]
        min_temp = daily["temperature_2m_min"][day_index]
        weather_code = daily["weathercode"][day_index]
        date = daily["time"][day_index]
        
        advice = suggest_clothing(max_temp, min_temp, weather_code)
        
        return {
            "date": date,
            "day_label": "今日" if day_index == 0 else "明日" if day_index == 1 else "明後日",
            "today": {
                "max_temp": max_temp,
                "min_temp": min_temp,
                "weather_code": weather_code
            },
            "suggestion": advice
        }
    except Exception as e:
        return {"error": f"天気情報の取得に失敗しました: {str(e)}"}
