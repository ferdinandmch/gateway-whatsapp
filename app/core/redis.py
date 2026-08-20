from typing import Optional

# Redis client is provisioned in V1 but not actively used.
# Active Redis usage begins in a future spec (caching, rate limiting, pub/sub).

_redis_client = None


def get_redis_client(redis_url: str):
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(redis_url, decode_responses=True)
    return _redis_client
