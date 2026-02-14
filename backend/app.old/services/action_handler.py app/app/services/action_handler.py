import logging
from typing import Dict, Any, List
from app.models import UserIntent

logger = logging.getLogger(__name__)

class ActionHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_action(self, user_intent: UserIntent, context: Dict[str, Any]) -> Dict[str, Any]:
        # Check if this is an investigation/debugging context
        if user_intent.is_investigation or user_intent.is_debugging:
            # Skip summarization and pass raw data to AI
            return {
                "type": "raw_data",
                "data": context.get("raw_data", []),
                "error": context.get("error", None),
                "user_intent": user_intent
            }
        
        # Normal handling with summarization
        summary = self._create_summary(context)
        return {
            "type": "summary",
            "summary": summary,
            "user_intent": user_intent
        }
    
    def _create_summary(self, context: Dict[str, Any]) -> str:
        # Implementation of summarization logic
        return "Summary of the context"
