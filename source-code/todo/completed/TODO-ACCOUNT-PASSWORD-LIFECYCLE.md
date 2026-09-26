# Account password lifecycle and login visibility

**Status:** Completed and production verified.

This roadmap adds the account recovery controls required for AKURU's current
Admin-managed family model. It does not introduce email recovery or allow a
Parent to reset a child's password. Those later capabilities are tracked in
`TODO-FUTURE-ACCOUNT-RECOVERY.md`.

## Step 1 — Record secure account lifecycle rules

- [x] Document that passwords and temporary passwords must never be stored in
  plaintext, included in audit data, written to logs, analytics or error
  reports, or returned by account-list APIs.
- [x] Define an Admin-only reset permission enforced by FastAPI independently
  of frontend navigation.
- [x] Define one-time temporary-password disclosure: AKURU generates a strong
  password, returns it only in the successful reset response and never makes it
  retrievable again.
- [x] Define the session and password state transitions for reset, forced
  replacement and normal authenticated password change.
- [x] Define a password policy shared by temporary-password replacement and
  normal password changes, including rejection of the current password.

**Acceptance:** backend, frontend and audit behavior have one documented rule
set and no workflow requires storing a recoverable password.

## Step 2 — Add Admin-issued temporary-password resets

- [x] Add an authenticated, CSRF-protected Admin API that resets an active
  Parent or Student account by opaque public reference.
- [x] Generate the temporary password using a cryptographically secure random
  generator with sufficient length and character diversity.
- [x] Store only its strong salted password hash and set the account to require
  a password replacement on next login.
- [x] Return the generated temporary password only once in the successful API
  response. Retries must not disclose the same password or silently generate a
  second password.
- [x] Add an Admin account-management action with a clear confirmation step.
- [x] Show the generated password in a one-time result panel with Copy and Done
  controls. Closing or leaving the panel permanently removes it from the UI.
- [x] Do not put the password in a URL, browser storage, Query cache,
  notification text or downloadable file.

**Acceptance:** an Admin can issue a temporary password, see it exactly once
and hand it to the account owner without AKURU retaining a readable copy.

## Step 3 — Revoke sessions and force replacement

- [x] Revoke every active session belonging to the account in the same database
  transaction as the password reset.
- [x] Ensure an already-open browser loses access on its next authenticated
  request and clears private frontend query state.
- [x] Allow the temporary password to authenticate only into the existing
  forced-password-replacement experience.
- [x] Require a valid new password and confirmation without asking the user to
  re-enter the temporary password after login.
- [x] Reject reuse of the temporary password and revoke the temporary login
  session after successful replacement, issuing a fresh authenticated session
  only after the password transition is complete.

**Acceptance:** the former password and every former session stop working as
soon as the reset succeeds, and normal portal access remains blocked until the
temporary password is replaced.

## Step 4 — Add normal authenticated password changes

- [x] Add a protected Change password page for Admin, Parent and Student roles.
- [x] Require the current password, new password and confirmation for a normal
  password change.
- [x] Apply the shared password policy and return specific, safe validation
  messages, including that the new password cannot equal the current password.
- [x] Revoke the user's other sessions after a successful change and rotate the
  current session securely.
- [x] Ensure role and family authorization remain unchanged by a password
  change.

**Acceptance:** any authenticated user can safely replace their known password
and all other signed-in devices lose access.

## Step 5 — Add auditing without password exposure

- [x] Record who initiated each Admin reset, which account was affected, when
  it occurred and that sessions were revoked.
- [x] Record successful forced replacements and normal password changes without
  storing current, temporary or new passwords.
- [x] Record rejected and rate-limited attempts using safe identifiers and
  metadata that do not expose credentials.
- [x] Add Admin operational visibility for reset and suspicious-authentication
  events while preserving Parent and Student privacy.
- [x] Add automated checks proving that audit data, application logs and API
  error payloads contain no password values.

**Acceptance:** security events are traceable while credentials remain absent
from all persistent and operational records.

## Step 6 — Add rate limits and enumeration protection

- [x] Apply independent limits to login, Admin reset and password-change
  endpoints using appropriate account and network signals.
- [x] Use bounded delays and temporary lockouts that slow automated attacks
  without permanently locking a child out of AKURU.
- [x] Keep unauthenticated responses consistent for existing and unknown
  usernames and avoid exposing role, display name, family or account status.
- [x] Avoid materially different response timing for known and unknown account
  identifiers where an unauthenticated endpoint is involved.
- [x] Emit safe operational events for repeated failures and rate-limit
  activation.
- [x] Document support recovery for a legitimately locked account.

**Acceptance:** automated guessing and username discovery are constrained, and
ordinary errors do not reveal whether a Parent or Student account exists.

## Step 7 — Show Student last-login information

- [x] Persist a Student's last successful login time separately from failed
  attempts and ordinary session activity.
- [x] Decide and document whether the displayed value means the current login
  or the preceding successful login, and use that definition consistently.
- [x] Show the value to Admins for every Student account.
- [x] Show the value to a Parent only for Students linked to that Parent.
- [x] Display `Never signed in` when no successful login has occurred.
- [x] Use the user's local timezone in the frontend while preserving an
  unambiguous UTC timestamp in the database and API.
- [x] Do not expose Student login information to other Students or unrelated
  Parents.

**Acceptance:** Admins and authorized Parents can see a clear, accurate last
login time without expanding family data access.

## Step 8 — Verification and controlled release

- [x] Test Admin reset authorization, one-time disclosure, retry behavior,
  password hashing and audit redaction.
- [x] Test immediate session revocation across multiple browsers and devices.
- [x] Test forced replacement, normal change, password reuse rejection and
  current-session rotation.
- [x] Test login and password endpoint rate limits, safe unknown-user responses
  and account-unlock recovery.
- [x] Test Admin and Parent last-login visibility, `Never signed in`, timezone
  rendering and family isolation.
- [x] Update Admin, Parent, Student and developer documentation.
- [x] Run the full backend and frontend release gates before production
  deployment.

**Done when:** the complete current-scope password lifecycle is implemented,
security-tested, documented and production-verified.

