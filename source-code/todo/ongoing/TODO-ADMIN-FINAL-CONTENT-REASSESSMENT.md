# Admin final-content reassessment

Status: Ongoing
Created: 2026-11-11
Started: 2026-11-11
Completed: Not completed

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
- [ ] Commit/push, deploy with encrypted backup and migration, verify production services/APIs and normal Admin UI without starting paid reassessment.
- [ ] Record acceptance evidence and move this plan to completed.
