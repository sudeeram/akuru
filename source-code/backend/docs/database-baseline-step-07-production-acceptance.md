# Database baseline Step 7 — Production acceptance and evidence

Production acceptance began on 17 September 2026 against
`akuru.magicalinternational.com`, running reviewed release
`2e2950354b5e275aa102d58684a9023aa94a697e` and baseline migration
`0001_initial_akuru_schema`.

## Passed controls

- The bootstrap Admin completed the forced password change. The temporary
  password no longer authenticates and the replacement credential is stored
  outside the repository in the operator-only credential file.
- Admin login, CSRF rejection, logout, revoked-session rejection and Admin-only
  role enforcement were exercised through the public HTTPS API. Temporary
  Parent and Student accounts were denied access to the Admin route.
- A bounded invalid-login check reached HTTP 429, proving the production login
  rate limiter is active.
- The public health endpoint returned HTTP 200 over HTTPS with HSTS,
  `nosniff`, frame denial and Content Security Policy headers.
- PostgreSQL, Redis, the API and the frontend had no wildcard public listener.
  The API, worker, frontend and Redis services were active, and the configured
  Redis connection responded successfully.
- No priority-error API, worker or frontend journal entries were present for
  the acceptance window. The backup and retention timers are enabled and
  active.
- The production catalog contains one published iGCSE Chemistry textbook using
  Unit terminology, with Units 1–4 and Topics 1–29. No source document was
  attached while the hierarchy was created.

## Acceptance script correction

The release check previously used an HTTP `HEAD` request for `/health`, while
the application deliberately exposes that endpoint as `GET`. The script now
captures headers from a `GET`, includes Redis health, verifies that both
retention timers are enabled and active, and includes Redis in the recent-error
check.

## Deferred Chemistry content pilot

The project owner chose to complete Chemistry Unit 1 later. Only the licensed
source for Chemistry Topic 1 is currently present in the operator's local
source-material folder, and there is no Topic 2 source file. Topic 1 was
rendered to a 12-page PDF and visually sampled, but no source was uploaded to
production.

The following checks move to the later Chemistry textbook-onboarding work and
must use the real Topic 1 and Topic 2 sources:

1. Upload each PDF to its matching Chemistry topic.
2. Review every extraction page, OCR block, formula, diagram and printed-page
   label; resolve all review flags without inventing content.
3. Confirm both topic quality reports pass and publish one reviewed content
   version for each topic.
4. Add reviewed coverage for the pilot topic, then prove exact citations,
   fail-closed question eligibility and same-subject/topic retrieval isolation.
5. Store the final non-secret content-acceptance report under
   `/data/akuru/release-evidence`.

The two role-enforcement accounts created for this acceptance run were disabled
and their sessions revoked during Step 8. They cannot be used as real accounts.

## Release decision

The identity and operational baseline is accepted. Chemistry content ingestion
remains deferred by the project owner. Rollback is not indicated by the checks
completed so far; the encrypted pre-reset backup and pre-squash release remain
available.
