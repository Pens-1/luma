"""スケジュール最適化サービスのテスト"""
import pytest
from datetime import datetime

from app.models.schedule import (
    ScheduleRequest,
    Task,
    FixedEvent,
)
from app.services.scheduler import optimize_schedule, ScheduleOptimizer


class TestScheduleOptimizer:
    """ScheduleOptimizerクラスのテスト"""

    def test_empty_tasks(self):
        """タスクがない場合は空のスケジュールを返す"""
        request = ScheduleRequest(
            tasks=[],
            fixed_events=[],
            work_start="09:00",
            work_end="18:00"
        )
        result = optimize_schedule(request)
        
        assert result.status == "success"
        assert len(result.schedule) == 0
        assert result.total_work_minutes == 0

    def test_single_task(self):
        """単一タスクのスケジュール"""
        request = ScheduleRequest(
            tasks=[
                Task(id="task-1", title="テストタスク", priority=1, duration_minutes=60)
            ],
            fixed_events=[],
            work_start="09:00",
            work_end="18:00"
        )
        result = optimize_schedule(request)
        
        assert result.status == "success"
        assert len(result.schedule) == 1
        assert result.schedule[0].task_id == "task-1"
        assert result.total_work_minutes == 60

    def test_multiple_tasks_priority_order(self):
        """優先度順にタスクが配置される"""
        request = ScheduleRequest(
            tasks=[
                Task(id="task-low", title="低優先度", priority=3, duration_minutes=30),
                Task(id="task-high", title="高優先度", priority=1, duration_minutes=30),
                Task(id="task-mid", title="中優先度", priority=2, duration_minutes=30),
            ],
            fixed_events=[],
            work_start="09:00",
            work_end="18:00"
        )
        result = optimize_schedule(request)
        
        assert result.status == "success"
        assert len(result.schedule) == 3
        
        # 優先度の高いタスクが早い時間に配置される
        task_order = [s.task_id for s in result.schedule]
        assert task_order.index("task-high") < task_order.index("task-mid")
        assert task_order.index("task-mid") < task_order.index("task-low")

    def test_avoid_fixed_events(self):
        """確定予定を避けてスケジュール"""
        request = ScheduleRequest(
            tasks=[
                Task(id="task-1", title="タスク1", priority=1, duration_minutes=60),
                Task(id="task-2", title="タスク2", priority=2, duration_minutes=60),
            ],
            fixed_events=[
                FixedEvent(
                    id="event-1",
                    title="会議",
                    start=datetime(2025, 12, 12, 10, 0),
                    end=datetime(2025, 12, 12, 11, 0)
                )
            ],
            work_start="09:00",
            work_end="18:00",
            date="2025-12-12"
        )
        result = optimize_schedule(request)
        
        assert result.status == "success"
        assert len(result.schedule) == 2
        
        # タスクが会議時間と重なっていないことを確認
        for scheduled_task in result.schedule:
            # 10:00-11:00と重なっていないか
            task_start_hour = scheduled_task.start.hour
            task_end_hour = scheduled_task.end.hour
            task_end_minute = scheduled_task.end.minute
            
            # 完全に10:00より前に終わるか、11:00以降に始まる
            is_before = (task_end_hour < 10) or (task_end_hour == 10 and task_end_minute == 0)
            is_after = task_start_hour >= 11
            assert is_before or is_after, f"タスクが会議と重なっています: {scheduled_task}"

    def test_deadline_constraint(self):
        """期限のあるタスクは期限前に配置"""
        request = ScheduleRequest(
            tasks=[
                Task(
                    id="task-urgent",
                    title="緊急タスク",
                    priority=2,
                    duration_minutes=60,
                    deadline=datetime(2025, 12, 12, 12, 0)  # 12:00期限
                ),
            ],
            fixed_events=[],
            work_start="09:00",
            work_end="18:00",
            date="2025-12-12"
        )
        result = optimize_schedule(request)
        
        assert result.status == "success"
        assert len(result.schedule) == 1
        
        # 期限（12:00）より前に終わっていること
        assert result.schedule[0].end.hour <= 12

    def test_insufficient_time(self):
        """時間が足りない場合はfailedを返す"""
        request = ScheduleRequest(
            tasks=[
                Task(id="task-1", title="長いタスク", priority=1, duration_minutes=600),  # 10時間
            ],
            fixed_events=[],
            work_start="09:00",
            work_end="12:00"  # 3時間しかない
        )
        result = optimize_schedule(request)
        
        # 時間が足りないのでスケジュール不可
        assert result.status == "failed"
        assert len(result.unscheduled) == 1

    def test_total_work_minutes_calculation(self):
        """総作業時間が正しく計算される"""
        request = ScheduleRequest(
            tasks=[
                Task(id="task-1", title="タスク1", priority=1, duration_minutes=60),
                Task(id="task-2", title="タスク2", priority=2, duration_minutes=45),
                Task(id="task-3", title="タスク3", priority=3, duration_minutes=30),
            ],
            fixed_events=[],
            work_start="09:00",
            work_end="18:00"
        )
        result = optimize_schedule(request)
        
        assert result.status == "success"
        assert result.total_work_minutes == 60 + 45 + 30  # 135分


class TestScheduleOptimizerHelpers:
    """ヘルパーメソッドのテスト"""

    def test_time_to_minutes(self):
        """時刻文字列を分数に変換"""
        request = ScheduleRequest(
            tasks=[],
            work_start="09:30",
            work_end="18:00"
        )
        optimizer = ScheduleOptimizer(request)
        
        assert optimizer._time_to_minutes("09:00") == 540
        assert optimizer._time_to_minutes("09:30") == 570
        assert optimizer._time_to_minutes("12:00") == 720
        assert optimizer._time_to_minutes("18:00") == 1080
