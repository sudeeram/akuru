# 03 — AKURU integration APIs and Telegram identity

**Status:** Planned
**Depends on:** AKURU's existing published-topic, enrolment and source-authorization services. Docker/OpenClaw installation can be completed first; do not connect its Gateway to these APIs until their security gate passes.

Build the restricted AKURU boundary before OpenClaw receives any Student or source data.

## Telegram account linking

- [ ] Add a Student–Telegram link model containing numeric Telegram user ID, private chat ID, status, timestamps and audit evidence; enforce one active Telegram identity per Student and vice versa.
- [ ] Let a signed-in Student create a short-lived, single-use pairing code or deep link; exchange it only through an authenticated integration endpoint receiving trusted Telegram sender context.
- [ ] Give Students, linked Parents and Admins link-status visibility and revocation; revocation immediately rejects future integration calls.
- [ ] Reject groups, forums, usernames, display names and model-provided Student identifiers as identity sources.
- [ ] Add pairing attempt limits, expiry, replay protection and link/revoke audit events without logging the pairing secret.

## Restricted service authentication and reads

- [ ] Issue a separately revocable integration credential with only Quick Mock identity/source scopes. Keep it outside Git, model prompts and normal AKURU user sessions.
- [ ] Resolve the linked Student on every call from authenticated Telegram runtime identity; recheck active account, course, subject, grade/term progression and publication/coverage rules.
- [ ] Add bounded, typed `get_my_profile`, `get_my_enrolments`, `get_my_covered_topics` and `get_my_mock_options` responses.
- [ ] Add bounded generation-context and marking-context endpoints returning only approved eligible topic/past-paper evidence, mark constraints and exact source references.
- [ ] Set limits for question count, source count, response size and page text. Block cross-subject retrieval and bulk export.
- [ ] Expose no arbitrary document download, raw object key, database ID, AKURU write API or unrelated family data.
- [ ] Log safe invocation metadata and authorization failures without retaining the temporary paper, answers or marks in AKURU.

## Verification gate

- [ ] Test pairing, expiry, replay, revocation, CSRF and service-token scope.
- [ ] Test Laura/Enya isolation, concurrent calls, forged sender details, cross-subject and uncovered-topic requests.
- [ ] Test that a revoked link or disabled Student account fails closed while normal AKURU web access is unaffected.
- [ ] Review OpenAPI contracts and document exactly which tool parameters come from trusted runtime context rather than the model.

**Done when:** AKURU can answer the minimal read-only Quick Mock queries for a linked Student and reject all unlinked, out-of-scope and cross-child requests without exposing its general database or document store.
