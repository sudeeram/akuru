import uuid
from typing import Any

from app.queue.base import QueueUnavailable


class RedisDocumentQueue:
    def __init__(self, client: Any, queue_name: str):
        self.client = client
        self.queue_name = queue_name

    def enqueue(self, job_id: uuid.UUID) -> None:
        try:
            self.client.rpush(self.queue_name, str(job_id))
        except Exception as exc:
            raise QueueUnavailable("Redis could not accept the document job.") from exc

    def dequeue(self, timeout_seconds: int = 5) -> uuid.UUID | None:
        try:
            result = self.client.blpop(self.queue_name, timeout=timeout_seconds)
        except Exception as exc:
            raise QueueUnavailable("Redis could not provide a document job.") from exc
        if result is None:
            return None
        value = result[1]
        if isinstance(value, bytes):
            value = value.decode("ascii")
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError) as exc:
            raise QueueUnavailable("Redis returned an invalid document job identifier.") from exc
