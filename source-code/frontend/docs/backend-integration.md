# Frontend-to-FastAPI integration status

This inventory records which frontend workflows are backed by implemented FastAPI routes. A visible preview must not submit to a route listed as planned.

## Implemented end to end

| Backend capability | Frontend behavior |
| --- | --- |
| Login, current user, logout and forced password change | Login and password-change screens use authenticated `/api/v1/auth/*` routes. |
| Portal state | All roles restore PostgreSQL-backed state from `/api/v1/state`. |
| Admin UI reference authorization | `/ui-features` verifies Admin access through FastAPI. |
| Parent and Student account creation | Admin Accounts form calls `/api/v1/admin/accounts`; students include parent, progression and subjects. |
| Student configuration update | Admin Accounts form calls `/api/v1/admin/students`. |
| Private document upload | Admin Library sends raw PDF/PNG/JPEG bytes plus supported source metadata. |
| Processing state | Library polls while queued/processing and displays progress and safe failure text. |
| Failed-job retry | Failed documents expose the authenticated retry action. |
| Document removal | Library uses the authenticated soft-delete endpoint after confirmation. |
| Original file access | Admin opens the authenticated private original-file endpoint. |
| Extraction review | Admin sees job stage/version/attempt, rendered pages, blocks, confidence, methods, review flags, LaTeX and private equation/diagram crops. |

The portal state endpoint supplies the document list used by the Admin dashboard. The dedicated document-list/status and specific-job routes remain available for future focused screens; duplicating those requests is unnecessary in the current portal.

## Visible previews awaiting backend roadmap steps

| Frontend area | Required backend step |
| --- | --- |
| Textbook unit correction and publication | Step 6 |
| Grade/term curriculum coverage editing | Step 7 |
| Paper question inventory and marking-source links | Step 8 |
| Question-to-unit approval | Step 9 |
| Student practice, official papers and mocks | Step 11 |
| Marking and Parent review | Steps 12–13 |
| Mastery, recommendations and study plans | Steps 14–16 |

Admin unit, coverage and question forms are disabled and labeled as previews until their write APIs exist. Extraction review currently presents source evidence; editing blocks, review notes and publication remain explicitly assigned to Step 6. Student and Parent data collections remain empty until their later APIs are implemented.
