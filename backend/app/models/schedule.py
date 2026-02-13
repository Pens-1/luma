"""スケジュール最適化のPydanticモデル定義"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    """Notionから取得するタスク"""
    id: str = Field(..., description="タスクID")
    title: str = Field(..., description="タスクタイトル")
    priority: int = Field(default=2, ge=1, le=3, description="優先度 (1=高, 2=中, 3=低)")
    duration_minutes: int = Field(..., ge=5, description="所要時間（分）")
    deadline: Optional[datetime] = Field(default=None, description="期限")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "task-1",
                "title": "設計レビュー",
                "priority": 1,
                "duration_minutes": 60,
                "deadline": "2024-12-12T18:00:00"
            }
        }


class FixedEvent(BaseModel):
    """Google Calendarから取得する確定予定"""
    id: str = Field(..., description="イベントID")
    title: str = Field(..., description="イベントタイトル")
    start: datetime = Field(..., description="開始時刻")
    end: datetime = Field(..., description="終了時刻")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "event-1",
                "title": "定例ミーティング",
                "start": "2024-12-12T10:00:00",
                "end": "2024-12-12T11:00:00"
            }
        }


class ScheduleRequest(BaseModel):
    """スケジュール最適化リクエスト"""
    fixed_events: list[FixedEvent] = Field(default=[], description="確定済みの予定（GCalから）")
    tasks: list[Task] = Field(..., description="スケジュールするタスク（Notionから）")
    work_start: str = Field(default="09:00", description="作業開始時刻 (HH:MM)")
    work_end: str = Field(default="22:00", description="作業終了時刻 (HH:MM)")
    date: Optional[str] = Field(default=None, description="対象日 (YYYY-MM-DD)、省略時は今日")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fixed_events": [
                    {"id": "event-1", "title": "定例MTG", "start": "2024-12-12T10:00:00", "end": "2024-12-12T11:00:00"}
                ],
                "tasks": [
                    {"id": "task-1", "title": "設計レビュー", "priority": 1, "duration_minutes": 60},
                    {"id": "task-2", "title": "コードレビュー", "priority": 2, "duration_minutes": 30}
                ],
                "work_start": "09:00",
                "work_end": "22:00"
            }
        }


class ScheduledTask(BaseModel):
    """スケジュールされたタスク"""
    task_id: str
    title: str
    start: datetime
    end: datetime
    priority: int


class UnscheduledTask(BaseModel):
    """スケジュールできなかったタスク"""
    task_id: str
    title: str
    reason: str


class ScheduleResponse(BaseModel):
    """スケジュール最適化レスポンス"""
    status: str = Field(..., description="success または partial")
    schedule: list[ScheduledTask] = Field(..., description="スケジュールされたタスク")
    unscheduled: list[UnscheduledTask] = Field(default=[], description="スケジュールできなかったタスク")
    summary: str = Field(..., description="結果サマリー")
    total_work_minutes: int = Field(..., description="総作業時間（分）")
