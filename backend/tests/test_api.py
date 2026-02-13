"""FastAPI エンドポイントのテスト"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_check(self):
        """ヘルスチェックが正常に動作"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRootEndpoint:
    """ルートエンドポイントのテスト"""

    def test_root(self):
        """ルートエンドポイントが情報を返す"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "endpoints" in data


class TestScheduleOptimizeEndpoint:
    """スケジュール最適化エンドポイントのテスト"""

    def test_optimize_empty_tasks(self):
        """空のタスクリストでも正常に動作"""
        response = client.post(
            "/api/v1/optimize/schedule",
            json={
                "tasks": [],
                "fixed_events": [],
                "work_start": "09:00",
                "work_end": "18:00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["schedule"]) == 0

    def test_optimize_single_task(self):
        """単一タスクの最適化"""
        response = client.post(
            "/api/v1/optimize/schedule",
            json={
                "tasks": [
                    {
                        "id": "task-1",
                        "title": "テストタスク",
                        "priority": 1,
                        "duration_minutes": 60
                    }
                ],
                "fixed_events": [],
                "work_start": "09:00",
                "work_end": "18:00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["schedule"]) == 1
        assert data["total_work_minutes"] == 60

    def test_optimize_with_fixed_events(self):
        """確定予定を考慮した最適化"""
        response = client.post(
            "/api/v1/optimize/schedule",
            json={
                "tasks": [
                    {
                        "id": "task-1",
                        "title": "タスク1",
                        "priority": 1,
                        "duration_minutes": 60
                    },
                    {
                        "id": "task-2",
                        "title": "タスク2",
                        "priority": 2,
                        "duration_minutes": 30
                    }
                ],
                "fixed_events": [
                    {
                        "id": "event-1",
                        "title": "会議",
                        "start": "2025-12-12T10:00:00",
                        "end": "2025-12-12T11:00:00"
                    }
                ],
                "work_start": "09:00",
                "work_end": "18:00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["schedule"]) == 2

    def test_optimize_invalid_request(self):
        """不正なリクエストでバリデーションエラー"""
        response = client.post(
            "/api/v1/optimize/schedule",
            json={
                "tasks": [
                    {
                        "id": "task-1",
                        # titleが欠けている
                        "priority": 1,
                        "duration_minutes": 60
                    }
                ]
            }
        )
        assert response.status_code == 422  # Validation Error

    def test_optimize_priority_order(self):
        """優先度順に配置される"""
        response = client.post(
            "/api/v1/optimize/schedule",
            json={
                "tasks": [
                    {"id": "low", "title": "低", "priority": 3, "duration_minutes": 30},
                    {"id": "high", "title": "高", "priority": 1, "duration_minutes": 30},
                    {"id": "mid", "title": "中", "priority": 2, "duration_minutes": 30},
                ],
                "fixed_events": [],
                "work_start": "09:00",
                "work_end": "18:00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # スケジュールを取得して順序を確認
        schedule = data["schedule"]
        task_ids = [s["task_id"] for s in schedule]
        
        # 高優先度が最初に配置されている
        assert task_ids.index("high") < task_ids.index("mid")
        assert task_ids.index("mid") < task_ids.index("low")
