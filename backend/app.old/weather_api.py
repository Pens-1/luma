import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
import os

# Weather API configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/forecast"

async def fetch_weather_data(lat: float, lon: float, days: int = 1) -> Optional[Dict[Any, Any]]:
    """
    天気情報を取得する
    
    Args:
        lat (float): 緯度
        lon (float): 経度
        days (int): 取得する日数 (1-5日まで)
    
    Returns:
        dict: 天気情報の辞書、取得に失敗した場合はNone
    """
    if not WEATHER_API_KEY:
        print("Weather API key is not set")
        return None

    params = {
        'lat': lat,
        'lon': lon,
        'appid': WEATHER_API_KEY,
        'units': 'metric',
        'cnt': days * 8  # 3時間ごとに1回、指定日数分のデータを取得
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Failed to fetch weather data: {response.status}")
                    return None
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def extract_weather_for_notion_task(task: Dict[str, Any], weather_data: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Notionタスクに天気情報を追加する
    
    Args:
        task (dict): Notionタスクデータ
        weather_data (dict): 天気情報
    
    Returns:
        dict: 天気情報を含んだタスクデータ
    """
    if not weather_data or 'list' not in weather_data:
        return task
    
    # 天気情報をタスクに追加
    task_with_weather = task.copy()
    
    # 今日の天気情報を取得
    current_weather = weather_data.get('list', [{}])[0]
    
    if current_weather:
        weather_info = {
            'temperature': current_weather.get('main', {}).get('temp'),
            'description': current_weather.get('weather', [{}])[0].get('description'),
            'humidity': current_weather.get('main', {}).get('humidity'),
            'wind_speed': current_weather.get('wind', {}).get('speed')
        }
        
        task_with_weather['weather'] = weather_info
    
    return task_with_weather

async def get_weather_for_notion_tasks(tasks: list, lat: float, lon: float) -> list:
    """
    Notionタスクリストに天気情報を追加する
    
    Args:
        tasks (list): Notionタスクリスト
        lat (float): 緯度
        lon (float): 経度
    
    Returns:
        list: 天気情報を含んだタスクリスト
    """
    # 天気情報を取得
    weather_data = await fetch_weather_data(lat, lon)
    
    if not weather_data:
        print("Failed to fetch weather data")
        return tasks
    
    # 各タスクに天気情報を追加
    updated_tasks = []
    for task in tasks:
        updated_task = extract_weather_for_notion_task(task, weather_data)
        updated_tasks.append(updated_task)
    
    return updated_tasks

# Example usage
async def main():
    # Example task from Notion
    example_task = {
        "id": "12345",
        "title": "外出する",
        "description": "天気によって服装を変える",
        "due_date": "2023-06-15"
    }
    
    # Example coordinates (Tokyo)
    lat = 35.6895
    lon = 139.6917
    
    # Get weather for the task
    tasks_with_weather = await get_weather_for_notion_tasks([example_task], lat, lon)
    
    print("Task with weather info:", tasks_with_weather)

if __name__ == "__main__":
    asyncio.run(main())
