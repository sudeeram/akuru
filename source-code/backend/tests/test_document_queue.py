import uuid

import pytest

from app.queue import QueueUnavailable, RedisDocumentQueue
from app.services.document_processing import ProcessingFailure, preflight


class RedisClientStub:
    def __init__(self):
        self.values = []

    def rpush(self, name, value):
        self.values.append((name, value.encode("ascii")))

    def blpop(self, name, timeout):
        if not self.values:
            return None
        queue_name, value = self.values.pop(0)
        return queue_name.encode("ascii"), value


def test_redis_queue_round_trip() -> None:
    client = RedisClientStub()
    queue = RedisDocumentQueue(client, "akuru:test")
    job_id = uuid.uuid4()
    queue.enqueue(job_id)
    assert queue.dequeue() == job_id
    assert queue.dequeue() is None


def test_redis_queue_rejects_invalid_identifiers() -> None:
    client = RedisClientStub()
    client.values.append(("akuru:test", b"not-a-uuid"))
    queue = RedisDocumentQueue(client, "akuru:test")
    with pytest.raises(QueueUnavailable, match="invalid"):
        queue.dequeue()


def test_preflight_enforces_page_limit_and_handles_images() -> None:
    assert preflight(b"image", "image/png", 1)["pageCount"] == 1
    with pytest.raises(ProcessingFailure, match="contains 2 pages") as exceeded:
        preflight(b"%PDF /Type /Page /Type /Page", "application/pdf", 1)
    assert exceeded.value.code == "page_limit_exceeded"


def test_preflight_fails_closed_when_pdf_page_count_is_unknown() -> None:
    with pytest.raises(ProcessingFailure) as unknown:
        preflight(b"%PDF without page markers", "application/pdf", 10)
    assert unknown.value.code == "page_count_unknown"
