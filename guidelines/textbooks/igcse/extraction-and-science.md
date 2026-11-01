# Extraction and scientific fidelity

Standard: `akuru-igcse-textbook-screenshots` 1.0.0.

## Source inventory and layout

- Preserve original bytes, filenames, SHA-256, dimensions, page order and visible printed-page labels. Verify labels against the pixels; filenames are only proposals. Distinguish printed page, source-image sequence and derived PDF page.
- Record qualification, subject, textbook/group/topic identity and edition only from evidence or identified owner input. Missing title/edition/specification references remain unknown. A unit's contents list does not mean its later topics have been supplied.
- Inspect full pages before interpreting fragments. Separate headings, main text, sidebars, key points, safety notes, figures, captions, tables and exercises. Preserve continuation across pages and distinguish optional/extension/subject-only material.
- OCR is a proposal, not the source of truth. Preserve raw text and geometry. A vision check must inspect the actual source, not merely rephrase OCR output. Mark uncertain spans explicitly rather than filling them from general knowledge.
- Detect reading regions before joining lines. Do not assume every narrow sidebar is a main text column. Region ordering must survive all later sorts and merges. Never merge a caption, table, answer space, formula or sidebar into unrelated prose.
- Parse Tesseract TSV as literal tab-separated fields, not quoted CSV text. Detect embedded TSV row artefacts, malformed fields, dropped lines and implausible block sizes. This is a required outcome; the current AKURU implementation still needs the corresponding fix.
- Enlargement can improve recognition but cannot restore absent pixels. Measure its effect; do not describe upscaling as added source detail. Ask for a better source only for the specific unreadable page/region.

## Teaching content

- Capture all learning objectives, definitions, important explanations, conditions/exceptions, worked examples, practical steps, safety context and exercise dependencies. Do not replace the topic with flashcard-style bullet summaries.
- Faithful paraphrase is allowed if explicitly identified. Exact transcription is preferred for definitions where wording matters, formulas, numbers, question prompts, labels and procedural constraints. Never claim a paraphrase is a literal transcript.
- Preserve chemistry-only and extension boundaries. Do not promote explicitly optional extension content into required exam scope. Bind safety warnings to their demonstrations; explanatory treatment is not an invitation to perform the experiment at home.
- Keep source content, editorial corrections, AI explanations and AI-generated solutions separate. A clear source typo may justify a proposed correction, but retain the original reading and evidence and request approval. Do not silently repair a scientific inconsistency.
- Review statements that could become false universal rules when removed from context, such as phase-only kinetic-energy rankings or requiring visible excess solid in every saturated solution. Preserve source provenance and flag the teaching interpretation.

## Notation and numerical validation

- Preserve case, signs, decimal places, units, sub/superscripts, charges, state symbols and reaction arrows. Distinguish `Cl` from `CI`, `g` from `9`, `cm³` from `cm`, and negative temperatures from positive ones.
- Store a legible scientific form plus a plain-text or structured equivalent. Normalising a visible subscript to Unicode/LaTeX is not permission to change the compound. Do not infer formulas from an uncertain glyph without recording the inference and review need.
- Keep exact table strings, including trailing zeros; use decimal arithmetic for checks. Preserve intentional blank cells as null with an explanation, not zero or an invented value.
- Validate worked arithmetic and equation atom balance where feasible. Separate quoted values from computed values and approximate graph readings. Never invent curve coordinates, measurement precision or mark tolerances.
- Long decimal strings and particle counts require focused verification; a plausibility check is useful but not proof of literal extraction accuracy.
