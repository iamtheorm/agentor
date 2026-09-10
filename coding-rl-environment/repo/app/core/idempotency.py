import redis.asyncio as redis
import os

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

class IdempotencyManager:
    """
    Manages idempotency keys to prevent double-spending.
    """
    def __init__(self, client: redis.Redis):
        self.client = client

    async def acquire_lock(self, idempotency_key: str, ttl: int = 300) -> bool:
        """
        Acquires a lock atomically using Redis SET NX.
        """
        result = await self.client.set(f"idemp:{idempotency_key}", "locked", ex=ttl, nx=True)
        return bool(result)

    async def release_lock(self, idempotency_key: str):
        """
        Releases the lock. 
        """
        await self.client.delete(f"idemp:{idempotency_key}")

idempotency_manager = IdempotencyManager(redis_client)
