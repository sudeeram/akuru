# Topic 1 — live Tutor development evaluation

Date: 2026-11-01. Owner authorised a maximum US$2 cumulative API budget, using the separate Evaluation project key. Production was not contacted or changed.

## Scope

The accepted-clarification package was imported, reviewed and published in disposable local PostgreSQL schemas with synthetic learner data, then exercised through AKURU's actual Tutor service, learner context, retrieval, quotas, citation validation and OpenAIProvider. Temporary schemas/storage were removed. A budgeted client was injected to restrict credentials and spend; live account-router failover and browser-to-server acceptance were not tested.

Twenty predeclared core questions plus two targeted approximation/privacy cases were reviewed against source evidence. Two full early runs, focused checks and a final core regression produced 66 Tutor turns: 52 paid generations and 14 deterministic evidence-gate replies. This is 22 unique cases, not 66 independent questions. No paid embeddings, image-pixel input or AI graders were used. Teacher model alias: `gpt-6.1-sol`; final prompt version `1.0.2`. The selected alias was not pinned to an independently verified snapshot.

## Findings and changes

- A `next_topic`/`next_unit` schema mismatch prevented normal questions; corrected before paid calls.
- Local hash-vector retrieval missed five valid in-topic requests in the first live run. Added same-topic/version lexical fallback with multi-term support, exact approved-figure matching and rejection of unrelated figures for explicit figure requests.
- Exercise prompts could be selected as if they supported an answer. Generic teaching retrieval now prefers actual teaching evidence and excludes exercise-only prompts unless explicitly requested.
- Short follow-up questions lost their topic context. Retrieval now incorporates the current session's preceding student question for bounded follow-ups.
- Some correct responses omitted source citations, and explanation mode could withhold a requested numerical result. Versioned prompt guidance addresses those behaviours while retaining staged guided practice.
- Revised prompts and retrieval returned the correct source figures and numerical results in the final checks, and respected all four accepted source clarifications.

## Outcome

Codex performed semantic review against the predeclared criteria, with deterministic numerical/citation/asset checks; independent human educator approval was not performed. The final reviewed set had 21 satisfactory outcomes and one partial explanation under its declared rubric. The partial explanation correctly distinguished evaporation temperature/surface behaviour from boiling temperature, but omitted the fuller contrast with boiling throughout the liquid and bubble formation. This was not a numerical/scientific falsehood; the explanation could be more complete. This small, iteratively tuned development set is not a held-out evaluation or proof of student learning gains.

The generic missing-evidence reply remains too broad for personal-history/privacy/scope cases. The reviewed-package confirmation repeats some already accepted clarification notes. Actual Student browser rendering, production configuration, real assessment history, voice, live failover, marking, independent educator review and Topic 2 generalisation remain outside the result. Model text/captions were tested; displaying valid diagram assets is not proof of image understanding.

## Usage and evidence

- Input tokens: 147,479; cached input tokens: 0.
- Output tokens: 9,212, including 784 reasoning tokens (not added again).
- Estimated Standard API cost: **US$0.387078**, using dated model rates of US$2/million input and US$10/million output. This is token-based estimation, not a retrieved billing statement.
- Conservative settled budget accounting: US$0.552981, below the US$2 ceiling. Unknown usage would retain its full pre-request reservation; no unknown-usage calls occurred.
- Only Evaluation credentials were used. No other application key paid for this evaluation.
- Backend regression suite: 270 passed, 1 skipped; dependency warnings only.

Licensed material, raw request/response evidence, readable question-by-question review, usage ledger and cost calculations are under the Git-ignored Topic 1 `ai-prepared-reviewed-v1/teaching-evaluation/` directory. Reusable opt-in runner: `source-code/backend/scripts/evaluate_prepared_tutor.py`. No commit, push, production import or deployment was made.
