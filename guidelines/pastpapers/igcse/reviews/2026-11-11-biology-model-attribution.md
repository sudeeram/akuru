# Biology model attribution correction

Started/completed: 2026-11-11.

The operator confirmed that all Biology AI-assisted paper work used **GPT-6.1 Sol**, reasoning effort **Light**. Applied this retrospective attribution to existing production AI-assisted analysis records through authenticated, CSRF-protected Admin APIs.

## Scope

- Inspected all **44** active Biology past-paper review workspaces.
- Appended **136** metadata-corrected analysis records across **17** papers: 130 accuracy records for the 16 source-compared papers, plus six extraction records containing Codex-assisted report-identity interpretation for January 2020 2BR.
- The source-compared papers cover June 2025 standard/regional, November 2024 standard, June 2024 standard/regional, November 2023 standard and January 2023 standard/regional.
- The remaining 27 papers have native-only extraction provenance; those records were not relabelled as AI-assisted. Native provenance within updated papers was also preserved.

## Attribution representation

Recorded `modelName` and the operator-supplied model label as **GPT-6.1 Sol**, with `modelIdentitySource=operator_recorded`. This is not provider-response verification or a claim that the display label is a verified API model identifier. No response ID was fabricated.

The current production contract has no structured reasoning-effort field. **Light** is explicitly recorded in provenance notes, together with the confirmation date and the fact that it supersedes earlier missing-identity notes. It is visible in the analysis provenance details. Original processing timestamps were retained; no new source comparison was claimed.

## Preservation and verification

- Used current source/content hashes and optimistic analysis/question versions.
- Read back all 136 appended records and the 17 resulting workspaces.
- Verified question wording, sources, visuals, marks, marking rules, curriculum mappings, human/AI approval states, question revisions and release gates remain unchanged.
- Copied confidence estimates, reasons, inspected source pages and method versions without alteration. Prior analysis records remain in append-only history.
- No question content edits, paid AI calls, migration, application deployment or service restart.
- Ignored local baselines, requests/receipts and verification evidence: `tmp/biology-model-attribution/`. No credentials or licensed source material added to Git.

Updated the provenance guideline to require recording the actual model selection and reasoning-effort label before each subsequent AI-assisted batch. For Codex-assisted work, obtain operator confirmation when runtime model identity is unavailable; never infer the identity from the current chat or inherit a prior batch's model silently. This is a documented processing requirement, not new automatic API enforcement.

Example: [June 2025 Biology 2BR accuracy](https://akuru.magicalinternational.com/admin/exam-documents/review/eea024fe-978f-4392-b330-c0011201cf63/accuracy). The Model column now shows GPT-6.1 Sol; reasoning effort is in the provenance notes.
