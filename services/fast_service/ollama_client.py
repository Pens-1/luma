"""
Ollama Client
OllamaとのREST API通信を担当
"""
import httpx
import json
from typing import List, Dict, Any, Optional


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
            
            except httpx.TimeoutException:
                return "❌ Ollama timeout (120s exceeded)"
            except httpx.HTTPStatusError as e:
                return f"❌ Ollama HTTP error: {e.response.status_code}"
            except Exception as e:
                return f"❌ Ollama error: {str(e)}"
