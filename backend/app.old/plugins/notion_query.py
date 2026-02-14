from fastapi import APIRouter, Query, HTTPException
import httpx
import os
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/notion",
    tags=["Notion Integration"]
)

NOTION_API_KEY = os.getenv("NOTION_API_SECRET")
DATABASE_ID = os.getenv("NOTION_TODO_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

@router.get("/todos")
async def get_todos(status: str = Query("Not started", description="タスクのステータス")):
    """
    Notionデータベースからタスクを取得します。
    """
    if not NOTION_API_KEY or not DATABASE_ID:
        raise HTTPException(status_code=500, detail="Notion API Key or Database ID not set.")

    # ステータス名のマッピング（日本語/英語の揺れを吸収）
    status_map = {
        "未着手": "Not started",
        "進行中": "In progress",
        "提出": "In progress",  # ユーザーの運用に合わせて「提出」を「進行中」とみなす
        "完了": "Done",
        "TODO": "Not started",
        "DOING": "In progress",
        "DONE": "Done"
    }
    normalized_status = status_map.get(status, status)

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # ページネーションを使用して全タスクを取得
    all_tasks = []
    next_cursor = None
    
    while True:
        # ページネーション用のペイロード
        payload = {}
        if next_cursor:
            payload["page_size"] = 100
            payload["start_cursor"] = next_cursor
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=HEADERS, json=payload)
                if response.status_code != 200:
                    return {"error": f"Notion API Error: {response.text}"}
                
                data = response.json()
                results = data.get("results", [])
                
                # タスクを抽出
                for page in results:
                    props = page["properties"]
                    # ... (既存の抽出ロジック)
                    title, item_status, priority, due_date = "Untitled", "Unknown", "Medium", None

                    for key, prop in props.items():
                        p_type = prop.get("type")
                        if p_type == "title":
                            title = prop["title"][0]["text"]["content"] if prop["title"] else "(No Title)"
                        elif p_type == "status":
                            item_status = prop["status"]["name"] if prop["status"] else "Unknown"
                        elif p_type == "select":
                            # Statusがselect型で実装されているケースへの対応
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

    # アプリケーション側でフィルタリング（マッピングを考慮）
    def match_status(target, query):
        if query.lower() in ["all", "すべて", "全部", "any"]:
            return True
        q = query.lower()
        t = target.lower()
        if q == t: return True
        # マッピングによる一致
        if status_map.get(query, "").lower() == t: return True
        # 逆引き
        for k, v in status_map.items():
            if v.lower() == q and k.lower() == t: return True
        return False

    filtered_tasks = [t for t in all_tasks if match_status(t["status"], status)]
    
    # 指定されたステータスがない場合、全てのタスクのステータス一覧をヒントとして返す
    status_list = list(set(t["status"] for t in all_tasks))

    return {
        "tasks": filtered_tasks, 
        "count": len(filtered_tasks),
        "available_statuses": status_list,
        "note": f"Filtered by '{status}'. Total tasks in DB: {len(all_tasks)}"
    }

@router.post("/todos")
async def create_todo(title: str, due_date: Optional[str] = None):
    """
    Notionデータベースに新しいタスクを作成します。
    """
    if not NOTION_API_KEY or not DATABASE_ID:
        raise HTTPException(status_code=500, detail="Notion API Key or Database ID not set.")

    url = "https://api.notion.com/v1/pages"
    
    # 基本的なプロパティ構造
    properties = {
        "Name": {  # データベースのタイトルプロパティ名は環境によるが、一般的には "Name" か "Title"
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        }
    }
    
    # 期日が指定されている場合、適切なプロパティに追加
    if due_date:
        # Notionの日付プロパティ名はデータベースによって異なる可能性があるため、
        # 一般的な名前を試す
        properties["Due Date"] = {
            "date": {
                "start": due_date
            }
        }

    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": properties
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=HEADERS, json=payload)
            
            if response.status_code != 200:
                return {"error": f"Notion API Error: {response.text}"}
            
            data = response.json()
            return {
                "message": "Task created successfully",
                "id": data["id"],
                "url": data["url"],
                "title": title,
                "due_date": due_date
            }

        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}
