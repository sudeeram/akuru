# Subject-specific marking

Step 13 adds versioned subject policies and deterministic checks to the two-pass AKURU assessment service. Deterministic signals and AI decisions are stored separately. A deterministic signal never creates a marking point or awards a mark; only an AI decision tied to an approved official marking point can contribute to the score.

## Engines

| Subject | Checks supplied to the assessment passes |
| --- | --- |
| Maths | Restricted symbolic-equivalence sampling, formula, substitution, working lines, units and rounding signals. Method and accuracy points are decided separately, so correct working can earn an official method mark when the final answer is wrong. |
| Biology, Chemistry, Physics and Human Biology | Terminology, causal links, experiment detail, independent/dependent/control variables, calculation working and conclusions. |
| ICT | Technical vocabulary, scenario references, trade-off language and linked extended reasoning. |
| English | Approved task fulfilment, evidence, organisation and language dimensions. Incomplete dimension coverage or uncertainty routes the result to review. |
| French | Approved comprehension, vocabulary, grammar and communication dimensions. Incomplete dimension coverage or uncertainty routes the result to review. |

The engine name, version and complete deterministic output are preserved in `assessment_results`. They are also returned with the assessment result for troubleshooting, while the portal presents the student with rubric decisions and teaching feedback.

## Handwritten working

The frontend uploads an image or PDF directly to:

`POST /api/v1/assessments/{assessmentId}/questions/{questionId}/working`

FastAPI validates the filename, MIME type, file signature, size, active assessment, student ownership and question membership. The original is stored privately under the configured storage backend. OCR text and confidence are stored in `assessment_working_files` and passed to assessment as a separate transcription. If confidence is below `AKURU_ASSESSMENT_OCR_REVIEW_THRESHOLD`, the result enters `needs_review` and identifies the original image as the review source.

Students and their linked parent can download the original through the authenticated assessment endpoint. Cross-family access returns a generic not-found response. The original is never included in ordinary portal state or placed under the public frontend directory.

## Limitations

The built-in symbolic checker accepts a restricted arithmetic expression grammar and returns unknown for unsupported notation or functions. It is evidence for the Maths policy rather than a computer algebra system. The next Maths-specific corpus evaluation should measure when a reviewed CAS adapter is justified.
