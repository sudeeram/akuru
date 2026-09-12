from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    key: str
    content: bytes
    content_type: str


class ObjectStorage(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None: ...

    def get(self, key: str, content_type: str) -> StoredObject: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...
