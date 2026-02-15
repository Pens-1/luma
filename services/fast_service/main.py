"""
Fast Service - Tools API
ツール実行機能を提供するAPIサーバー
"""
import sys
import os
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 共有ライブラリをインポート
if os.path.exists("/app/shared"):
    sys.path.append("/app/shared")
else:
    shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared"))
    sys.path.append(shared_path)

from utils import format_result

# Fast Service固有のモジュール
from tools import weather, forecast, janken, omikuji
# from tools import notion  # Disabled

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API モデル定義
class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class ToolExecutionRequest(BaseModel):
    parameters: Dict[str, Any]

class ToolExecutionResponse(BaseModel):
    result: Any
    status: str = "success"
    error: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    print("🚀 Tools API starting...")
    yield
    # 終了時
    print("👋 Tools API stopping...")

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "service": "luma-tools-api"}


@app.get("/tools", response_model=List[ToolInfo])
async def get_tools():
    """利用可能なツール一覧を返す"""
    # 将来的にはツールクラスから動的に生成する
    return [
        ToolInfo(
            name="weather",
            description="指定した日数の天気を取得 (デフォルト: 京都)",
            parameters={"day_index": "int (0=今日, 1=明日...)"}
        ),
        ToolInfo(
            name="forecast",
            description="指定した都市の詳細な天気予報を取得",
            parameters={"city": "str (English city name)"}
        ),
        ToolInfo(
            name="janken",
            description="じゃんけんをする (グー, チョキ, パー)",
            parameters={"user_hand": "str (グー/チョキ/パー)"}
        ),
        ToolInfo(
            name="omikuji",
            description="おみくじを引く (今日の運勢)",
            parameters={}
        ),
        # Notion is disabled
    ]


@app.post("/tools/{tool_name}", response_model=ToolExecutionResponse)
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """
    指定されたツールを実行する
    """
    logger.info(f"🔧 Executing tool: {tool_name} with params: {request.parameters}")
    
    try:
        result = None
        
        if tool_name == "weather":
            day_index = request.parameters.get("day_index", 0)
            result = await weather.get_weather(day_index)
            
        elif tool_name == "forecast":
            city = request.parameters.get("city")
            if not city:
                raise HTTPException(status_code=400, detail="Missing 'city' parameter")
            result = forecast.get_forecast(city)
            
        elif tool_name == "janken":
            user_hand = request.parameters.get("user_hand")
            if not user_hand:
                raise HTTPException(status_code=400, detail="Missing 'user_hand' parameter")
            result = await janken.play_janken(user_hand)

        elif tool_name == "omikuji":
             result = await omikuji.run()

        elif tool_name == "notion":
             raise HTTPException(status_code=503, detail="Notion tool is currently disabled")
             
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # エラー判定（ツール内部からの戻り値に含まれる場合）
        if isinstance(result, dict) and "error" in result:
             return ToolExecutionResponse(result=result, status="error", error=result["error"])

        return ToolExecutionResponse(result=result)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return ToolExecutionResponse(result=None, status="error", error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
