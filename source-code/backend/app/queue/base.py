import uuid
from typing import Protocol


class QueueUnavailable(RuntimeError):
    pass


class DocumentQueue(Protocol):
    def enqueue(self, job_id: uuid.UUID) -> None: ...

    def dequeue(self, timeout_seconds: int = 5) -> uuid.UUID | None: ...
