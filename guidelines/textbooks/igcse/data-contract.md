# Logical textbook preparation contract

Standard: `akuru-igcse-textbook-screenshots` 1.0.0. Package format: `akuru-textbook-preparation-v1`.

This logical preparation contract is transported by the dedicated Admin prepared-package ZIP importer. Do not POST the JSON to an ordinary PDF upload endpoint or write directly to production tables. The portable ZIP must include validated source PNGs and original-pixel figure crops; see the backend import guide. All imports remain unapproved supporting drafts.

| Collection | Required information |
| --- | --- |
| Identity | Course, subject, group/topic references, actual title/edition or unknown, identity evidence. |
| Provenance | Method, guideline/format versions, operator/processing date, provider and exact model if exposed, raw OCR role, benchmark-use declaration. Unknown model IDs must remain unknown. |
| Pages | Stable page IDs, source path/hash, dimensions, verified printed label, source sequence. |
| Objectives | Stable IDs, source text/treatment, printed page, core/chemistry-only/extension scope. |
| Blocks | Stable IDs, page evidence, kind/title/content, original or paraphrased treatment, notation/table structure, objective/figure/safety/issue links, draft status. |
| Figures | Stable figure ID, original source region, pixel coordinate system/bounds, crop path/hash, caption and treatment, accessible description, relevance and candidate status. |
| Exercises | Complete question/nested part labels, shared context, prompts, word banks, required table/figure links, printed skill/badge evidence, separately inferred task demand. Missing source marks/answers are null. |
| Review issues | Exact affected blocks/pages, severity, original reading, proposed correction/interpretation, reason and action. |
| Release gates | Admin approval/publication false by default; explicit specification-alignment, difficulty-calibration and import-support status. |

Retain full source/OCR evidence separately from clean teaching text. Derived fields must state their origin. Do not use a made-up confidence percentage as approval; recorded OCR certainty, source-fidelity estimates and scientific interpretation concerns are different measurements.

A source-first freeze records the prepared package checksum before the separate comparison stage. Post-benchmark corrections must create a new revision or a transparent delta, not silently replace the candidate and report its improved results as the original trial. This pilot is not formally blinded because the conversation previously inspected v2.2; later independent evaluations should use separate source-only processing contexts.

Licensed pages, crops, prepared content, benchmark text, detailed payloads and full local reports remain under ignored `textbooks/` or `tmp/`. Git holds generic rules/tools, synthetic tests and sanitised batch outcomes only. Keep live credentials, student identities and model secrets out of all preparation files.
