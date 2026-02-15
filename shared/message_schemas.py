"""
Message Schemas
Redis Pub/Subで使用するメッセージフォーマット定義
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class UserMessage(BaseModel):
    """ユーザーからのメッセージ (input:user)"""
    user_id: str
    username: str
    content: str
    channel_id: str
    message_id: str
    timestamp: str


class BotReaction(BaseModel):
    """Botへのリアクション指示 (bot:reaction)"""
    channel_id: str
    message_id: str
    emoji: str


class BotResponse(BaseModel):
    """Botからの応答 (output:user)"""
    channel_id: str
    content: str


class EvaluationRequest(BaseModel):
    """評価依頼 (evaluator:request)"""
    request_id: str
    context: Dict[str, Any]
    # context = {
    #   "intent": ユーザーの意図,
    #   "result": 実行結果,
    #   "user_id": ユーザーID
    # }


class EvaluationResponse(BaseModel):
    """評価結果 (evaluator:response:{id})"""
    is_correct: bool
    reason: str
    should_fix: bool
    fix_target: Optional[str] = None
    fix_instruction: Optional[str] = None


class AiderRequest(BaseModel):
    """Aider修正依頼 (aider:requests)"""
    type: str  # "auto_fix" or "user_request"
    target_file: Optional[str] = None
    instruction: str
    context: Optional[Dict[str, Any]] = None


class AiderProgress(BaseModel):
    """Aider進捗報告 (aider:progress)"""
    status: str  # "starting", "running", "completed", "failed"
    message: str
    timestamp: str = datetime.now().isoformat()
