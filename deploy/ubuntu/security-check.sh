#!/usr/bin/env bash
set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${root}"
if git grep -nEI 'sk-[A-Za-z0-9_-]{20,}' -- ':!deploy/ubuntu/security-check.sh'; then
  echo "Potential committed secret detected." >&2; exit 1
fi
if git grep -nE '(process\.env\.|import\.meta\.env\.).*(OPENAI_API_KEY|DATABASE_PASSWORD|ACCOUNT_KEYS)' -- source-code/frontend; then
  echo "Backend secret name found in frontend source." >&2; exit 1
fi
if git ls-files | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$'; then
  echo "Private environment file is tracked." >&2; exit 1
fi
echo "Tracked-file secret and frontend-boundary checks passed."
