from pathlib import Path

import pytest

from app import database_maintenance
from app.config import Settings


def test_connection_arguments_do_not_contain_password() -> None:
    settings = Settings(database_password="secret#value", _env_file=None)
    arguments = database_maintenance.connection_arguments(settings, "akuru_test")
    assert "secret#value" not in arguments
    assert arguments[-1] == "akuru_test"


def test_client_environment_passes_password_outside_command() -> None:
    settings = Settings(database_password="secret#value", _env_file=None)
    assert database_maintenance.client_environment(settings)["PGPASSWORD"] == "secret#value"


def test_missing_backup_fails_before_creating_database(tmp_path: Path) -> None:
    settings = Settings(database_password="secret#value", _env_file=None)
    with pytest.raises(FileNotFoundError, match="Backup does not exist"):
        database_maintenance.restore_drill(settings, tmp_path / "missing.dump")
