# Database baseline reset — Step 0 eligibility record

Audit date: 17 September 2026

Pre-squash Git revision: `3a002046f705ef5ea398478c7a05ef3150b604e6`

Recovery tag: `pre-baseline-squash-20260917`

## Read-only findings

The current repository has one Alembic head at `h86c0d2f7a97` and 39 active migration files. The production deployment reports one head at `b72fa92d4e11`; production has not received the textbook-topic migrations.

Neither environment contains uploaded documents, extraction records, textbook content, curriculum coverage, question mappings, assessments, mastery evidence, Tutor learning records or evaluation content. Production `/data/akuru/documents` contains zero files.

Both environments contain three user identities: one Admin, one Parent and one Student. Each also contains the Student profile, progression/subject enrolment and quota records. Production contains one active session and three audit events. Local contains three sessions, two audit events and one active study-plan shell with zero study-plan items.

The initial assumption that production contained only an Admin account is therefore incorrect. No records were deleted or changed during this audit.

## Eligibility decision

Educational-content eligibility is satisfied, but destructive reset authorization is pending. The database reset must not begin until the owner confirms that the Parent, Student, enrolment, quota and empty local study-plan records are disposable and that all three accounts should be recreated as needed.

The production audit used read-only table counts because the deployed revision predates `app.content_migration_audit`. Immediately before the eventual reset, deploy the reviewed audit code and rerun `python -m app.content_migration_audit --require-empty` against production.

## Freeze

Until the baseline reset is completed or cancelled, do not upload educational documents, create additional accounts, begin Student work, or deploy schema changes. Read-only inspection and local code development may continue.

## Evidence handling

This record deliberately excludes usernames, password hashes, session tokens, database credentials and document paths. The recovery tag preserves the full migration chain. Production backup and database recreation belong to later roadmap steps and were not performed in Step 0.
