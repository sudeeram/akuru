# Tutor Step 1 — Profiles and curated avatars

Tutor Step 1 gives each Student multiple versioned tutor identities assembled only from controlled AKURU values. It adds no generated-avatar path and makes no OpenAI voice request.

## Stored entities

- `tutor_avatars` contains Admin-published fictional superhuman AKURU BOT presets. Its public string code and frontend asset path are safe to return to users.
- `tutor_voice_presets` contains display choices and an optional backend-only provider reference. The provider reference is excluded from Student, Parent and Admin API responses.
- `tutor_profiles` owns a stable random public reference, Student owner, active state and current version number. Its UUID never leaves the service response.
- `tutor_profile_versions` is immutable. Every edit, including a rename, creates the next version with the complete persona snapshot.

Deleting a profile is a soft deletion. Historical versions remain available for later Tutor sessions and audits. Disabling an avatar or voice prevents new selection while retaining the metadata needed to display an existing profile.

## Curated values

The migration seeds five child-safe AKURU BOT hero choices from the existing `frontend/public/akuru-bots` assets: Atlas, Nova, Spark, Orbit and Byte. It also seeds masculine, feminine and neutral voice-style placeholders. Tutor Step 10 will map reviewed voice choices to provider-specific realtime voices without exposing the mapping to the browser.

The API accepts only:

- presentation: masculine, feminine or neutral;
- tone: calm, encouraging, direct or playful;
- friendliness, enthusiasm and speed: low, medium or high;
- communication character: childlike, balanced or authoritative;
- explanation depth: concise, standard or detailed; and
- teaching style: guided, Socratic, example-led or exam-focused.

Balanced, medium levels, encouraging tone, standard depth and guided teaching form the frontend defaults. Profile names are whitespace-normalized, length-limited and reject markup or URLs. Profiles do not require approval because all visual and persona selections are pre-populated.

## Authorization and APIs

Students manage only their own profiles through `/api/v1/tutoring/profiles`. The authenticated principal supplies the Student identity; no create or update body accepts a student ID. Mutations require CSRF protection.

Parents read profiles through `/api/v1/tutoring/students/{student_id}/profiles`, which verifies the current `student_profiles.parent_id` relationship. A foreign child returns the same not-found response as a missing child. Admin can read a Student's profiles for support but cannot create, edit or impersonate that Student's profile.

`GET /api/v1/tutoring/options` returns curated display metadata and availability without database UUIDs or provider mappings. `GET /api/v1/tutoring/admin/presets` lets Admin inspect all presets. Admin may change availability and ordering through the avatar and voice preset endpoints; every change creates an audit event.

## Frontend

Students receive a **My tutors** workspace with an avatar picker and every controlled persona setting. They can create multiple tutors, rename/edit one by creating a new immutable version, or remove one. Parents receive a read-only **Tutors** workspace for each linked child. Admin receives **Tutor presets**, where curated avatars and voices can be enabled, disabled and reordered.

Internal profile and database UUIDs are never printed. Parent child selectors display names even though the selected account reference is used in the request.

## Verification

PostgreSQL integration tests cover authentication, CSRF, Student-only mutation, multiple immutable versions, sibling isolation, Parent ownership, Admin read-only support access, preset disabling, safe public response fields, name validation and retained versions after soft deletion. Frontend contract tests cover all three role experiences and ensure no generated-avatar or provider-voice control is included.
