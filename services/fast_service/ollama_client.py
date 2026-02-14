"""
Ollama Client
OllamaとのREST API通信を担当
"""
import httpx
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# エラーログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/ollama_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama REST API クライアント"""
    
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.chat_url = f"{base_url}/api/chat"
    
    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        format: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Ollama Chat APIを呼び出し
        
        Args:
            model: モデル名 (例: "qwen3-coder:30b")
            messages: メッセージリスト [{"role": "user", "content": "..."}]
            format: 応答フォーマット ("json" or None)
            temperature: 温度パラメータ
        
        Returns:
            LLMの応答テキスト
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 8192  # コンテキスト長を拡張
            }
        }
        
        if format:
            payload["format"] = format
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(self.chat_url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                content = data.get("message", {}).get("content", "")
                
                return content
            
            except httpx.TimeoutException as e:
                error_msg = f"❌ Ollama timeout (120s exceeded) - Model: {model}"
                logger.error(f"Timeout error: {error_msg}")
                return error_msg
            except httpx.HTTPStatusError as e:
                error_msg = f"❌ Ollama HTTP error: {e.response.status_code}"
                logger.error(f"HTTP error: {error_msg} - URL: {self.chat_url} - Model: {model} - Response: {e.response.text[:200]}")
                return error_msg
            except Exception as e:
                error_msg = f"❌ Ollama error: {str(e)}"
                logger.error(f"Unexpected error: {error_msg} - Model: {model}")
                return error_msg
