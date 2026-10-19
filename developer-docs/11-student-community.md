# Student Community

Community is optional and Student-only. Public identity is separate from User identity, with a unique NFKC-normalized, case-insensitive public name and a separate opaque learner reference. No existing Student is opted in by migration. Responses use dedicated schemas and never reuse portal-state Student records. Public avatars use the existing validated artwork; absent avatars use a neutral star instead of real-name initials.

## Enrolment and discovery

Current `StudentProgression` records define course membership. AKURU currently permits one current progression per Student; services return course choices as a list to accommodate future membership changes without altering follow storage. Subject enrolments are currently Student-wide, so they are associated with the current course, not historical progression records. Discovery filters current course IDs in SQL. Subject-filter choices come from visible enrolled subjects of eligible participants and the viewer's own enrolments. Hidden subjects never contribute discovery matches or public responses.

Discovery scope is explicitly shared-course; no all-platform scope is accepted. Follows do not reference enrolments and survive course changes. A pre-existing incoming follow permits follow back across course boundaries. Public-profile reads require shared current course or an existing connection. Other Students' connection lists and counts are not exposed.

## Data and lifecycle

Migration `0012_student_community` creates five tables with frozen PostgreSQL DDL: community profiles, directed follows, directed blocks, notifications and reports. Pairs are unique; follows and blocks prohibit self-connections. Student-profile deletion cascades community data. Audit actor constraints still follow existing account-deletion procedures.

Pair mutations lock User rows in deterministic ID order, then expire and re-read state. This also handles first preference saves before a community-profile row exists. A follow and its durable `follow.v1` notification commit together. Notifications have a unique recipient/actor/type key; repeated follows within 24 hours retain the existing read state and do not create a new notification. A subsequent follow after 24 hours refreshes that record. No unfollow notification is generated. Community preference/follow/block/report changes are limited to 30 successful changes per Student per minute; the existing HTTP limiter also applies.

Hiding retains follows but suppresses the identity in discovery, relationship lists, public reads, Feed and unread counts. Re-enabling restores eligible connections. A block removes both follow directions and pair notifications; unblocking never restores them. Block settings retain an opaque unblock reference, but hidden/inactive names are replaced with “Unavailable learner”. Feed events resolve the current public identity and relationship state at read time.

Reports retain the public name at reporting and one row per reporter/target pair. Re-reporting a closed concern can reopen it after 24 hours. Admin review never returns reporter identity, and audited name-change action hides the target without changing account or learning access. A changed name cannot be sanctioned based on a stale name snapshot. Reports/relationships remain until Student-profile deletion; no general free-text reporting or messaging content is collected. Backups follow existing retention rules.

## API and frontend

`/api/v1/community`: own settings, course subject choices, paginated discover/following/followers, minimal member reads, follow/unfollow, block/unblock/list, private reports, Feed and own notice read state. Admin-only `/reports` supports a paginated queue and audited review. Mutations require existing CSRF and role checks; private responses use `Cache-Control: no-store`. Pages are bounded to 20 rows and queries to 64 characters.

Student route: `/student/community`, with URL-backed section/course/subject/search/page filters. Preferences also appear on the Student profile. Admin route: `/admin/community-reports`. Query keys include the actor; existing sign-out cache clearing applies. The Feed and top-bar badge share the same stored source and refresh every 60 seconds. Mutations invalidate related actor queries immediately.

## Verification and release

`tests/test_community.py` exercises HTTP privacy, course boundaries, hidden subjects, opt-in, follow/back, cooldown, blocking, moderation and CSRF. Default tests use isolated SQLite. Set `AKURU_COMMUNITY_TEST_POSTGRES=1` to run the same suite in disposable PostgreSQL schemas, including concurrent duplicate-follow and follow/block race checks. The schema is removed after each successful fixture run; failed interrupted runs may require removing their `community_test_` schema manually.

Before production: verify migration upgrade/schema parity/existing-data counts and downgrade/re-upgrade in a disposable restored database, run the full release gate and signed-in browser acceptance. Deployment requires a fresh verified encrypted backup and existing preflight/acceptance scripts. Rollback restores the prior application and build while retaining additive tables; do not drop production community data to roll back code.

Future discovery scopes and learning milestones need explicit product/audience rules. Versioned event types and enrolment-independent relationships provide extension points; the current release publishes no assessment activity.
