# Admin, Student and Parent profiles

Implemented locally on 19 October 2026, inspired by [PreSkool Profile](https://preskool.dreamstechnologies.com/html/profile.html). The user subsequently authorized committing and deploying all three role profiles to AKURU production.

- [x] `/admin/profile`, `/student/profile`, `/parent/profile` registered with the shared role-aware routing system.
- [x] “My profile” sidebar item and account-avatar shortcut for each role.
- [x] Profile banner with initials, real name, username and role; compact summary cards and divided information cards.
- [x] Admin account details and workspace destinations.
- [x] Student's own grade, term and enrolled courses; no fallback to another learner.
- [x] Parent's linked children and their enrolled courses; empty-family state.
- [x] Existing account-security/password workflow linked from all three profiles.
- [x] No backend, API, database, credential or publication changes. No fictitious profile completeness, security strength, two-factor authentication or inbox counts.
- [x] Typecheck, lint, 75 tests and production build. Model tests check Student/Parent identity isolation and missing-data fallbacks.
- [x] Local signed-in Admin browser check: desktop and 390px phone layout, no page overflow, password-settings destination and avatar navigation.

Populated Student and Parent screens have model tests but still need signed-in visual acceptance with representative local accounts. Photo uploads, contact/address fields and self-service identity editing require separately scoped persistent account support; this initial frontend profile shows the information currently supported by AKURU.
