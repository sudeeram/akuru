# Original AKURU Student avatar builder

Proposed 19 October 2026 (Asia/Colombo). Design approved and implemented locally after the user requested the working feature. Includes frontend code, authenticated backend persistence and local migration `0011_student_avatar`. The user subsequently authorized committing and deploying the avatar feature, including its nullable database migration.

## Goal and reference

Students create a personal avatar from original AKURU character parts, starting from their existing Student profile. The interaction reference is [Duolingo's avatar creator](https://blog.duolingo.com/avatar-creator/): visual feature selection and immediate preview. Create AKURU's own character silhouettes, facial proportions, expressions, hair, outfits and accessories; do not reuse Duolingo assets or trace its characters.

Confirmed direction: stylised cartoon human characters with playful expressions and simplified proportions, suitable for the iGCSE audience. The user explicitly excluded robot characters and naturalistic humans. Use original AKURU artwork and character construction. Three initial illustration directions have been generated for comparison: A — Soft geometry, B — Expressive curves, C — Bold shapes. The user selected Style A — Soft geometry, with four editable starting characters: two boys and two girls. Every starting character will support hair, glasses, eye colour and the other approved feature options; choices are not locked by the starting character. The refined four-character concept sheet is saved at `../../frontend/docs/design/student-avatars/style-a-four-bases-v2.png`. These are visual concepts, not yet separate interchangeable production layers.

## Student experience

1. Choose **Create my avatar** from `/student/profile` or **Edit avatar** after saving one.
2. Open a focused editor with a large live preview and labelled categories: face/skin tone, hair, eyes/brows, expression, clothing, accessories and background.
3. Select thumbnail options and colour swatches. All options work without gender selection. Include diverse hair textures, skin tones and appropriate headwear; distinguish colour choices with names, not colour alone.
4. **Surprise me** creates a starting combination from the approved AKURU parts. Students can keep customising it before saving. **Reset draft** returns to the current saved avatar.
5. **Save avatar** persists the selected configuration and refreshes the profile banner and top-bar `.ak-account`. Cancel leaves the saved avatar unchanged. A failed save keeps the draft and shows a retry action.
6. Students can return later to edit or remove their avatar and restore their initials.

## Original visual system

- Friendly illustrated portraits appropriate for the current iGCSE audience: expressive but not preschool-like.
- A distinct AKURU visual vocabulary: its own face/head shapes, eyes, brows and hair silhouettes, with blue/purple accents and a broader clothing/background palette.
- Author modular vector artwork directly as versioned SVG/React components. Keep parts aligned to one canvas so every supported combination renders coherently.
- Design for both the large profile portrait and a readable 32–40px top-bar avatar, with a consistent head-and-shoulders crop and safe margins.
- Start with a focused catalogue, such as 3 face shapes, 8 skin tones, 10 hairstyles, 6 hair colours, 4 eye/brow choices, 5 expressions, 6 outfits, 4 glasses/accessory options and 8 backgrounds. These are proposed art-production targets, not existing assets or a promise that every option multiplies independently.
- Keep version 1 part IDs stable after release. New catalogue versions must retain a compatible renderer for previously saved avatars.

## Generation approach

Use a modular character builder with constrained randomisation for the first release. This provides immediate previews, consistent artwork and predictable edits without per-avatar image-generation calls. No photos, selfies, free-text prompts or external avatar service are needed for the MVP.

AI could later help develop visual concept sheets or a separately scoped prompt-to-avatar experience. It is not required for generating a random avatar from the original AKURU parts. A future AI mode would need its own cost, privacy, review and storage design.

## Integration with AKURU

### Frontend

- Add a shared `StudentAvatar` renderer with an initials fallback, responsive sizing and appropriate accessible names/decorative treatment.
- Add an editor launched from the existing Student profile. Reuse AKURU's dialog/drawer, button and feedback components.
- Show the saved avatar in the Student profile, `.ak-account`, existing learner identity elements and the Parent's authorized family-profile cards.
- Keep the Student avatar separate from Tutor profile avatars and AKURU loading mascots.
- Preserve draft/leave protection, keyboard focus and save-in-progress behavior. Do not send an avatar configuration through URL parameters.

### Backend and persistence — implemented locally

The formerly frontend-only profile now uses a small backend extension to save avatar configuration. The nullable migration preserves initials for existing accounts.

- Store a nullable, versioned avatar configuration on the Student profile, introduced by a forward migration. Null preserves the existing initials behavior for every current learner.
- Store approved part identifiers and palette tokens rather than user-supplied SVG markup, image URLs or arbitrary image uploads.
- Implemented endpoints: Student-only read/update/reset through `GET/PATCH/DELETE /api/v1/student/avatar`. Saves derive the Student from the authenticated session and accept no target Student ID.
- Derive the Student identity from the signed-in principal; do not accept a client-selected Student ID for saves. Use existing CSRF, authentication, transaction and error conventions.
- Validate schema version, allowed fields, catalogue part IDs, colours and valid combinations on the server. Reject unknown fields and unsupported versions.
- Include the validated configuration in the existing authorized portal response for the Student and linked Parent/Admin views. This must not broaden which learners an account can access.
- Reset removes only the avatar preference. Passwords, roles, enrolments and learning/assessment data are unaffected.

## Delivery steps

- [x] Confirm cartoon-human direction; exclude robots and naturalistic humans.
- [x] Produce an initial concept sheet with three style directions and three sample identities per direction.
- [x] Select Style A — Soft geometry.
- [x] Generate a refined front-facing concept sheet with four starting characters, two boys and two girls.
- [x] User approved the revised four bases. Created separate original vector face, hair, eye, brow, expression, clothing, glasses and backdrop layers. The PNG remains a concept reference; the live editor uses vector adaptations.
- [x] Build the finite version-1 catalogue and local editor with live preview, all four presets, category controls, Surprise me, reset draft and save/remove actions.
- [x] Add validated persistence, audit events, existing portal-state integration and nullable migration. Applied locally after backup and a successful isolated restore drill.
- [x] Connect Student profile, top-bar account avatar and authorized Parent family-profile cards, with initials fallback for missing/unsupported configuration.
- [x] Test Student isolation, authorization/CSRF, schema/catalogue validation, save/reset across independent DB sessions, every supported feature with each base, random combinations, SVG ID isolation and unsupported-version fallback.
- [x] Browser-check populated Admin design preview, Base 04 selection, green eyes, glasses, save/reopen and phone live-preview/overflow behavior.
- [ ] Complete signed-in Student/Parent browser acceptance with representative local accounts, including failed-save recovery, keyboard focus/dirty-close behavior and two-device synchronization.
- [x] Typecheck, lint, 79 frontend tests, 183 backend tests, generated API contract check, production build and local Alembic consistency check pass.
- [ ] Authorized production release: verify encrypted backups, apply the additive migration, deploy the editor/API and run production acceptance.

## Initial release boundary

Student creation/editing only. All approved customisation options are available immediately. Photo uploads, paid/random unlocks, achievement economies, public avatar galleries, animation and AI prompt-generated images are separate future possibilities. The builder must not claim cross-device saving until backend persistence has been implemented and verified.


## Local implementation notes

- Frontend vector artwork: `components/portal/student-avatar.tsx`; editor: `features/student-avatar-editor.tsx`.
- Student entry: `/student/profile` → **Create my avatar** / **Edit avatar**.
- Admin design review: `/ui-features` → **Try the avatar builder**. Clearly labelled as a preview; it saves only preview component state and does not edit an account.
- Each base has a different face shape. Base 04 uses the approved fuller-cheek direction. All approved options remain selectable for every base.
- The renderer uses only bundled paths and validated palette tokens; no uploaded SVG, arbitrary URLs, prompts, selfies or external AI calls.
- Backend and frontend catalogue copies have an automated parity test. Keep version-1 IDs stable; introduce a compatible renderer before accepting any new catalogue version.
- The local migration adds one nullable JSON column to `student_profiles`; no production changes were made. Backup restore passed at the previous revision, then local upgrade and Alembic check passed at `0011_student_avatar`.
- Changes to avatar configuration are included in the existing role-scoped portal response. A save refreshes the current profile/top bar; another device receives it on its next state fetch/reload. There is no live push synchronization.
