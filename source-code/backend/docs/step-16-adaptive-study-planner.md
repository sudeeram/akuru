# Adaptive study planner

Step 16 converts approved weakness recommendations and unit mastery into a persistent, reviewable plan for one student.

## Eligibility and priority

The planner starts from the student's assigned subjects and cumulative published Grade + Term coverage. It accepts only approved recommendations whose unit remains inside that scope. Each item therefore retains an approved textbook source and cannot introduce material from another subject, sibling or future term.

Priority increases for a low mastery score, negative recent trend, low confidence, repeated diagnosis and a published assessment blueprint for the student's current Grade + Term. Selection rotates across subjects after ranking each subject's candidates, preventing one subject with many diagnoses from occupying every plan position.

Each selected item stores its duration, reason, unit, activity type, approved source and page, success condition and scheduled date. Spaced retries are scheduled at least three days after plan creation. The other activities are distributed across successive days.

## Versioning and history

`study_plans` stores versioned plan headers and permits one active plan per student. `study_plan_items` stores immutable plan membership plus completion state. Creating a new version supersedes the active header without deleting its items, so completed work remains in history.

An evidence fingerprint contains the approved recommendation identities, recurrence counts and mastery versions. Loading a current plan returns the existing version while that fingerprint is unchanged. New evidence creates a new version on the next plan load. An explicit Student or linked Parent request always creates a new version. A row lock on the student profile serializes concurrent generation.

## Access and API

Students can view and regenerate only their own plan and are the only role allowed to mark an item complete. Parents can view, explicitly regenerate and inspect history only for linked children. Plans and histories are queried by student ID at the database layer, keeping siblings separate.

Endpoints:

- `GET /api/v1/plans/students/{student_id}` returns the current plan and refreshes it only when evidence changed;
- `GET /api/v1/plans/students/{student_id}/history` returns all retained versions;
- `POST /api/v1/plans` explicitly regenerates a student's plan; and
- `POST /api/v1/plans/items/{item_id}/complete` records student completion.

The portal state includes the authorized plan for each visible student. The student Plan screen shows the reason, duration, approved source, success condition and schedule for every activity.
