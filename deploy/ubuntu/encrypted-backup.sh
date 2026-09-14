#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
readonly BACKUP_ROOT="${AKURU_BACKUP_ROOT:-/data/akuru/backups}"
readonly DOCUMENT_ROOT="${AKURU_LOCAL_STORAGE_PATH:-/data/akuru/documents}"
readonly RECIPIENT_FILE="${AKURU_BACKUP_RECIPIENT_FILE:-/etc/akuru/backup-age-recipient}"
if [[ ! -r "${RECIPIENT_FILE}" ]]; then echo "Missing age recipient file." >&2; exit 1; fi
: "${AKURU_DATABASE_PASSWORD:?Database environment is not loaded}"
: "${AKURU_DATABASE_HOST:?Database environment is not loaded}"
: "${AKURU_DATABASE_PORT:?Database environment is not loaded}"
: "${AKURU_DATABASE_USER:?Database environment is not loaded}"
: "${AKURU_DATABASE_NAME:?Database environment is not loaded}"
recipient="$(tr -d '[:space:]' < "${RECIPIENT_FILE}")"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
temporary="$(mktemp "${BACKUP_ROOT}/akuru-${stamp}.XXXXXX.dump")"
document_archive="$(mktemp "${BACKUP_ROOT}/akuru-documents-${stamp}.XXXXXX.tar")"
trap 'rm -f "${temporary}" "${document_archive}"' EXIT
PGPASSWORD="${AKURU_DATABASE_PASSWORD}" pg_dump --host "${AKURU_DATABASE_HOST}" --port "${AKURU_DATABASE_PORT}" --username "${AKURU_DATABASE_USER}" --dbname "${AKURU_DATABASE_NAME}" --format custom --no-owner --no-acl --file "${temporary}"
age --recipient "${recipient}" --output "${BACKUP_ROOT}/akuru-${stamp}.dump.age" "${temporary}"
tar --create --file "${document_archive}" --directory "${DOCUMENT_ROOT}" --one-file-system .
age --recipient "${recipient}" --output "${BACKUP_ROOT}/akuru-documents-${stamp}.tar.age" "${document_archive}"
find "${BACKUP_ROOT}" -type f -name 'akuru-*.dump.age' -mtime +30 -delete
find "${BACKUP_ROOT}" -type f -name 'akuru-documents-*.tar.age' -mtime +30 -delete
echo "Encrypted database and document backups created for ${stamp}."
