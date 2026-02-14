from typing import List, Dict
import requests

class NotionQuery:
    def __init__(self):
        # Initialize Notion API connection
        self.notion_api_key = "your_notion_api_key_here"
        self.database_id = "your_database_id_here"
        self.headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def get_tasks(self) -> List[Dict]:
        """Get tasks from Notion database with minimal information"""
        # Query Notion database
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        
        payload = {
            "page_size": 100  # Get up to 100 tasks
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Notion API error: {response.status_code}")
        
        data = response.json()
        
        # Extract only essential fields for each task
        tasks = []
        for result in data.get('results', []):
            task = {
                'id': result['id'],
                'title': self._get_task_title(result),
                'status': self._get_task_status(result)
            }
            tasks.append(task)
        
        return tasks
    
    def _get_task_title(self, result: Dict) -> str:
        """Extract task title from Notion result"""
        properties = result.get('properties', {})
        title_property = properties.get('Name') or properties.get('Title')
        
        if title_property and 'title' in title_property:
            return ''.join([text['text']['content'] for text in title_property['title']])
        return "No Title"
    
    def _get_task_status(self, result: Dict) -> str:
        """Extract task status from Notion result"""
        properties = result.get('properties', {})
        status_property = properties.get('Status')
        
        if status_property and 'select' in status_property:
            return status_property['select']['name']
        return "Unknown"
