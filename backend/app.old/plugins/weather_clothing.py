from fastapi import APIRouter, Query
import httpx
from typing import Optional, Dict

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

def suggest_clothing(max_temp: float, min_temp: float, weather_code: int) -> Dict[str, any]:
    advice = ""
    umbrella_needed = False

    # 降雨の天気コードを定義
    rain_weather_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82}
    if weather_code in rain_weather_codes:
        umbrella_needed = True

    # 服装のアドバイスを温度ごとに詳細化
    if max_temp >= 25:
        advice = "半袖、短パン、サンダルで快適に過ごせます。日焼け止めを忘れずに。"
    elif max_temp >= 20:
        advice = "長袖シャツや薄手のカーディガン、ジーンズやスラックスがおすすめです。"
    elif max_temp >= 15:
        advice = "セーター、トレンチコート、長ズボンを着用しましょう。"
    elif max_temp >= 10:
        advice = "厚手のセーター、ダウンジャケット、防風ジャケット、長靴を準備しましょう。"
    else:
        advice = "ダウンジャケット、マフラー、手袋、厚手の靴下、防寒着をしっかり用意しましょう。"

    # 朝晩の温度差がある場合のアドバイス
    if min_temp < 10 and max_temp > 15:
        advice += " 朝晩は冷え込むので、脱ぎ着しやすい上着を持ち歩きましょう。"

    # 降雨がある場合のアドバイス
    if umbrella_needed:
        advice += " 雨の予報があるため、傘を忘れずに。防水素材の服や靴をおすすめします。"

    return {
        "suggestion": advice,
        "umbrella_needed": umbrella_needed
    }

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
        
        clothing_advice = suggest_clothing(max_temp, min_temp, weather_code)
        
        return {
            "date": date,
            "day_label": "今日" if day_index == 0 else "明日" if day_index == 1 else "明後日",
            "today": {
                "max_temp": max_temp,
                "min_temp": min_temp,
                "weather_code": weather_code
            },
            "suggestion": clothing_advice["suggestion"],
            "umbrella_needed": clothing_advice["umbrella_needed"]
        }
    except Exception as e:
        return {"error": f"天気情報の取得に失敗しました: {str(e)}"}
