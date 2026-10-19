# Student Community: course discovery and following

Proposed 19 October 2026 (Asia/Colombo).

Status: implementation and local acceptance in progress. The user authorized end-to-end implementation, commit and production deployment on 19 October 2026.

## Goal

Let Students choose a public identity, discover other participating Students enrolled in the same course (for example, iGCSE), and follow one another. Keep interaction focused on learning connections, without introducing messaging or a general social network.

Course enrolment sets the initial discovery boundary. Subject enrolment is an optional search filter, not a requirement for following another Student within that course. Retain room for broader AKURU discovery and learning milestones later.

## First-release scope

- Optional Student community participation, disabled by default for existing accounts.
- A public name separate from the real name, login username and contact details; reuse the saved AKURU avatar, with a neutral fallback that does not expose real-name initials.
- Course-based discovery, public-name search and an optional subject filter within the selected course.
- One-way following, follow back, unfollow, and mutual-follow status.
- Discover, Following, Followers and Feed tabs in a Student Community workspace.
- In-app follow notifications, unread state and a top-bar notification entry.
- Hide profile, block, report profile and an authorized Admin report-review workflow.

Excluded: direct messages, posts, comments, reactions, attachments, public web profiles, exam/activity sharing, scores, leaderboards and email/push notifications. Milestone sharing is a future feature requiring its own visibility rules.

## Discovery and connection rules

1. Only authenticated Students with community participation enabled can discover or follow other participants. Enabling participation requires a valid public name and a clear explanation of visible information.
2. Initial discovery returns active, participating Students who share the selected enrolled course with the viewer. Exclude the viewer, blocked accounts in either direction, hidden profiles and inactive accounts.
3. If a Student has several courses, provide a course selector restricted to their current enrolments. If they have one course, select it automatically. With no eligible course, explain why discovery is unavailable.
4. Public-name search and subject filters operate within that course scope. Subject options belong to the selected course. Match actual enrolment identifiers, not name strings or assumed grade equivalence; confirm how AKURU represents courses and enrolments before implementation.
5. Students can follow a discovered learner even if they study different subjects within the same course. Enforce eligibility on the server at follow time as well as discovery time.
6. Following is independent of subject and course records. Existing connections survive enrolment changes; following/follower lists may therefore contain connections no longer discoverable through the current course filter. Existing connections remain follow-back eligible while both accounts participate and neither has blocked the other.
7. Keep discovery scope explicit in the service, initially shared-course only. A future all-AKURU scope must require an intentional product and authorization change; do not expose it through an unchecked client parameter.
8. Filtering by a subject must not reveal a hidden subject enrolment. Exclude hidden subjects from search matches and public responses.
9. Never expose account UUIDs as visible labels or use login usernames as public identity. Public-name collisions must not merge identities; use an opaque community reference for actions. Decide name uniqueness and any disambiguator during the first implementation phase.

## Public identity and privacy

Visible to eligible participating Students: public name, avatar, selected visible subjects, and the viewer's relationship to that Student. Course context comes from the selected discovery scope. Do not initially expose another Student's full follower/following lists or totals.

Private: real name, username, email, contact information, Parent details, account metadata, grades/term details, exam attempts, marks, answers and learning history. Add a minimal community-specific response schema rather than reusing the full portal Student response.

Public names need server-side length and character rules, whitespace/Unicode normalization, reserved-name rules and protection against impersonation and inappropriate content. Define practical limits and the Admin response to reports before release. Public names do not change login credentials.

Hide profile removes the Student from discovery and public profile access and prevents new follows in either direction. Retain existing relationship records privately; suppress hidden identities in lists and unread notifications. Re-enabling participation restores eligible connections unless a block or account action removed them. Explain this behavior in settings.

Blocking removes both follow directions, suppresses relevant notifications and prevents discovery, profile access, following and follow back between the accounts. Unblocking does not restore removed connections. Resolve notification identities at read time so hiding, blocking and account deactivation do not leak historical identities.

Reporting creates a private moderation record for authorized Admins; it must not notify the reported Student of the reporter's identity. Provide review status and an audited action to hide a profile or require a public-name change. Keep moderation separate from enrolment or assessment decisions.

## Following, notifications and Feed

- No approval request is required: a follow creates a single directed relationship.
- Button states: Follow, Follow back, Following; show Following each other where useful. Follow back creates the reverse relationship using the same validation rules.
- Following generates a durable in-app event for the recipient: “Nova started following you.” Include a Follow back action when eligible.
- Repeated or concurrent requests must not duplicate relationships or notifications. Unfollow is idempotent. Throttle repeated follow/unfollow cycles and deduplicate notifications to prevent notification spam; define cooldown behavior during implementation.
- Feed initially contains only the current Student's connection notifications, newest first, with pagination and read/unread controls. Unfollowing does not generate a notification.
- Revalidate current relationship state when rendering actions. Stale notifications must not offer a misleading Follow back action.
- Use one notification source for the Feed and top-bar unread count. Avoid loading other Students' private portal data to render either surface.
- Empty copy should explain how to find classmates, without suggesting exam activity is already shared.

## Implementation approach

Both frontend and backend work, including additive database migrations, will be necessary. Preserve existing avatar, authentication, enrolment and assessment behavior.

### Phase 1 — domain and visibility decisions

