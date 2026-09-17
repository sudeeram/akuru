from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_production_reset_requires_exact_scope_confirmation_and_backup_evidence() -> None:
    script = (ROOT / "deploy" / "ubuntu" / "deploy-reviewed-release.sh").read_text()

    assert '"${AKURU_DATABASE_NAME:-}" == "akuru"' in script
    assert '"$confirmation" == "RESET AKURU DATABASE"' in script
    assert "--maintenance-window" in script
    assert "systemctl stop akuru-api akuru-worker akuru-web" in script
    assert "--require-baseline-reset-eligible" in script
    assert "systemctl start akuru-backup.service" in script
    assert "plaintext_database_list=passed" in script
    assert "plaintext_document_list=passed" in script
    assert script.index("systemctl start akuru-backup.service") < script.index("dropdb --if-exists akuru")
    assert "createdb --owner" in script
    assert "CREATE EXTENSION IF NOT EXISTS vector" in script
    assert "app.bootstrap_admin" in script


def test_encrypted_backup_validates_plaintext_archives_and_writes_checksums() -> None:
    script = (ROOT / "deploy" / "ubuntu" / "encrypted-backup.sh").read_text()

    assert 'pg_restore --list "${temporary}"' in script
    assert 'tar --list --file "${document_archive}"' in script
    assert "database_sha256=" in script
    assert "document_sha256=" in script
    assert "akuru-${stamp}.manifest" in script
