# PostgreSQL backup and restore

AKURU uses PostgreSQL custom-format backups. They include the schema, Alembic revision and data, and can be inspected or selectively restored with `pg_restore`.

## Create a local backup

From `source-code/`, with `backend/.env` configured and PostgreSQL running:

```bash
npm run database:backup
```

Backups are written below `backend/backups/` and ignored by Git. To choose a protected destination:

```bash
npm run database:backup -- --output /secure/location/akuru.dump
```

## Prove a backup can be restored

The drill creates a temporary database, restores the archive, verifies the Alembic revision and public tables, and removes the temporary database:

```bash
npm run database:restore-drill -- --backup /secure/location/akuru.dump
```

With no `--backup`, the command creates a fresh backup and drills it immediately:

```bash
npm run database:restore-drill
```

The PostgreSQL account must be allowed to create and drop databases for the drill. The production application account should have narrower privileges; run production drills with a separate maintenance identity in an isolated environment.

## Operating policy

- Encrypt backup storage and restrict it to the operators who can access production student data.
- Keep at least one copy outside the application server and apply retention rules appropriate for family data.
- Run a restore drill after schema changes and on a regular schedule.
- A successful `pg_dump` is incomplete evidence; the restore drill must also pass.
- Never commit `.dump` files or copy production data into developer machines.
