from typing import List
from app.plugins.notion_query import NotionQuery
from app.services.task import Task

class ActionHandler:
    def __init__(self):
        self.notion_query = NotionQuery()
    
    def get_tasks_for_ai(self) -> List[dict]:
        """Get tasks for AI with limited information and max 10 tasks"""
        # Get all tasks from Notion
        all_tasks = self.notion_query.get_tasks()
        
        # Limit to maximum 10 tasks
        limited_tasks = all_tasks[:10]
        
        # Extract only essential information (id, title, status)
        minimal_tasks = []
        for task in limited_tasks:
            minimal_task = {
                'id': task.get('id'),
                'title': task.get('title'),
                'status': task.get('status')
            }
            minimal_tasks.append(minimal_task)
        
        return minimal_tasks
