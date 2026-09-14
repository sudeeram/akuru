# First frontend version

A local-first family learning portal with parent and three child accounts. Shared demonstration question library, separate student attempts, assignments and reviews, and four subjects across sample courses. All educational examples are original demo content, not official Pearson material.

## Included journeys
- Local login and logout, server-enforced role and student ownership checks.
- Student overview, subjects, visual lessons, practice, progressive hints, typed answers and image upload, timed mock attempts, printable papers, progress and revision plan.
- Parent overview and child detail, course enrolments, local document upload and manual import review, assessment review with correction, assignments.
- Persist local data and uploads outside source control. Deterministic demo checking with clear review-required handling for free text and handwriting.
- Responsive keyboard-accessible UI; local browser and API tests.

## Integration boundaries

The statements above describe the historical local frontend prototype. The current portal uses the FastAPI/PostgreSQL API. OpenAI credentials and provider calls remain exclusively in the backend; the browser can request workflows but never receives a key. Current visual support includes deterministic SVG/plots and Admin-reviewed conceptual images. Video remains an optional future service.
# Historical scope — superseded

This document describes the original demo. Current roles, folders and curriculum constraints are defined in [architecture.md](architecture.md) and [frontend architecture](../frontend/docs/architecture.md). Parent-managed courses/uploads and the combined Science demo no longer define current behavior.
