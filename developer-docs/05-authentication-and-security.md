# Authentication and security

## Sessions and passwords

Passwords use the recommended Argon2 configuration through `pwdlib`. Only hashes are stored. Login creates a high-entropy opaque session token; PostgreSQL stores only its SHA-256 digest. The browser receives:

- `akuru_session`: HttpOnly, SameSite Strict, Secure in production;
- `akuru_csrf`: same-site token readable by the frontend for mutation headers.

`app/security.py` resolves active, non-expired, non-revoked sessions. `app/permissions.py` provides role dependencies and rejects normal feature use until a temporary password is changed.

## CSRF and request controls

Every state-changing authenticated endpoint must require `X-CSRF-Token` through `require_csrf` or `require_csrf_roles`. Middleware rejects unapproved origins, untrusted hosts and oversized requests. Production adds HSTS, CSP, frame denial, MIME sniffing protection, referrer policy and permissions policy.

Login has persisted username/IP throttling. Production request limiting uses Redis and fails closed when the configured distributed limiter is unavailable.

## Password lifecycle

Admins can reset an active Parent or Student account by its opaque `public_ref`.
AKURU generates a 20-character temporary password with a cryptographically
secure random generator, stores only its Argon2 hash, revokes all sessions in
the reset transaction, and returns the readable value in that response only.
The request key prevents a browser retry from silently creating or redisplaying
a password. The user can sign in with it only to reach the forced replacement
screen; replacement rotates the session and does not ask for the temporary
password again.

Admin, Parent and Student accounts also have an authenticated Account security
route. A normal change verifies the current password, rejects reuse, revokes
other sessions and rotates the current session. Both workflows share the API's
12–200 character password boundary. Passwords must never appear in audit data,
logs, URLs, browser storage, query caches or account-list responses.

Successful resets, forced replacements, normal changes, rejected known-password
changes and reset rate limits are audited with public references and safe
metadata. `GET /api/v1/admin/accounts/security-events` gives Admins the latest
100 lifecycle events. Login uses the same response for an unknown username,
wrong password, inactive account or wrong role and locks a username/IP digest
temporarily after repeated failures. Support recovery is to wait for the stated
lock period or have an Admin issue a new temporary password.

`users.last_login_at` records the current successful login in UTC. It is not
updated by ordinary requests or failed attempts. Admin sees every Student and
Parent value; a Parent receives it only for linked Students. The browser renders
the timestamp in its local timezone and shows `Never signed in` for null values.

## Authorization model

There are three roles:

- Admin manages accounts, enrolments, sources, curriculum, releases and operations.
- Parent reads and reviews data for linked children only.
- Student accesses only their own eligible learning data and submissions.

Role permission alone is insufficient. Services also validate resource ownership and subject/course eligibility. Parent queries join through authorized child relationships. Student mutations derive ownership from the session instead of trusting a submitted Student ID.

Private file endpoints repeat authorization at delivery time. A valid object key or UUID is never sufficient access.

## Secret handling

Local secrets belong in ignored `backend/.env`. Production secrets live in `/etc/akuru/akuru.env`, owned by `root:akuru` with mode `0640`. OpenAI keys are mapped to Admin-configured aliases; the UI can report whether an alias is configured but never receives the key.

Never place database passwords, API keys, operations tokens, student data or private storage paths in:

- frontend code or frontend environment variables;
- Git commits;
- screenshots and documentation examples;
- audit event payloads; or
- raw user-facing errors.

## AI safety boundary

Prompts receive bounded, authorized source material and pseudonymous learner references where possible. Provider output is parsed into a strict schema and cannot directly publish learning material, change enrolment, award unchecked marks or execute arbitrary tools. Assessment feedback and Tutor features have independent evaluation/release gates.

Tutor access is blocked during formal assessments even if the frontend control is visible or a feature flag is enabled.

## Production security checklist

- Public ports: 80/443 through Nginx; restrict SSH by operator address.
- Private ports: 5432, 6379, 8000 and 5181 remain on loopback.
- Run application services as the unprivileged `akuru` account.
- Require HTTPS cookies and exact public hosts/origins.
- Keep malware scanning enabled and fail closed.
- Review audit events, provider failures and document-job failures.
- Run encrypted backups and restoration drills.
- Use retention tooling only after preview and authorization.
