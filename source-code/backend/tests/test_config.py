from sqlalchemy import URL

from app.config import Settings


def test_database_url_safely_handles_special_characters() -> None:
    settings = Settings(database_password="contains#special@characters", _env_file=None)
    assert isinstance(settings.database_url, URL)
    assert settings.database_url.password == "contains#special@characters"
    assert "contains#special@characters" not in settings.database_url.render_as_string()


def test_default_document_storage_is_outside_source_checkout() -> None:
    settings = Settings(database_password="secret", _env_file=None)
    assert settings.local_storage_path == "/data/akuru/documents"
