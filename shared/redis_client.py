"""
Redis Client Utility
共通のRedis接続とPub/Sub機能を提供
"""
import redis.asyncio as redis
import json
from typing import Any, Dict, AsyncIterator
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://:redis_password@redis:6379")


class RedisClient:
    """非同期Redisクライアント"""
    
    def __init__(self, url: str = REDIS_URL):
        self.url = url
        self._client = None
    
    async def connect(self):
        """Redis接続を確立"""
        if not self._client:
            self._client = await redis.from_url(
                self.url,
                decode_responses=True,
                encoding="utf-8"
            )
        return self._client
    
    async def disconnect(self):
        """接続を切断"""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """メッセージをチャンネルに送信"""
        client = await self.connect()
        await client.publish(channel, json.dumps(message, ensure_ascii=False))
    
    async def subscribe(self, *channels: str) -> AsyncIterator[Dict[str, Any]]:
        """チャンネルを購読してメッセージを受信"""
        client = await self.connect()
        pubsub = client.pubsub()
        await pubsub.subscribe(*channels)
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    yield data
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON: {message['data']}")
                    continue
    
    async def get(self, key: str) -> str:
        """キーの値を取得"""
        client = await self.connect()
        return await client.get(key)
    
    async def set(self, key: str, value: str, ex: int = None):
        """キーに値を設定"""
        client = await self.connect()
        await client.set(key, value, ex=ex)
