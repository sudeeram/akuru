# Step 18 — Diagrams and optional media

AKURU treats visual media as supporting explanation. Every stored visual links to one active retrieval chunk from a published textbook/reference in the same subject and unit. The learner view always presents that citation and never substitutes the visual for official question, rubric, or textbook evidence.

## Deterministic visuals

`POST /api/v1/media/admin/deterministic` creates SVG using validated numeric parameters. Supported kinds are `circuit_svg`, `forces_svg`, `geometry_svg`, and `plot_svg`. Values are bounded, triangle angles are checked, plots accept 2–30 points, and all text is escaped. The SVG includes `<title>` and `<desc>`. Because code controls the complete output, it can publish immediately with provider/model `akuru/akuru-svg-v1`. The original parameters, generator version, checksum, source manifest, and private object key remain in PostgreSQL/private storage.

## Conceptual illustrations

`POST /api/v1/media/admin/illustrations` sends an Admin request plus one approved source excerpt to OpenAI Images. It uses `AKURU_OPENAI_IMAGE_MODEL` and `AKURU_OPENAI_IMAGE_SIZE`; credentials are selected by the Step 5A priority router and never enter the prompt or browser. Requests prohibit marks, answers, unsupported labels, logos, and copyrighted characters. Provider failover restarts the whole image request.

The PNG is private and its record starts as `pending_review`. Only an Admin can retrieve it at this stage. `POST /api/v1/media/admin/{id}/review` records `published` or `rejected`, reviewer, notes, time, and an audit event. Learner APIs redact the prompt, parameters, model, response ID, and review notes. Published content still requires authenticated student/family scope, subject enrolment, and cumulative unit coverage.

## Storage and delivery

Assets use the configured local or OCI `ObjectStorage` backend under `media/{subject}/{uuid}`. Downloads send private/no-store caching, nosniff, and a restrictive content security policy. Database rows store SHA-256, content type, source/document/unit/version identifiers, source content hash, prompt/generator version, provider/model, and review state.

## Video boundary

Video remains optional and is not generated in Phase 1. A later implementation must take only an approved explanation through `storyboard → narration → video → Admin review → publication`, store each stage and its provenance privately, and use the same learner authorization. Nothing in Step 18 requires a video dependency or service.

## Endpoints

- `GET /api/v1/media/admin/sources?subjectId=...` lists safe labels for approved source selection.
- `GET /api/v1/media` gives Admins the review inventory, or learners only published eligible items with `studentId` and `subjectId`.
- `GET /api/v1/media/{id}/content` serves private bytes after role/scope checks.

Migration `c72d8e4f19a1` creates `educational_media`. Tests cover SVG escaping and parameter validation, OpenAI PNG decoding, same-subject source enforcement, Admin-only creation/review, pre-publication denial, student/parent isolation, learner metadata redaction, audit events, storage delivery, contracts, types, lint, build, and migration drift.
