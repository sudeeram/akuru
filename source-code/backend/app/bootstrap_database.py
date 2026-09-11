from sqlalchemy import create_engine, text

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    database_name = settings.database_name
    if not database_name.replace("_", "").isalnum():
        raise ValueError("Database name may contain only letters, numbers, and underscores")

    engine = create_engine(settings.server_database_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database_name}
        ).scalar()
        if not exists:
            connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
            print(f"Created PostgreSQL database: {database_name}")
        else:
            print(f"PostgreSQL database already exists: {database_name}")


if __name__ == "__main__":
    main()
