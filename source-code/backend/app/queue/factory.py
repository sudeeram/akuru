from functools import lru_cache

import redis

from app.config import get_settings
from app.queue.base import DocumentQueue
from app.queue.redis_queue import RedisDocumentQueue


@lru_cache
def get_document_queue() -> DocumentQueue:
    settings = get_settings()
    client = redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )
    return RedisDocumentQueue(client, settings.document_queue_name)
