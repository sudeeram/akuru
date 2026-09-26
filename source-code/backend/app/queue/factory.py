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
        # The worker's blocking dequeue waits for five seconds. The socket
        # must outlive that wait so an empty queue is returned as idle rather
        # than being misreported as a Redis outage.
        socket_timeout=10,
        health_check_interval=30,
    )
    return RedisDocumentQueue(client, settings.document_queue_name)
