"""
共通ユーティリティ関数
"""
import json
from typing import Any, Dict


def truncate_text(text: str, max_length: int = 1000) -> str:
    """テキストを指定長に切り詰め"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_result(result: Dict[str, Any], max_tasks: int = 10) -> str:
    """実行結果を人間が読みやすい形式に整形"""
    if "error" in result:
        return f"❌ エラー: {result['error']}"
    
    if "tasks" in result:
        tasks = result["tasks"]
        count = result.get("count", len(tasks))
        
        if count == 0:
            return "タスクは0件です。"
        
        lines = [f"タスクは{count}件あります:"]
        for i, task in enumerate(tasks[:max_tasks], 1):
            title = task.get("title", "Untitled")
            status = task.get("status", "Unknown")
            lines.append(f"{i}. {title} ({status})")
        
        if count > max_tasks:
            lines.append(f"... 他{count - max_tasks}件")
        
        return "\n".join(lines)
    
    # デフォルト: JSON文字列
    return json.dumps(result, ensure_ascii=False, indent=2)


def detect_complaint(text: str) -> bool:
    """ユーザーの不満を検知"""
    complaint_keywords = [
        "おかしい", "違う", "間違", "バグ", "動かない",
        "ない", "できない", "エラー", "失敗"
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in complaint_keywords)
