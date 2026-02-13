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

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    payload = {
        "filter": {
            "property": "Status",
            "status": {
                "equals": status
            }
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=HEADERS, json=payload)
            if response.status_code != 200:
                return {"error": f"Notion API Error: {response.text}"}
            
            data = response.json()
            tasks = []
            
            for page in data.get("results", []):
                props = page["properties"]
                
                # タイトルの取得（適宜プロパティ名を調整してください）
                title_prop = props.get("Name") or props.get("Title") or props.get("Task name") or props.get("名前")
                title = "Untitled"
                if title_prop and title_prop["title"]:
                    title = title_prop["title"][0]["text"]["content"]
                
                # 期限
                due_date = None
                if props.get("Due Date") and props["Due Date"]["date"]:
                    due_date = props["Due Date"]["date"]["start"]

                # 優先度
                priority = "Medium"
                if props.get("Priority") and props["Priority"]["select"]:
                    priority = props["Priority"]["select"]["name"]

                tasks.append({
                    "id": page["id"],
                    "title": title,
                    "status": status,
                    "priority": priority,
                    "due_date": due_date,
                    "url": page["url"]
                })
                
            return {"tasks": tasks, "count": len(tasks)}

        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

@router.post("/todos")
async def create_todo(title: str, due_date: Optional[str] = None):
    """
    Notionデータベースに新しいタスクを作成します。
    """
    if not NOTION_API_KEY or not DATABASE_ID:
        raise HTTPException(status_code=500, detail="Notion API Key or Database ID not set.")

    url = "https://api.notion.com/v1/pages"
    
    properties = {
        "Name": { # データベースのタイトルプロパティ名は環境によるが、一般的には "Name" か "Title"
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        }
        # "Status" プロパティは存在しないエラーが出るため削除
    }

    # "Due Date" プロパティも特定できないため、まずはタイトルのみで作成する
    # if due_date:
    #     properties["Due Date"] = { ... }

    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": properties
    }

    async with httpx.AsyncClient() as client:
        try:
            # まずは標準的なプロパティ名でトライ
            response = await client.post(url, headers=HEADERS, json=payload)
            
            # もしプロパティ名エラーなら、タイトルプロパティを調整してリトライ（簡易的な対応）
            if response.status_code == 400 and "property" in response.text:
                # エラーメッセージを見て判断するのは難しいので、
                # 一般的な別名 "Task name" でリトライしてみる
                del properties["Name"]
                properties["Task name"] = {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
                payload["properties"] = properties
                response = await client.post(url, headers=HEADERS, json=payload)

            if response.status_code != 200:
                 return {"error": f"Notion API Error: {response.text}"}
            
            data = response.json()
            return {
                "message": "Task created successfully",
                "id": data["id"],
                "url": data["url"],
                "title": title
            }

        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}
