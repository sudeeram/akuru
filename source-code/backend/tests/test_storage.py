from pathlib import Path
from types import SimpleNamespace

import pytest

from app.storage.local import LocalObjectStorage
from app.storage.oci import OCIObjectStorage


def test_local_storage_round_trip_and_path_confinement(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path / "objects")
    storage.put("documents/one/original.pdf", b"contents", "application/pdf")
    stored = storage.get("documents/one/original.pdf", "application/pdf")
    assert stored.content == b"contents"
    assert storage.exists("documents/one/original.pdf")
    storage.delete("documents/one/original.pdf")
    assert not storage.exists("documents/one/original.pdf")
    with pytest.raises(ValueError, match="escapes"):
        storage.put("../outside.pdf", b"unsafe", "application/pdf")


def test_oci_storage_uses_private_bucket_client_contract() -> None:
    calls = []

    class Client:
        def put_object(self, *args, **kwargs):
            calls.append(("put", args, kwargs))

        def get_object(self, *args):
            calls.append(("get", args, {}))
            return SimpleNamespace(data=SimpleNamespace(content=b"oci-content"))

        def head_object(self, *args):
            calls.append(("head", args, {}))

        def delete_object(self, *args):
            calls.append(("delete", args, {}))

    storage = OCIObjectStorage(Client(), "namespace", "private-bucket")
    storage.put("key", b"oci-content", "application/pdf")
    assert storage.get("key", "application/pdf").content == b"oci-content"
    assert storage.exists("key")
    storage.delete("key")
    assert [call[0] for call in calls] == ["put", "get", "head", "delete"]
