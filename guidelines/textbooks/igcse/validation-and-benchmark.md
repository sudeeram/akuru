# Validation, comparison and publication gates

Standard: `akuru-igcse-textbook-screenshots` 1.0.0.

## Source-first preparation

Use the screenshot pages as authority. A previously edited PDF is a comparison document, not guaranteed ground truth: it may contain notation errors, missing figures or changed page references. Freeze the candidate and record prior benchmark exposure. Never claim a formally blinded trial after seeing the benchmark in the same conversation.

## Executed checks

Complete the batch checklist with passed/failed/not run/not applicable outcomes and exact evidence. Check page inventory/hashes, all learning objectives and scope boundaries, every informative figure, every table cell, exercise labels/shared stems, notation, selected arithmetic, cross-page references and working local links. Inspect the assembled human-readable topic and all final crops at readable resolution. Structural checks are necessary but cannot establish full semantic accuracy.

Check that original files remain unchanged and generated content stays ignored. A validator must reject broken references, missing required cells, invented marks/answers, crop bounds outside the original image and accidental benchmark-as-source provenance.

## Comparison methods

- Compare coverage units: objectives, concepts, conditions, practical steps, figures, tables, worked examples, exercises and nested parts. Match by meaning and source reference rather than paragraph or PDF-page count.
- Run explicit numerical and notation probes with references to the original screenshot. Separately report source-first candidate and benchmark results. A missing literal string can indicate alternate formatting or image-only content, not necessarily a semantic failure.
- Record exact probe definitions and code. Report denominators and limitations; do not rename keyword-presence rates as OCR accuracy or comprehension percentages.
- If a fully adjudicated literal transcript exists, word/character error rates can be measured after documenting normalisation. This pilot has no such independent transcript, so it must not report WER/CER or a general model-accuracy percentage.
- Capture discrepancies with source/benchmark/candidate references, adjudication and remaining review needs. A benchmark typo is not a reason to copy the typo into the candidate.
- Include a few source-grounded learning queries to test whether the prepared evidence is sufficient. Distinguish an operator's evidence-sufficiency check from a real AKURU retrieval run, tutor evaluation or student trial.
- Measure actual human review time in a subsequent pilot before promising a percentage time saving. Counting review boxes is not a timing experiment; focused exceptions do not eliminate the need for a full-topic spot check and final approval.

## Release decision

No automatic production replacement. Prepared content remains a proposal. Admin must resolve blocking scientific/notation issues, review the assembled topic and approve it through a supported, audited pathway. Retain publication/versioning, source-role, subject ownership, student eligibility and retrieval gates. Do not mark old pages reviewed or rewrite approved records merely to reduce apparent review counts.

Store source-faithful content and any approved teaching correction separately. Only accepted versions may ground tutoring, flashcards or mock generation. Formal mocks additionally need official specification/past-paper/mark-scheme constraints. OpenClaw gets content only through its future authenticated, scoped AKURU integration; it must not read these local folders or bypass publication.

## Cost and repeatability

Use local OCR for inexpensive proposals, then visually verify difficult regions and scientific relationships. Cache results against source hashes and processing versions. Re-run only changed or disputed regions where possible. An automated provider stage must bound input pages/output, record usage, support safe retries and never silently incur repeated charges. Operator-assisted results here do not establish an automated API model's quality or price.

## Live Tutor acceptance after source preparation

Use a separate evaluation-project key, a declared small request set and an enforced cumulative spend ceiling. Dry-run the real Tutor pipeline before paid calls. Record model alias, prompt version, package/checklist hashes, supplied evidence, API token usage and an estimated cost based on dated pricing. Keep unknown/failed request usage conservatively reserved and disable automatic retries. Do not use production accounts or real-child histories for an extraction pilot.

Test ordinary explanations, misconception correction, multi-turn follow-ups, exact calculations/units, the accepted source clarifications, exact figure matching, compound revision requests, unsupported-topic refusal and privacy/injection boundaries. A safe refusal on in-scope content is a retrieval failure, not a teaching success. A returned citation must support the answer rather than merely contain an unanswered exercise prompt. Check diagram IDs, original pixels and printed-page identity independently of the model's text. Distinguish displaying a source crop from actual model vision input.

Have the operator inspect responses against predeclared criteria and source material; do not rely solely on an AI grader or equate a development-set pass count with global accuracy. Preserve baseline and targeted retest artifacts. Identify partial explanations and generic fallback messages explicitly. Live browser rendering, independent educator review and held-out/new-topic evaluation remain separate checks. See the sanitised [Topic 1 teaching evaluation record](reviews/2026-11-01-chemistry-topic1-teaching-evaluation.md).
