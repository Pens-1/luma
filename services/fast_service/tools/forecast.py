import requests
from datetime import datetime

def get_forecast(city: str):
    """
    Open-Meteo APIを使用して3日間の天気予報を取得する
    APIキー不要
    """
    # 都市名から座標を取得（簡易マップ）
    locations = {
        "Tokyo": {"lat": 35.6895, "lon": 139.6917},
        "Osaka": {"lat": 34.6937, "lon": 135.5023},
        "Nagoya": {"lat": 35.1815, "lon": 136.9066},
        "Fukuoka": {"lat": 33.5904, "lon": 130.4017},
        "Sapporo": {"lat": 43.0611, "lon": 141.3465},
        "London": {"lat": 51.5074, "lon": -0.1278},
        "New York": {"lat": 40.7128, "lon": -74.0060},
    }

    loc = locations.get(city)
    if not loc:
        # 見つからない場合は東京をデフォルトにせずエラーを返すか、
        # あるいは本来はGeocoding APIを使うべきだが、今回はモック的にTokyoを返す
        if city.lower() == "tokyo":
            loc = locations["Tokyo"]
        else:
            return {"error": f"City '{city}' not supported in this prototype."}

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&daily=temperature_2m_max,weathercode&timezone=auto"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        forecast_list = []
        for i in range(3):
            date_str = data["daily"]["time"][i]
            temp_max = data["daily"]["temperature_2m_max"][i]
            code = data["daily"]["weathercode"][i]
            
            forecast_list.append({
                "date": date_str,
                "temperature": temp_max,
                "weathercode": code
            })

        return {
            "city": city,
            "forecast": forecast_list
        }
    except Exception as e:
        return {"error": str(e)}
