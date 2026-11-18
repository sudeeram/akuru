# Calculation score bands

Implemented locally: 2026-11-18.

Score bands are private rubric data, stored in the existing JSON scoring rules. No database migration is required. They support mutually exclusive full/partial-credit outcomes; they do not infer a marking scheme from a confidence percentage.

## Representation

Rule version 1 remains supported unchanged. Version 2 adds `scoreBands`. Each band references a separate marking-point code containing its complete evidence criterion, accepted equivalents, units/rounding requirements and exclusions. Its `marks` is a server-owned score, not a model-generated total. Each point belongs to at most one band and each group uses distinct positive scores. Zero is represented by no matching band.

Example for Biology June 2025 2BR Q3(b): first replace the combined marking point with `FULL` (correct 0.057 g per hour to two significant figures, including 5.7 × 10⁻²) and `PARTIAL` (the specific one-mark answers allowed by the original scheme, including 0.0573, 0.05729…, 0.06 or 0.1; exclude 0.572). Preserve original scheme evidence and the two-mark question allocation.

```json
{
  "version": 2,
  "groups": [],
  "combinedResponses": [],
  "scoreBands": [{
    "id": "mass-loss-rate",
    "bands": [
      {"pointId": "FULL", "marks": 2},
      {"pointId": "PARTIAL", "marks": 1}
    ]
  }]
}
```

The model assesses both criteria as binary evidence matches with unchanged criterion text and raw `maxMarks: 1`. Both assessment passes must agree and awarded matches require an exact non-empty phrase in the student's answer. The server then selects the highest matching band, awards only its configured marks, and applies enclosing subpart/question caps. Final decisions contain the weighted maximum/award, while the allocation audit retains raw model decisions, selected bands and credited IDs. Alternative band evidence never adds to a higher band. Standalone synonym matching does not override band decisions, since a numeric string alone cannot establish context or exclusions.

Numerical equivalence and method interpretation remain model evidence-matching responsibilities; this is not an unrestricted symbolic/numeric answer parser. Routine tests use fixtures, not paid model calls. Live scoring validation is still required before claiming that a specific configured rubric marks student answers reliably.

## Admin workflow

1. Read the exact scheme, including continuation pages and partial-credit exclusions.
2. Add distinct full/partial marking criteria in the existing point editor.
3. Under Automatic marking rules → Calculation score bands, associate their codes and marks.
4. Save the rubric. Rule edits clear automatic readiness and invalidate any prior scoring-validation pass. Content/source reassessment may also be required after a rubric change.
5. Run scoring validation with reviewed synthetic examples. Enter the credited code, not a count of marks: `FULL | 0.057`, `PARTIAL | 0.06`, `0 | 0.572`. Add equivalent notation and every applicable partial band as further samples within the eight-sample limit.
6. Validation uses configured band weights when checking zero/full/partial coverage and comparing actual marks. Failed validation does not promote readiness. A pass records its source/rubric hashes and marks automatic readiness.
7. Reassess final source content and follow normal approval/release gates. Neither a band definition nor a unit-test pass authorises production release automatically.

Official full-paper compilation namespaces band and point IDs and preserves per-subpart caps. Tutor practice uses the same frozen rubric and marking allocator.

## Unsupported combinations

Band groups must be disjoint. An enclosing scoring group must contain all alternatives of each band group it touches, have capacity for its highest band, and have no conditional full-credit requirement. Dependencies/follow-through anywhere in a band rubric, and combined-response overrides targeting band points, are rejected for manual review. Negative/zero-valued bands, duplicated codes/scores, unknown points, and scores above the question maximum are rejected. These limits deliberately avoid guessing how complex method-credit or penalty rules should work.

Empty score-band fields are omitted from serialized older rubrics, preserving existing source/rubric fingerprints and immutable snapshots.