- [x] Inspect current course/subject enrolment, Student profile, notification and Admin moderation capabilities; reuse appropriate infrastructure.
- [x] Confirm exact eligibility queries for multiple courses, inactive accounts and enrolment changes.
- [x] Finalize public-name validation, collision handling, subject visibility defaults, rate limits and notification cooldown.
- [x] Document the visibility and relationship transitions above as service-level rules.

### Phase 2 — persistence and services

- [x] Add community profile preferences, directed follow relationships, blocks, reports and durable notification/event storage where existing infrastructure cannot serve these needs.
- [x] Add foreign keys, a unique follower/followed pair, self-follow protection, relevant query indexes and transactional consistency. Ensure future broader discovery does not require rebuilding relationships.
- [x] Derive the acting Student from the authenticated session; never accept a client-selected acting Student ID.
- [x] Implement minimal paginated discovery, relationship lists, profile preferences, follow/unfollow, block/unblock, report and own notification read/update APIs.
- [x] Enforce Student role, CSRF on mutations, ownership, bounded search/page sizes, throttling and eligibility on the backend. Protect report-review actions with Admin authorization and audit records.
- [x] Keep notification creation consistent with relationship writes; retries must not produce duplicate events. Define account deletion/deactivation cleanup and report retention.
- [x] Add a focused forward migration; verify existing accounts remain opted out and existing learning data remains unchanged.
- [x] Regenerate OpenAPI and frontend types; add a typed community API module.

### Phase 3 — frontend

- [x] Add public-name and participation settings to the Student profile, with a preview and visibility explanation.
- [x] Add Community navigation and Discover, Following, Followers and Feed tabs using AKURU's compact cards, divided card headers and shared controls.
- [x] Add course selector, public-name search and optional subject filter; reset subject selection when changing courses.
- [x] Show avatar, public name, visible subjects and current relationship action on learner cards.
- [x] Provide follow/back/unfollow feedback, pending states and recovery after failed requests; reconcile all affected lists and unread counts.
- [x] Connect the top-bar notification entry to the same stored notifications as the Feed.
- [x] Add hide, block, unblock and report flows, plus the minimal Admin report-review surface.
- [x] Cover loading, empty, no-course, opted-out, filtered-no-results, unavailable-profile and error states; preserve filters when navigating back.
- [x] Verify keyboard access, accessible status announcements and compact mobile layouts.

### Phase 4 — verification and local review

- [x] Test shared-course discovery with different subjects, multiple courses, subject filters and public-name search.
- [x] Test denial of cross-course discovery/new follows, hidden-subject leakage, nonparticipant access, unauthorized role access and arbitrary target/action manipulation.
- [x] Test follow back across later enrolment changes, duplicate/concurrent requests, self-follow, unfollow and notification cooldown.
- [x] Test hide/re-enable, block/unblock, deactivation and stale notifications across both directions of a relationship.
- [x] Test report confidentiality and Admin-only moderation actions.
- [x] Verify privacy in API responses, list counts, search results, notification previews and avatar fallback; no private identity or learning data is disclosed.
- [x] Verify migration upgrades on a disposable database, API contract parity, relevant backend/frontend suites and production build.
- [x] Update Student/Admin and developer documentation; complete local browser review with representative participating and nonparticipating accounts.
- [ ] Record production acceptance results. Commit and deploy through verified encrypted backup, preflight and production acceptance, as subsequently authorized by the user.

## Acceptance examples

- An iGCSE Student studying Science can find and follow another participating iGCSE Student who studies Mathematics, without requiring a shared subject.
- Selecting Science returns only eligible iGCSE Students whose Science enrolment is visible.
- A Student enrolled only in another course cannot be found or newly followed through iGCSE discovery.
- The recipient receives one notification with Follow back; following back produces mutual status without duplicate relationships.
- An existing connection remains after a course change, subject to participation and blocking rules.
- Hidden, blocked or inactive profiles do not leak through search, relationship lists, notification previews or direct access.
- No marks, exam history, private account identity or messaging capability appears in the first release.

## Future provision

Keep connection storage separate from discovery scope and event types versioned. Later proposals may introduce broader discovery or selected learning milestones, each with explicit audience controls. Completion events must come from authoritative learning services, not arbitrary client claims. Do not implement these future capabilities or expose assessment data in this release.

## Local acceptance — 19 October 2026

- Full release gate passed: 81 frontend tests; 195 backend tests with the PostgreSQL-only race test skipped in the default SQLite fixture; type checks, lint and production build passed.
- Explicit PostgreSQL Community suite: 11 passed, including duplicate follow and follow/block races in disposable schemas.
- Fresh local backup restored successfully. Migration upgrade/schema parity/existing row counts, downgrade and re-upgrade passed in a disposable restored database. Local migration applied successfully.
- Signed-in local browser acceptance used disposable accounts: opt-in/public name, discovery across different subjects, subject filter, follow, recipient top-bar badge and Feed, follow back/mutual state, mark read, private report, block/unblock and Admin hide/name-change review passed. Mobile Feed reported 390px content width at a 390px viewport.
- Implementation detail: courses derive from current progression; one current course is supported by today's data model. Subject choices use visible enrolled subjects in that course plus the viewer's own subjects. Public names use normalized unique case-insensitive keys; mutations allow 30 successful changes/minute; follow notifications deduplicate for 24 hours.
- Guides and developer documentation are updated. Production deployment remains pending its encrypted backup and release acceptance.
