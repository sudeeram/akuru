# Marking-scheme analysis

Standard: `akuru-igcse-pastpapers` 1.1.0  
Last updated: 2026-10-21

## Match and read the source

MUST match the scheme to the exact subject, session, component and variant. Use table geometry to associate question labels, answer content, notes and maximum marks. Carry merged cells and continued rows across pages without assigning notes to neighbouring subparts.

An evidence link is provenance, not an extracted rubric. Each assessable part needs proposed marking rules as well as its exact scheme evidence before approval.

## Preserve scoring semantics

Capture independently:

- Awardable points, their maximum credit and source codes where supplied.
- Accepted alternatives and equivalent wording.
- Required combinations, dependencies, follow-through and exclusions where explicitly stated.
- Groups such as “any N from”, their score cap and rules preventing duplicate credit.
- ALLOW, ACCEPT, IGNORE and DO NOT ACCEPT instructions, scoped to the correct point or group.
- Multiple-choice correct option and distractor explanations, separately.
- Numerical tolerance, units, significant figures and required working where specified.

Do not add up every listed alternative as though each earns another mark. Distinguish a source label such as `M1` from its semantic point type: do not assume every M-labelled Chemistry point is a mathematical method mark. Preserve the source label and use `other`/review-needed when its meaning is unclear.

For 1C Q2(a), preserve four possible observations in an any-two group capped at two marks, plus the scheme's combined-response and IGNORE/ALLOW rules. For Q2(c)(i), retain all three linked requirements and their alternatives. For Q2(c)(ii), preserve the ion charge and accepted equivalent notation. The Q2 maximum is eight marks.

## Validation and review

Check rubric maximum against each part's marks, rule references, cycles and contradictory instructions. Do not invent dependencies to make arithmetic pass. If the application cannot represent a scoring rule, flag the unsupported rule and block automatic-marking readiness/release until it is supported; content approval may proceed independently. Preserve the original rule for manual review.

Candidate responses from examiner reports must never become accepted answers merely because they appear near examiner commentary. The marking scheme remains the scoring authority; any apparent discrepancy requires review.

## Executable credit allocation (2026-10-21 addition)

Use the existing paper-specified subpart maximum; do not ask reviewers to duplicate that value. A larger list of possible points is valid for an any-N rubric. Preserve each distinct point once, with equivalent accepted responses attached to that point. One response may satisfy multiple distinct points only when supported by the scheme; it must not create duplicate credit for synonyms of one point.

The model proposes point matches with exact supporting student wording. Server code validates the point identities, evidence and permitted credit, then applies per-subpart maxima, optional nested/disjoint group limits, prerequisites and required points for full credit. Store the raw decisions alongside the final allocation. Never trust a model-supplied total or silently drop unsupported scoring instructions.

Q2(a) acceptance example:

- Four possible observations; existing subpart maximum is two marks.
- Effervescence, fizzing and bubbles are alternatives for one observation.
- The scheme's “moves on the surface” response satisfies movement and floating.
- Four matched observations still score two, while repeated synonyms still score one.
- Capped correct points and unused optional alternatives must not be diagnosed as student mistakes or used as negative mastery evidence.

Content approval and automatic-marking readiness are independent. An Admin may approve wording, evidence and coverage while scoring rules remain unchecked or manual-only. Unchecked/manual-only rules block preparation/publication for automatic assessment. Editing the rubric requires readiness to be checked again. The structured v1 engine supports one mark per distinct point and nested/disjoint capped groups. Conditional zero-score exclusions, arbitrary overlapping groups and alternative allocation paths remain manual-only until implemented and evaluated. Preserve their source instructions.

Tests MUST cover correct combined responses, duplicate synonyms, zero credit, all possible points, caps, invalid references, fabricated evidence, stale writes, readiness gates and private rubric access. Exact deterministic aliases apply only to standalone responses; positive substrings inside negated or contradictory sentences are not automatic matches. Other wording is assessed semantically with evidence and confidence checks.

Dependencies interacting with selective groups require manual marking in rule v1; additive dependencies and explicitly allowed follow-through are supported. Do not confirm automatic readiness for a rule combination the validator rejects.

## Diagram model answers

For a drawing/displayed-formula response, preserve exact scheme diagrams as private answer visuals scoped to the subpart and optional marking-point codes. A source page link or OCR transcript alone is not a complete model answer. Keep all essential bonds, labels, axes and annotations; exclude adjacent answers. Propose crops for Admin review and require explicit approval. Never attach a model answer to the question-illustration list. Preserve source version/hash and crop bounds. Show approved answers only through the submitted-attempt authorization path.

For June 2025 1C Q5(c)(ii), preserve separate displayed butane and methylpropane structures, one mark each, with every bond shown. A rotated copy is not a second isomer. Scientific drawing assessment remains manual until a dedicated image-based evaluation passes; do not judge it from OCR text or pixel similarity.
