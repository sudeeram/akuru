from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.storage.base import ObjectStorage
from app.storage.local import LocalObjectStorage
from app.storage.oci import OCIObjectStorage


@lru_cache
def get_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalObjectStorage(Path(settings.local_storage_path))
    if settings.storage_backend == "oci":
        if not settings.oci_object_namespace or not settings.oci_object_bucket:
            raise RuntimeError("OCI namespace and bucket are required for OCI object storage.")
        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("Install the OCI Python SDK before using OCI object storage.") from exc
        client = oci.object_storage.ObjectStorageClient(oci.config.from_file())
        return OCIObjectStorage(client, settings.oci_object_namespace, settings.oci_object_bucket)
    raise RuntimeError(f"Unsupported storage backend: {settings.storage_backend}")
