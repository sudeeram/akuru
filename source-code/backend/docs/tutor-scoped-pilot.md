# Multiple student/topic grants in a controlled text tutor release

The existing `AKURU_TUTOR_TEXT_PILOT` JSON remains backward compatible. Its original student, subject, topic and published content-version fields are the first grant. Optional `additional_scopes` supplies up to 500 further explicit grants, each containing:

- `student_id`
- `subject_id`
- `topic_id`
- `topic_content_version_id`
- `evidence_sha256`

There are no wildcard student or topic grants. Duplicate student/subject/topic tuples are rejected. All grants share the parent pilot's approved model, prompt versions, feature restrictions and timezone-aware expiry. Each request validates its own grant's published content version; superseding one topic closes that grant until revalidated. Existing single-grant deployments need no configuration change.

Session topic choices are the intersection of the current student's explicit grants and their published cumulative curriculum coverage. Granting a topic alone does not bypass enrolment or coverage. Formal assessments still block assistance; voice and assessed guided practice remain outside this text pilot. Account routing remains pinned to the approved model.

For Biology rollout, preserve the existing Chemistry grant and add exact entries for the two authorised students and the 22 published Biology topic versions. Keep configuration credentials on the server only; put non-secret evidence and test results under the ignored release-evidence directory. Back up the environment before replacing it and validate the staged configuration before restarting the API.

The pilot expiry is still enforced. This is a scoped controlled release, not a permanent unrestricted subject-wide release. Textbook retrieval preflights do not substitute for checking live teaching quality.

## Biology teaching boundaries and retrieval

Supplementary policy v1.1 has explicit school-level concept lists for the 22 reviewed Biology topic titles. Related explanations remain labelled as additional material and cannot invent page numbers, figures or Pearson marking claims. Topic access is still determined by the exact grant and coverage checks above. Personal treatment and dosing requests are declined; the rules permit textbook explanations of hormones and vaccination.

Retrieval normalises bounded Biology word variants (for example, respiring/respiration and photosynthesising/photosynthesis) before lexical ranking. This fixes a live case where a green-leaf starch passage outranked the published respiration explanation. The existing published-topic/version filters, approval requirements and exclusion of exercise prompts from answer evidence remain intact. These ranking scores are not accuracy probabilities.
