from typing import Any

from app.storage.base import StoredObject


class OCIObjectStorage:
    """OCI adapter using an injected ObjectStorageClient-compatible client."""

    def __init__(self, client: Any, namespace: str, bucket: str):
        self.client = client
        self.namespace = namespace
        self.bucket = bucket

    def put(self, key: str, content: bytes, content_type: str) -> None:
        self.client.put_object(
            self.namespace, self.bucket, key, content,
            content_type=content_type,
        )

    def get(self, key: str, content_type: str) -> StoredObject:
        response = self.client.get_object(self.namespace, self.bucket, key)
        return StoredObject(key=key, content=response.data.content, content_type=content_type)

    def delete(self, key: str) -> None:
        self.client.delete_object(self.namespace, self.bucket, key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(self.namespace, self.bucket, key)
            return True
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status == 404:
                return False
            raise
