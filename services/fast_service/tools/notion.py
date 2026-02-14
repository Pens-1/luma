"""
Notion Tool
Notion APIとの連携
"""
import httpx
import os
from typing import Dict, Any, Optional


NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


async def get_tasks(status: str = "Not started") -> Dict[str, Any]:
    """
    Notion データベースからタスクを取得
    
    Args:
        status: ステータス (例: "Not started", "In progress", "Done")
    
    Returns:
        {"tasks": [...], "count": int, "available_statuses": [...]}
    """
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        return {"error": "Notion API Key or Database ID not set"}
    
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    
    # ステータスマッピング（日本語/英語の揺れを吸収）
    status_map = {
        "未着手": "Not started",
        "進行中": "In progress",
        "提出": "Done",  # ユーザー運用に合わせる
        "完了": "Done"
    }
    
    # 全タスクを取得（ページネーション対応）
    all_tasks = []
    next_cursor = None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            payload = {}
            if next_cursor:
                payload["start_cursor"] = next_cursor
            
            try:
                response = await client.post(url, headers=HEADERS, json=payload)
                if response.status_code != 200:
                    return {"error": f"Notion API Error: {response.text}"}
                
                data = response.json()
                results = data.get("results", [])
                
                # タスク抽出
                for page in results:
                    props = page["properties"]
                    title, item_status, priority, due_date = "Untitled", "Unknown", "Medium", None
                    
                    for key, prop in props.items():
                        p_type = prop.get("type")
                        
                        if p_type == "title":
                            title = prop["title"][0]["text"]["content"] if prop["title"] else "(No Title)"
                        elif p_type == "status":
                            item_status = prop["status"]["name"] if prop["status"] else "Unknown"
                        elif p_type == "select":
                            if "status" in key.lower() or "ステータス" in key:
                                item_status = prop["select"]["name"] if prop["select"] else "Unknown"
                            elif "priority" in key.lower() or "優先" in key:
                                priority = prop["select"]["name"] if prop["select"] else "Medium"
                        elif p_type == "date":
                            due_date = prop["date"]["start"] if prop["date"] else None
                    
                    all_tasks.append({
                        "id": page["id"],
                        "title": title,
                        "status": item_status,
                        "priority": priority,
                        "due_date": due_date,
                        "url": page["url"]
                    })
                
                # 次のページがあるか確認
                if data.get("has_more"):
                    next_cursor = data.get("next_cursor")
                else:
                    break
            
            except Exception as e:
                return {"error": f"Connection Error: {str(e)}"}
    
    # フィルタリング
    def match_status(target, query):
        if query.lower() in ["all", "すべて", "全部"]:
            return True
        q = query.lower()
        t = target.lower()
        if q == t:
            return True
        # マッピング考慮
        if status_map.get(query, "").lower() == t:
            return True
        for k, v in status_map.items():
            if v.lower() == q and k.lower() == t:
                return True
        return False
    
    filtered_tasks = [t for t in all_tasks if match_status(t["status"], status)]
    available_statuses = list(set(t["status"] for t in all_tasks))
    
    return {
        "tasks": filtered_tasks,
        "count": len(filtered_tasks),
        "total_in_db": len(all_tasks),
        "available_statuses": available_statuses
    }


async def create_task(title: str, due_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Notionにタスクを作成
    
    Args:
        title: タスク名
        due_date: 期限 (YYYY-MM-DD形式)
    
    Returns:
        {"id": str, "url": str, "title": str}
    """
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        return {"error": "Notion API Key or Database ID not set"}
    
    url = "https://api.notion.com/v1/pages"
    
    properties = {
        "Name": {
            "title": [{"text": {"content": title}}]
        }
    }
    
    if due_date:
        properties["Due Date"] = {
            "date": {"start": due_date}
        }
    
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(url, headers=HEADERS, json=payload)
            
            if response.status_code != 200:
                return {"error": f"Notion API Error: {response.text}"}
            
            data = response.json()
            return {
                "id": data["id"],
                "url": data["url"],
                "title": title,
                "due_date": due_date
            }
        
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}
