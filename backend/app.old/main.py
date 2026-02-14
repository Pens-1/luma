"""FastAPI メインアプリケーション

OR-Toolsを使った最適化APIとn8n/Dify連携用エンドポイントを提供。
"""
import importlib
import pkgutil
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.models.schedule import ScheduleRequest, ScheduleResponse
from app.services.scheduler import optimize_schedule
from app import plugins

app = FastAPI(
    title="Luma Optimization API",
    description="OR-Toolsを使ったスケジュール最適化APIと自己進化プラグイン群",
    version="0.2.0",
)

# CORS設定（n8n, Difyからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 自己進化プラグインの動的ロード ---
def load_plugins():
    for loader, module_name, is_pkg in pkgutil.iter_modules(plugins.__path__):
        full_module_name = f"app.plugins.{module_name}"
        module = importlib.import_module(full_module_name)
        if hasattr(module, "router"):
            app.include_router(module.router, prefix="/api/v1/plugins")
            print(f"✅ Loaded plugin: {module_name}")

load_plugins()
# ------------------------------

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Luma Optimization API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "schedule_optimizer": "/api/v1/optimize/schedule"
        }
    }


@app.post("/api/v1/optimize/schedule", response_model=ScheduleResponse)
async def api_optimize_schedule(request: ScheduleRequest):
    """スケジュール最適化エンドポイント
    
    タスクリストと確定予定を受け取り、OR-Toolsで最適なスケジュールを計算します。
    
    - **fixed_events**: Google Calendarから取得した確定予定
    - **tasks**: Notionから取得した未完了タスク（優先度、所要時間、期限付き）
    - **work_start/work_end**: 作業可能な時間帯
    
    Returns:
        最適化されたスケジュールと、スケジュールできなかったタスクのリスト
    """
    try:
        result = optimize_schedule(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"最適化エラー: {str(e)}")

