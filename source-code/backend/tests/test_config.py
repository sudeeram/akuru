from sqlalchemy import URL

from app.config import Settings
from pydantic import ValidationError
import pytest


def test_database_url_safely_handles_special_characters() -> None:
    settings = Settings(database_password="contains#special@characters", _env_file=None)
    assert isinstance(settings.database_url, URL)
    assert settings.database_url.password == "contains#special@characters"
    assert "contains#special@characters" not in settings.database_url.render_as_string()


def test_default_document_storage_is_outside_source_checkout() -> None:
    settings = Settings(database_password="secret", _env_file=None)
    assert settings.local_storage_path == "/data/akuru/documents"


def test_production_rejects_insecure_transport_and_missing_operations_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(database_password="secret", environment="production", _env_file=None)
    secure = Settings(database_password="secret", environment="production", public_host="akuru.example.com", cookie_secure=True,
        cors_origins=["https://akuru.example.com"], allowed_hosts=["akuru.example.com"],
        operations_token="long-random-operations-token", malware_scan_command="clamscan",
        tutor_release_gates_required=True, _env_file=None)
    assert secure.cookie_secure is True
