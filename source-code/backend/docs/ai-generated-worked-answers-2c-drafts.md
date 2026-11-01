# Chemistry June 2025 2C qualitative worked-answer drafts

Created: 2026-11-01. Production import/verification evidence is recorded below when completed.

The owner requested AI-generated models for Q2(c), Q2(e) and Q3(c), whose exact schemes describe criteria but provide no drawn official model. Three Codex-prepared, independently reviewable candidates use `science-diagram-v1` and trusted PNG rendering:

| Question / part | Model | Estimated confidence |
| --- | --- | --- |
| Q2(c) | Smooth hydrogen-volume curve from the origin to a horizontal plateau | 97% |
| Q2(e) | Exothermic energy profile, reactant/product labels, upward activation arrow and downward ΔH arrow | 97% |
| Q3(c) | Separate Mg²⁺ / O²⁻ shell diagrams, each with 2,8 electrons and charge outside brackets | 98% |

Confidence is a source-informed AI estimate, not a measured correctness probability. The original question and scheme, their exact evidence and current source fingerprint bind each draft. The generation note identifies Codex conversation assistance without inventing an exact model identity or claiming an OpenAI API call. No production OpenAI credentials are required for importing these externally prepared candidates.

The diagrams, full explanations and limitations were visually checked against the marking criteria before import. Graphs have no invented numerical measurements. Product energy is lower; activation and ΔH arrows have the correct full-level endpoints and are single-headed. Mg loses two electrons; O gains two; both have ten electrons. Dots throughout comply with the scheme's any-combination allowance. Electron arrangements derive from verified atomic numbers and charges.

Drafts remain `awaiting_review`, with no approved asset attachment, question approval or publication. Admin expands the relevant preview in **AI-generated worked answers**, independently checks it and selects **Approve worked answer**. Approval automatically attaches that answer to its matching part. Approving Q2(c) must retain the independently reviewed Q2(e) draft and vice versa; a regression verifies two models on the same question. The required-answer gate remains until approval. Automatic marking of student drawings remains disabled. Existing official answer assets and question illustrations are preserved.

Licensed sources, generated images, detailed payloads and API snapshots remain in ignored local `tmp/` and production storage. Runtime code supports these diagrams in authenticated previews, optional explanation edits, automatic private attachment on approval and normal student reveal rules. No migration was needed.

## Production completion evidence

Imported and verified on 2026-11-01 through the authenticated, CSRF-protected Admin API:

| Part | Draft reference | Status |
| --- | --- | --- |
| Q2(c) | `00254b60-322c-43ac-8063-37059e99e54b` | awaiting_review |
| Q2(e) | `093fd91a-b3a7-4e21-8957-57fe7e2c33d7` | awaiting_review |
| Q3(c) | `5fb84173-3258-4657-b5bf-ddc9a3abb32a` | awaiting_review |

All three production PNG previews were fetched and visually checked. Before/after workspace equality proved that draft creation did not change question revisions, wording, criteria, approvals, release gates or current accuracy/provenance records. No answers were approved by the operator.

Runtime release: `86a122c9942d150b84bbc216e04bd68c53cdac24`, deployed at 2026-11-01 01:44:33 UTC. Evidence: `/data/akuru/release-evidence/deployed-86a122c9942d150b84bbc216e04bd68c53cdac24-20261101T014433Z.txt`. The preceding renderer release was `5234b0a`; the final release also corrects shared workspace-search decoding so numeric direct-entry question links select the intended question rather than falling back to Q1. The hook now consumes TanStack's decoded search state; a regression covers quoted numeric URL serialization and validated context preservation.

Verification: full backend suite 244 passed / one skipped before the final three regressions were added; the final focused graph/science/lifecycle suite passed all 23 tests, including those additional cases. Frontend suite: 108 passed. TypeScript, targeted frontend lint and generated API-contract consistency passed. Existing seven backend dependency warnings remain. Production acceptance passed HTTPS/headers, routes/fallback boundaries, health, timers and loopback bindings. Read-only browser checks confirmed correct Q2/Q3 direct links, all three loaded previews, confidence estimates, enabled approval controls, diagram explanation editing without irrelevant graph controls, unchanged question save state and no page errors. Unrelated local UI/navigation edits were excluded.
