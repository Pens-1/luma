"""
Notion Tool
Notion APIとの連携
"""
import httpx
import os
import sys
from typing import Dict, Any, Optional


# 環境変数を優先、なければエラー
NOTION_API_KEY = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_API_SECRET")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID") or os.getenv("NOTION_TODO_DATABASE_ID")

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    print("❌ Notion API Key or Database ID not set!")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


async def validate_api_token(api_key: str) -> bool:
    """
    Validate the Notion API token.
    """
    try:
        if not api_key:
            return False
        
        url = "https://api.notion.com/v1/users/me"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url, 
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Notion-Version": "2022-06-28"
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Notion API Error: {response.status_code} - {response.text}")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Error validating API token: {e}")
        return False


async def get_tasks(status: str) -> Dict[str, Any]:
    """
    指定されたステータスのタスクを取得
    """
    if not await validate_api_token(NOTION_API_KEY):
        return {"error": "Invalid Notion API Key. Check .env file."}

    print(f"DEBUG: Querying Notion DB: {NOTION_DATABASE_ID}")
    
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    
    # フィルタリング条件を追加
    payload = {
        "filter": {
            "property": "Status",
            "select": {
                "equals": "In Progress"
            }
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=HEADERS, json=payload)
            
            if response.status_code != 200:
                print(f"❌ Notion API Error: {response.status_code} - {response.text}")
                return {"error": f"Notion API Error: {response.text}"}
            
            data = response.json()
            results = data.get("results", [])
            
            all_tasks = []
            for page in results:
                props = page["properties"]
                
                # タイトル取得
                title_prop = props.get("Name") or props.get("Task") or props.get("Title") or props.get("名前")
                if title_prop and title_prop["title"]:
                    title = title_prop["title"][0]["text"]["content"]
                else:
                    title = "(No Title)"
                
                # ステータス取得
                status_prop = props.get("Status") or props.get("State") or props.get("ステータス")
                item_status = "Unknown"
                if status_prop:
                    if status_prop["type"] == "status":
                        item_status = status_prop["status"]["name"]
                    elif status_prop["type"] == "select":
                        item_status = status_prop["select"]["name"] if status_prop["select"] else "None"

                all_tasks.append({
                    "id": page["id"],
                    "title": title,
                    "status": item_status,
                    "url": page["url"]
                })
            
            # 部分一致フィルタリング
            filtered_tasks = []
            if status.lower() in ["all", "すべて", "一覧"]:
                filtered_tasks = all_tasks
            else:
                for t in all_tasks:
                    if status.lower() in t["status"].lower() or t["status"].lower() in status.lower():
                        filtered_tasks.append(t)
            
            return {
                "tasks": filtered_tasks,
                "count": len(filtered_tasks),
                "debug_total": len(all_tasks)
            }

    except Exception as e:
        print(f"❌ Notion Connection Error: {e}")
        return {"error": str(e)}


async def create_task(title: str, due_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Notionにタスクを作成
    """
    if not await validate_api_token(NOTION_API_KEY):
        return {"error": "Invalid Notion API Key. Check .env file."}
    
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
