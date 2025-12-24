"""
Redis client for caching and real-time features
"""

from typing import Any, Optional
from functools import lru_cache
import json
import structlog
import redis.asyncio as redis

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """
    Wrapper for Redis operations
    """
    
    def __init__(self):
        """Initialize Redis connection"""
        self.host = settings.REDIS_HOST
        self.port = settings.REDIS_PORT
        self.db = settings.REDIS_DB
        self.password = settings.REDIS_PASSWORD
        self.max_connections = settings.REDIS_MAX_CONNECTIONS
        
        self._client = None
        self._pool = None
    
    async def connect(self) -> None:
        """Establish connection to Redis"""
        try:
            # Create connection pool
            self._pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                decode_responses=True,
            )
            
            # Create Redis client
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            
            logger.info(
                "Connected to Redis",
                host=self.host,
                port=self.port,
                db=self.db,
            )
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self._client:
            await self.connect()
        
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in Redis
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        if not self._client:
            await self.connect()
        
        try:
            serialized = json.dumps(value)
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        
        Args:
            key: Cache key
            
        Returns:
            Success status
        """
        if not self._client:
            await self.connect()
        
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis DELETE failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        if not self._client:
            await self.connect()
        
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error("Redis EXISTS failed", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        if not self._client:
            await self.connect()
        
        try:
            await self._client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value or None
        """
        if not self._client:
            await self.connect()
        
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error("Redis INCR failed", key=key, error=str(e))
            return None
    
    async def publish(self, channel: str, message: Any) -> bool:
        """
        Publish message to channel (pub/sub)
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            Success status
        """
        if not self._client:
            await self.connect()
        
        try:
            serialized = json.dumps(message)
            await self._client.publish(channel, serialized)
            return True
        except Exception as e:
            logger.error("Redis PUBLISH failed", channel=channel, error=str(e))
            return False
    
    async def ping(self) -> bool:
        """
        Test connection
        
        Returns:
            True if connected
        """
        if not self._client:
            await self.connect()
        
        try:
            return await self._client.ping()
        except Exception as e:
            logger.error("Redis PING failed", error=str(e))
            return False
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")


@lru_cache()
def get_redis_client() -> RedisClient:
    """
    Get singleton Redis client instance
    """
    return RedisClient()


# Utility functions for common caching patterns
async def cache_get_or_set(
    key: str,
    fetch_func,
    ttl: int = 3600,
) -> Any:
    """
    Get from cache or fetch and cache
    
    Args:
        key: Cache key
        fetch_func: Async function to fetch data
        ttl: Time to live in seconds
        
    Returns:
        Cached or fetched value
    """
    client = get_redis_client()
    
    # Try to get from cache
    cached = await client.get(key)
    if cached is not None:
        return cached
    
    # Fetch data
    data = await fetch_func()
    
    # Cache it
    await client.set(key, data, ttl)
    
    return data