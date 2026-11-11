# Admin final-content reassessment

Status: Completed
Created: 2026-11-11
Started: 2026-11-11
Completed: 2026-11-11

## Scope

Admins manually review image crops, labels and associations. Source-grounded AI reassesses final saved wording, marking points, report interpretation and reviewed visuals. Only low-confidence content (75% or lower) or explicit blockers requires individual manual content review. Preserve human approvals, source conflicts, history, manual scoring and Student-release boundaries.

Deploy the workflow before running the final Biology June 2025 2BR comparison. No paid final assessment is included in implementation acceptance.

- [x] Add authenticated Admin-only readiness, durable job listing and revision/hash/history-bound batch creation, with CSRF and idempotency.
- [x] Separate source-link jobs from accuracy jobs with additive migration 0022; preserve existing job data.
- [x] Validate visual review before queueing; show separate image and low-confidence content queues.
- [x] Compare original source pages and actual selected crop bytes, checking version hashes and bounded inputs. Record actual provider/model/response provenance, separate wording/marking/visual estimates and specific blockers.
- [x] Reject stale snapshots before/after paid calls, unprovided source pages, incomplete part inventories and invalid output. Fail interrupted work without automatic paid retries.
- [x] Append fresh assessments atomically with job completion, using existing guarded AI approval. Preserve prior checked low-confidence source concerns for Admin adjudication rather than silently increasing their scores.
- [x] Add accuracy-page and individual-question controls, paid-call confirmation, saved progress, polling, error messages and retained question/subpart selection. Do not release papers.
- [x] Pass focused backend regressions and local migration drift check.
- [x] Pass frontend tests, typecheck, lint, contract verification and production build.
- [x] Commit/push, deploy with encrypted backup and migration, verify production services/APIs and normal Admin UI without starting paid reassessment.
- [x] Record acceptance evidence and move this plan to completed.

## Production acceptance — 2026-11-11

Application commit `667a1096587d3d47ac6f1a39c31ee696ae71c942` deployed after encrypted backup. Migration 0022 applied and drift check passed; release evidence is `/data/akuru/release-evidence/deployed-667a1096587d3d47ac6f1a39c31ee696ae71c942-20261111T154905Z.txt`.

- 67 focused backend tests and 122 frontend tests passed; typecheck, lint, generated contracts and build passed. Full backend suite: 476 passed, 1 skipped. The broad run also corrected a stale migration-inventory assertion for the earlier evidence job table and isolated the secret-validation test from the developer's real dotenv file. Those follow-up changes affect tests only.
- Authenticated production read-back is identical to the pre-deployment Biology June 2025 2BR snapshot. No content, accuracy record, image decision or release switch changed.
- New readiness/job reads return 401 without authentication; authenticated POST without CSRF returns 403. No final accuracy jobs exist and implementation/acceptance made zero paid model calls.
- Normal Admin browser check confirmed separate queues, eligible counts and paid-work confirmation. Opened then cancelled confirmation; no job dispatched. Screenshot and private acceptance JSON remain under ignored `tmp/final-accuracy-release/`.
- Actual readiness: all six questions need reassessment; Q1, Q2, Q3 and Q6 are image-ready. Q4 still has candidate/selected visual gates, and Q5 a selected visual gate. These were reported, not silently approved.
- Final AI comparison and subsequent Student release are intentionally outside this implementation acceptance. Finish the remaining manual image gates, then explicitly queue the comparison. Prior source conflicts retain Admin adjudication requirements.

The build continues to report the existing 30 npm dependency advisories, tracked separately. This release does not update dependencies or claim they are resolved.
