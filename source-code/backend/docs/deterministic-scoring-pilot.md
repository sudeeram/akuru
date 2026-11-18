# Biology June 2025 2BR deterministic-scoring rollout

Verified: 2026-11-18. Runtime release: `75ebbc9b5f87df9e1cbaf4193400628589c3b423`. All ten certificates were replayed after this final engine update.

- All 31 subparts inspected and inventoried. Ten bounded-response subparts have current deployed-server certificates covering 135 actual answer cases, with no model calls.
- Four existing legacy/model-validated automatic parts remain identifiable separately: Q1(a), Q1(b), Q2(b), Q3(d)(i). Their history and prior safe releases were preserved. There are 14 automatic/live Tutor parts in total and 17 manual-only parts.
- Precise manual-only reasons were appended to the seventeen affected subparts through Admin APIs, preserving existing human notes.
- All six source-accuracy assessments are current. Human approvals, exact source references, visuals and curriculum mappings were preserved. Q1(b)’s unchanged scheme-over-report decision was explicitly re-recorded after source freshness changed.
- The complete paper and complete automatic assessment remain unready; no formal exam was published. Unsupported explanations/source contradictions were not hidden by higher confidence or keyword rules.
- A normal signed-in Student submitted `0.057` for Q3(b) and saw 2/2 with deterministic provenance. The synthetic acceptance result/transcript remain audited; its test-only mastery projection was rolled back and excluded from future independent evidence.
- The existing Tutor pilot expiry alone was extended to 25 November with explicit user approval; audience, topics, model and tools stayed unchanged.
- Chemistry remains unchanged. The second-paper production demonstration was deferred at the user’s request: finish Biology first.

| Part | Max | Source confidence | Scoring readiness | Current server cases | Tutor release | Remaining route / limitation |
| --- | ---: | ---: | --- | ---: | --- | --- |
| Q1(a) | 2 | 98% | Legacy automatic | — | Live | Open comparison: preserve within-plant versus between-plant meaning; legacy model-validation history retained. |
| Q1(b) | 4 | 98% | Legacy automatic | — | Live | Open biological sequence with source/report discrepancy adjudication; legacy automatic readiness is not a deterministic certificate. |
| Q1(c(i)) | 1 | 98% | Certified automatic | 12 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q1(c(ii)) | 2 | 98% | Manual only | — | Not released | Explain microbial digestion/absorption; semantic relationships and valid paraphrases required. |
| Q1(d) | 2 | 99% | Manual only | — | Not released | Self-incompatibility explanation requires biological meaning, not keywords. |
| Q1(e) | 3 | 70% | Manual only | — | Not released | Open structural adaptation explanation; source extraction estimate also needs separate clarification. |
| Q1(f) | 1 | 99% | Manual only | — | Not released | Reasoned comparison of pollination conditions; valid wording cannot be bounded to a safe finite alias set. |
| Q1(g) | 2 | 99% | Manual only | — | Not released | Meiosis/chromosome pairing explanation; semantic/manual route. |
| Q2(a) | 3 | 98% | Certified automatic | 9 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q2(b) | 3 | 98% | Legacy automatic | — | Live | Related muscle actions and pupil change, including negation/contradiction handling; preserve legacy release, no keyword certification. |
| Q3(a) | 1 | 99% | Certified automatic | 14 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q3(b) | 2 | 98% | Certified automatic | 21 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q3(c) | 2 | 98% | Manual only | — | Not released | Practical reliability reasoning; curriculum confidence/accepted mapping is a separate pending gate. |
| Q3(d(i)) | 2 | 98% | Legacy automatic | — | Live | Open practical modification with alternatives/caps; legacy release retained, deterministic grammar unavailable. |
| Q3(d(ii)) | 3 | 98% | Manual only | — | Not released | Causal transpiration explanation and linked factors require semantic assessment. |
| Q3(e) | 2 | 98% | Manual only | — | Not released | Practical investigation design; curriculum uncertainty and semantic credit remain separate blockers. |
| Q4(a) | 2 | 99% | Manual only | — | Not released | Definition includes ecological scope/variety meaning; finite names matcher would reject valid definitions. |
| Q4(b(i)) | 2 | 98% | Manual only | — | Not released | Unbiased sampling procedure with valid method alternatives requires semantic recognition. |
| Q4(b(ii)) | 3 | 96% | Manual only | — | Not released | Three-mark multistage density/selection calculation: unusual extracted scheme allowance needs source adjudication and safe multi-stage method modelling. |
| Q4(b(iii)) | 1 | 99% | Certified automatic | 14 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q4(b(iv)) | 5 | 88% | Manual only | — | Not released | Extended data discussion; missing converse/variation allowance recorded in source comparison; semantic/capped assessment required. |
| Q5(a) | 2 | 96% | Certified automatic | 11 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q5(b) | 4 | 99% | Manual only | — | Not released | Cloning sequence with any-N/ordered biological steps requires semantic recognition. |
| Q5(c) | 2 | 99% | Manual only | — | Not released | Immunity explanation requires physiological relationships rather than keyword occurrence. |
| Q5(d) | 4 | 88% | Manual only | — | Not released | Data discussion including control/converse allowance recorded as a source issue; semantic assessment required. |
| Q6(a(i)) | 1 | 99% | Certified automatic | 14 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q6(a(ii)) | 1 | 99% | Certified automatic | 13 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q6(a(iii)) | 1 | 99% | Certified automatic | 14 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q6(b(i)) | 2 | 98% | Certified automatic | 13 | Live | Certified bounded recognition; ambiguous inputs refer for review. |
| Q6(b(ii)) | 2 | 99% | Manual only | — | Not released | Protein filtration explanation requires physiological meaning and linked credit. |
| Q6(b(iii)) | 3 | 98% | Manual only | — | Not released | Internal publisher conflict between two-point prose and three-mark maximum requires explicit adjudication; semantic glucose explanation also unsupported. |

## Reproducibility and boundaries

Private licensed source snapshots, synthetic packages and per-part receipts are retained in ignored working storage. Production retains immutable server validation audit records. The generic engine and CLI contain no paper/question IDs. For each new engine version, replay actual inputs against the deployed server; a previous local pass is insufficient.

Single compiled main-question items mixing semantic and deterministic engines remain explicitly unsupported. Prepare separate supported assessment items; do not silently discard certificates. Sibling-only source-issue freshness still uses legacy question-wide hashes, so the developer workflow explicitly rechecks/restores unchanged adjudications and releases. These engineering boundaries remain recorded in the ongoing roadmap.
