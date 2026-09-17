from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_production_deployment_is_forward_only_and_requires_backup_evidence() -> None:
    script = (ROOT / "deploy" / "ubuntu" / "deploy-reviewed-release.sh").read_text()

    assert '"${AKURU_DATABASE_NAME:-}" == "akuru"' in script
    assert "--recreate-database" not in script
    assert "dropdb" not in script
    assert "createdb" not in script
    assert "app.bootstrap_admin" not in script
    assert "systemctl start akuru-backup.service" in script
    assert "plaintext_database_list=passed" in script
    assert "plaintext_document_list=passed" in script
    assert script.index("systemctl start akuru-backup.service") < script.index('alembic" upgrade head')
    assert 'for _ in {1..30}' in script
    assert '--header "Host: ${AKURU_PUBLIC_HOST}"' in script


def test_encrypted_backup_validates_plaintext_archives_and_writes_checksums() -> None:
    script = (ROOT / "deploy" / "ubuntu" / "encrypted-backup.sh").read_text()

    assert 'pg_restore --list "${temporary}"' in script
    assert 'tar --list --file "${document_archive}"' in script
    assert "database_sha256=" in script
    assert "document_sha256=" in script
    assert "akuru-${stamp}.manifest" in script
    assert script.count('find "${BACKUP_ROOT}" -maxdepth 1') == 3


def test_preflight_runs_from_backend_and_checks_runtime_ownership() -> None:
    script = (ROOT / "deploy" / "ubuntu" / "release-preflight.sh").read_text()

    assert 'readlink -f "${source_root}/backend/.env"' in script
    assert 'sudo -u akuru test -w "${source_root}/frontend"' in script
    assert '(cd "${source_root}/backend"' in script
    assert "--require-baseline-reset-eligible" not in script
    assert "migration_policy=forward_only" in script


def test_release_acceptance_ignores_journal_no_entries_banner() -> None:
    script = (ROOT / "deploy" / "ubuntu" / "release-acceptance.sh").read_text()

    assert "--priority=err --quiet --no-pager" in script
