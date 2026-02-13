"""OR-Toolsを使ったスケジュール最適化サービス"""
from datetime import datetime, timedelta
from typing import Optional

from ortools.sat.python import cp_model

from app.models.schedule import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduledTask,
    UnscheduledTask,
    Task,
    FixedEvent,
)


class ScheduleOptimizer:
    """CP-SATソルバーを使ったスケジュール最適化
    
    タスクを時間スロットに割り当て、以下を最適化:
    - 優先度の高いタスクを早い時間に配置
    - 期限のあるタスクを期限前に完了
    - 確定予定との衝突を回避
    """
    
    # 時間スロットの粒度（分）
    SLOT_DURATION = 15
    
    def __init__(self, request: ScheduleRequest):
        self.request = request
        self.date = self._parse_date()
        self.work_start_minutes = self._time_to_minutes(request.work_start)
        self.work_end_minutes = self._time_to_minutes(request.work_end)
        self.total_slots = (self.work_end_minutes - self.work_start_minutes) // self.SLOT_DURATION
        
    def _parse_date(self) -> datetime:
        """対象日を解析"""
        if self.request.date:
            return datetime.strptime(self.request.date, "%Y-%m-%d")
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _time_to_minutes(self, time_str: str) -> int:
        """HH:MM形式を0時からの分数に変換"""
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    
    def _minutes_to_datetime(self, minutes: int) -> datetime:
        """分数をdatetimeに変換"""
        return self.date + timedelta(minutes=minutes)
    
    def _get_blocked_slots(self) -> set[int]:
        """確定予定でブロックされているスロットを取得"""
        blocked = set()
        
        for event in self.request.fixed_events:
            event_start = event.start.hour * 60 + event.start.minute
            event_end = event.end.hour * 60 + event.end.minute
            
            # スロットインデックスに変換
            start_slot = max(0, (event_start - self.work_start_minutes) // self.SLOT_DURATION)
            end_slot = min(self.total_slots, (event_end - self.work_start_minutes + self.SLOT_DURATION - 1) // self.SLOT_DURATION)
            
            for slot in range(start_slot, end_slot):
                blocked.add(slot)
        
        return blocked
    
    def _get_deadline_slot(self, task: Task) -> Optional[int]:
        """タスクの期限スロットを取得"""
        if task.deadline is None:
            return None
        
        # 期限が今日より前なら最優先
        if task.deadline.date() < self.date.date():
            return 0
        
        # 期限が今日なら、その時刻のスロット
        if task.deadline.date() == self.date.date():
            deadline_minutes = task.deadline.hour * 60 + task.deadline.minute
            return max(0, (deadline_minutes - self.work_start_minutes) // self.SLOT_DURATION)
        
        # 期限が明日以降なら制約なし
        return None
    
    def optimize(self) -> ScheduleResponse:
        """スケジュールを最適化"""
        model = cp_model.CpModel()
        
        blocked_slots = self._get_blocked_slots()
        tasks = self.request.tasks
        
        if not tasks:
            return ScheduleResponse(
                status="success",
                schedule=[],
                unscheduled=[],
                summary="スケジュールするタスクがありません",
                total_work_minutes=0
            )
        
        # 各タスクの開始スロット変数
        task_starts = {}
        task_ends = {}
        task_slots_needed = {}
        
        for task in tasks:
            slots_needed = (task.duration_minutes + self.SLOT_DURATION - 1) // self.SLOT_DURATION
            task_slots_needed[task.id] = slots_needed
            
            # 開始スロット（0からtotal_slots - slots_neededまで）
            max_start = max(0, self.total_slots - slots_needed)
            task_starts[task.id] = model.NewIntVar(0, max_start, f"start_{task.id}")
            task_ends[task.id] = model.NewIntVar(slots_needed, self.total_slots, f"end_{task.id}")
            
            # end = start + slots_needed
            model.Add(task_ends[task.id] == task_starts[task.id] + slots_needed)
        
        # 制約1: タスク同士が重ならない
        for i, task1 in enumerate(tasks):
            for task2 in tasks[i+1:]:
                # task1がtask2の前に終わる OR task2がtask1の前に終わる
                b = model.NewBoolVar(f"order_{task1.id}_{task2.id}")
                model.Add(task_ends[task1.id] <= task_starts[task2.id]).OnlyEnforceIf(b)
                model.Add(task_ends[task2.id] <= task_starts[task1.id]).OnlyEnforceIf(b.Not())
        
        # 制約2: 確定予定と重ならない
        for task in tasks:
            slots_needed = task_slots_needed[task.id]
            for blocked_slot in blocked_slots:
                # タスクがblocked_slotを使わないようにする
                # start > blocked_slot OR end <= blocked_slot
                b = model.NewBoolVar(f"avoid_{task.id}_{blocked_slot}")
                model.Add(task_starts[task.id] > blocked_slot).OnlyEnforceIf(b)
                model.Add(task_ends[task.id] <= blocked_slot).OnlyEnforceIf(b.Not())
        
        # 制約3: 期限のあるタスクは期限前に完了
        for task in tasks:
            deadline_slot = self._get_deadline_slot(task)
            if deadline_slot is not None:
                model.Add(task_ends[task.id] <= deadline_slot)
        
        # 目的関数: 優先度の高いタスクを早く配置
        # priority 1 = 重み3, priority 2 = 重み2, priority 3 = 重み1
        objective_terms = []
        for task in tasks:
            weight = 4 - task.priority  # priority 1 -> 3, priority 2 -> 2, priority 3 -> 1
            objective_terms.append(weight * task_starts[task.id])
        
        model.Minimize(sum(objective_terms))
        
        # ソルバー実行
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        status = solver.Solve(model)
        
        # 結果を構築
        scheduled = []
        unscheduled = []
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for task in tasks:
                start_slot = solver.Value(task_starts[task.id])
                end_slot = solver.Value(task_ends[task.id])
                
                start_minutes = self.work_start_minutes + start_slot * self.SLOT_DURATION
                end_minutes = self.work_start_minutes + end_slot * self.SLOT_DURATION
                
                scheduled.append(ScheduledTask(
                    task_id=task.id,
                    title=task.title,
                    start=self._minutes_to_datetime(start_minutes),
                    end=self._minutes_to_datetime(end_minutes),
                    priority=task.priority
                ))
            
            # 開始時刻でソート
            scheduled.sort(key=lambda x: x.start)
            
            total_work = sum(task.duration_minutes for task in tasks)
            
            return ScheduleResponse(
                status="success",
                schedule=scheduled,
                unscheduled=unscheduled,
                summary=f"{len(scheduled)}件のタスクを配置しました（総作業時間: {total_work}分）",
                total_work_minutes=total_work
            )
        else:
            # スケジュール不可能な場合
            for task in tasks:
                unscheduled.append(UnscheduledTask(
                    task_id=task.id,
                    title=task.title,
                    reason="時間枠が不足しているか、制約を満たせません"
                ))
            
            return ScheduleResponse(
                status="failed",
                schedule=[],
                unscheduled=unscheduled,
                summary="スケジュールを作成できませんでした。タスクを減らすか、作業時間を延長してください。",
                total_work_minutes=0
            )


def optimize_schedule(request: ScheduleRequest) -> ScheduleResponse:
    """スケジュール最適化のエントリーポイント"""
    optimizer = ScheduleOptimizer(request)
    return optimizer.optimize()
