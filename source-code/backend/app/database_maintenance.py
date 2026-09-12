"""Create PostgreSQL backups and prove that they can be restored."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.config import Settings, get_settings


POSTGRES_BIN_DIRS = (
    Path("/Applications/Postgres.app/Contents/Versions/latest/bin"),
    Path("/opt/homebrew/bin"),
    Path("/usr/local/bin"),
)


def postgres_tool(name: str) -> str:
    located = shutil.which(name)
    if located:
        return located
    for directory in POSTGRES_BIN_DIRS:
        candidate = directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    library_root = Path("/Library/PostgreSQL")
    if library_root.is_dir():
        candidates = sorted(library_root.glob(f"*/bin/{name}"), reverse=True)
        if candidates:
            return str(candidates[0])
    raise RuntimeError(f"{name} was not found. Install PostgreSQL client tools and add them to PATH.")


def client_environment(settings: Settings) -> dict[str, str]:
    return {**os.environ, "PGPASSWORD": settings.database_password}


def connection_arguments(settings: Settings, database_name: str) -> list[str]:
    return [
        "--host", settings.database_host,
        "--port", str(settings.database_port),
        "--username", settings.database_user,
        "--dbname", database_name,
    ]


def create_backup(settings: Settings, output: Path | None = None) -> Path:
    if output is None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output = Path("backups") / f"akuru-{stamp}.dump"
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        postgres_tool("pg_dump"),
        *connection_arguments(settings, settings.database_name),
        "--format=custom", "--no-owner", "--no-acl", "--file", str(output),
    ]
    subprocess.run(command, env=client_environment(settings), check=True)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("PostgreSQL produced an empty backup.")
    print(f"Backup created: {output}")
    return output


def restore_drill(settings: Settings, backup: Path) -> None:
    backup = backup.expanduser().resolve()
    if not backup.is_file():
        raise FileNotFoundError(f"Backup does not exist: {backup}")
    target_name = f"akuru_restore_{uuid.uuid4().hex[:12]}"
    admin_engine = create_engine(settings.server_database_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{target_name}"')
        subprocess.run(
            [
                postgres_tool("pg_restore"),
                *connection_arguments(settings, target_name),
                "--exit-on-error", "--no-owner", "--no-acl", str(backup),
            ],
            env=client_environment(settings),
            check=True,
        )
        restored_url = settings.database_url.set(database=target_name)
        restored_engine = create_engine(restored_url)
        try:
            with restored_engine.connect() as connection:
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                table_count = connection.execute(text(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )).scalar_one()
            if table_count < 1:
                raise RuntimeError("The restored database contains no public tables.")
        finally:
            restored_engine.dispose()
        print(f"Restore drill passed: revision {revision}, {table_count} public tables")
    finally:
        with admin_engine.connect() as connection:
            connection.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :database AND pid <> pg_backend_pid()"
            ), {"database": target_name})
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{target_name}"')
        admin_engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup", help="Create a custom-format PostgreSQL backup")
    backup.add_argument("--output", type=Path)
    drill = commands.add_parser("restore-drill", help="Restore and validate a backup in an isolated database")
    drill.add_argument("--backup", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    if args.command == "backup":
        create_backup(settings, args.output)
        return
    backup = args.backup or create_backup(settings)
    restore_drill(settings, backup)


if __name__ == "__main__":
    main()
