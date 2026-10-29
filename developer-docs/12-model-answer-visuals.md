# Model-answer visuals and drawn submissions

Implemented: 2026-10-29. This extends official-paper review; question illustrations and private answers have different access paths.

## Data and versioning

`ReviewPart` stores `responseType`, `answerVisualRequired` and `answerVisuals`. Each association contains the immutable asset ID, subpart label, local marking-point codes, caption, accessible description and proposed/approved/rejected state. Dedicated crops belong to the workspace's exact scheme `DocumentVersion`; metadata records source SHA-256, creator, normalized bounds and crop SHA-256. Saving a review records the decision using the existing revision/audit workflow. Crop retry reuses identical source/page/bounds/description.

Migration `0014_answer_visuals` adds private JSON manifests to `mark_scheme_entry_versions`. Official draft preparation copies approved associations only. Publication checks the approved workspace, and assessment creation snapshots the manifest into `AssessmentQuestion.rubric`. Replacing a crop creates a new immutable asset; old attempts retain their frozen answers.

Migration `0015_drawing_submissions` adds `AssessmentAnswer.drawing_files`, a map from subpart to private working-file ID. Replacement changes the active answer map, preserving the old file and incrementing the answer revision. Normal typed-answer saves preserve this map. Uploads and submissions serialize on the assessment lock and recheck the deadline after extraction. Originals are retained; OCR is not authoritative for drawings.

## APIs and authorization

- Admin crop POST: `/api/v1/admin/official-paper-reviews/{paper}/visual-crops`, with `source: "scheme"`; existing `source: "paper"` behavior remains the default.
- Admin review saves retain the expected-revision check and explicit model-answer approval. A scheme crop cannot be assigned as a question visual.
- Student drawing upload: `/api/v1/assessments/{assessment}/questions/{question}/drawings/{part_label}`. Existing size/type/malware/storage-quota checks apply. File ownership, question and allowed drawing part are checked server-side.
- Student answer image: `/api/v1/assessments/{assessment}/questions/{question}/answer-visuals/{asset}`. Requires the Student's submitted assessment and a frozen approved association. Expiry without submission is insufficient. Responses are private/no-store; no public object-storage URLs.
- Generic document-asset endpoints remain Admin-only. Admin human review can open original Student drawings through existing scoped working-file endpoints.

The current assessment policy reveals model answers after submission, independently of whether the Student's marks still need human review. This also applies to formal papers; there is no newly invented separate exam-results scheduling policy.

## Marking and release policy

A drawing response requires an approved model-answer visual and `manual_only` readiness. Other text parts retain their existing readiness requirements. A released question containing a drawing is held for human review as a whole; it is not assigned a partial automatic score. The placeholder DB mark is never presented as the Student's score, and no mastery/weakness event is produced before human approval.

Optional `AKURU_ASSESSMENT_DRAWING_SUGGESTIONS_ENABLED=true` sends bounded original images and approved model-answer images through the existing assessment provider. Output is validated against exact points and score caps. Every proposal remains `needs_review`; provider/render failures fall back to manual review. The default is false and production should retain it until the evaluation matrix is reviewed. See `source-code/backend/evaluations/drawings/README.md`. Automatic scientific drawing grading is not enabled by this release.

## UI and testing

Admin: response format, required visual, scheme-page crop editor, marking-point links, descriptions and approval decisions. Student: per-part file upload/replacement/preview, responsive approved answer diagrams and enlarge action in practice/results/tutor practice. Existing role/user cache clearing remains in force.

`tests/test_answer_visuals.py` covers source validation, replay, approval gates, direct image denial, cross-question/sibling isolation, upload-replace-submit flow and pending results. Tests use synthetic images rather than licensed scheme content. Full backend and frontend checks are required before deployment.

Rollback: the two migrations are additive. Roll back application code while retaining columns and assets; do not drop columns after real drawing submissions have been saved. Backups and the standard reviewed-release deployment script remain mandatory.
