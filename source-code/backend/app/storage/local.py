from pathlib import Path

from app.storage.base import StoredObject


class LocalObjectStorage:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError("Object key escapes the private storage root.")
        return path

    def put(self, key: str, content: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(path)

    def get(self, key: str, content_type: str) -> StoredObject:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        return StoredObject(key=key, content=path.read_bytes(), content_type=content_type)

    def delete(self, key: str) -> None:
        path = self._path(key)
        path.unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()
