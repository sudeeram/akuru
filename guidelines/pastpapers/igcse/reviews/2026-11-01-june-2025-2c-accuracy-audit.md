# June 2025 Chemistry 2C re-analysis and accuracy assessment

Started and source corrections/metadata verified: 2026-11-01.

Standard: `akuru-igcse-pastpapers` 1.3.0; profile: `pearson-edexcel-igcse` 1.1.0. Scope: standard 2C, six questions, 38 subparts, 70 marks. Production paper: `b4fd7a17-e3dd-4403-9799-875e1abb464c`. Regional papers and 1C corrections are outside this batch.

## Sources and method

Production originals were downloaded through authenticated Admin APIs and SHA-256 matched with local originals:

| Source | Pages | SHA-256 |
| --- | --- | --- |
| Question paper | 20 | `24d7789716fa324e17428967b7a215d4ef1179a6002c931a38348cccbcb50bf8` |
| Marking scheme | 12 | `5738e79ef6ad0ce86bcaa4605e5210a80827945951537f6799badb874083e6b7` |
| Examiner report | 76 | `2d8352e677b1e582858490f48e14d0c60a283af991104601496145cead167ba8` |

Compared native text, rendered question pages 4–19 (including the intervening blank page), scheme pages 4–11 and report body pages 4–74 with saved review content. All 12 distinct linked question/official-answer assets were fetched from production and visually compared with full-page originals. Shared apparatus, choice-box names, neutral-atom labels, graph axes/origin, scales, table headers, readings and deliberately blank response areas were checked. The official ester model remains private answer evidence.

Method: `codex_assisted`, provider `OpenAI (Codex conversation)`, guideline 1.3.0, prompt `2c-source-comparison-v1`, assessment method `source-comparison-v1`. The exact current model ID is not exposed in this conversation and was deliberately left **Not recorded**. Original extraction model identity remains unknown. No OpenAI API key or invented model name was used.

## Applied corrections

- Extended report links for 18 subparts across Q2–Q6 to include continuation pages and candidate examples. Retained exact-block links and added checked whole-page links.
- Added derived advice describing the examples, distinguishing candidate errors from official scoring authority. Original handwriting remains visible in the report; a complete literal transcript is not claimed.
- Warned against converting Q3(d)'s overgeneralised report tip into an extra scoring dependency; the official scheme remains authoritative.
- Encoded Q2(d)'s allowed combined phrase as an explicit M3/M4 combined-response rule, preserving the four-mark maximum.
- Captured Q3(e)(i)'s parenthesised optional electron-minus sign; chloride charge, coefficient, product and electron side remain required.

Q1 needed no material correction. Wording, marks, review statuses, coverage decisions, textbook links, visual placements, answer approvals and readiness choices were preserved. Final revisions: Q1 3; Q2 6; Q3 7; Q4 3; Q5 5; Q6 3. All six questions and 38 subparts remain `unreviewed`. Nothing was published or assigned to students.

## Accuracy estimates

| Question | Confidence | Lowest-confidence part |
| --- | --- | --- |
| 1 | 98% | all parts |
| 2 | 93% | e |
| 3 | 92% | d |
| 4 | 95% | c(iv) |
| 5 | 94% | c(ii), d(i) |
| 6 | 93% | c |

Recorded six append-only assessments with all 38 subpart estimates through authenticated, CSRF-protected Admin APIs. Each includes separate paper/scheme/report pages and reasons, provenance, exact source versions/hashes and assessed content hash. The recording tool verified every question's content, revision, approval, reviewer and review timestamp stayed identical to the post-correction baseline. These are subjective source-fidelity estimates, not measured accuracy rates. Automatic-scoring readiness and curriculum coverage remain separate.

## Checklist and remaining gates

| Checks | Outcome | Evidence / limitation |
| --- | --- | --- |
| S01–S02 | Passed | Component/date/hash matches and exact production versions. |
| L01–L03, Q01–Q03 | Passed | Native text and renders checked for reading order, boundaries, options, answer spaces, notation, footer exclusion and all 70 marks. |
| V01–V05 | Passed | All 12 assets compared with full pages; complete labels, blank axes, apparatus, tables and answer-safe placements retained. No replacement needed. |
| M01–M02 | Passed for faithful review capture | Exact points, alternatives, caps, dependencies and follow-through checked. Unsupported conditional allocation stays manual; this is not scoring approval. |
| M03 | Incomplete | Q2(c), Q2(e), Q3(c) need verified private model drawings. Schemes provide criteria but no drawn model; report candidates were not substituted. Q4(c)(iv)'s official ester answer is attached. |
| R01, R03 | Passed | Headings and continuation examples associated; six parts with no located specific commentary remain explicitly identified. Candidate errors are not accepted answers. |
| R02 | Preservation/context passed; literal transcription not run | Report body renders inspected and original handwriting retained. No word-for-word or automated handwriting validation claim. |
| I01–I03 | Passed | Authenticated APIs, expected revisions, pre-write comparison, read-back and separate append-only metadata. No direct database writes or publication. |

Admin must confirm content and coverage before approval. Automatic scientific drawing assessment remains disabled. Conditional marking/manual-only gates remain active. Confidence does not satisfy release gates. Licensed PDFs/images/text, payloads, credentials and detailed snapshots remain in ignored `tmp/` / `pastpapers/` locations and production storage.

## Deployment and acceptance

Release `5860681734667942092bd619cc5ce90e71f36639` deployed on 2026-11-01 at 01:19:59 UTC using the reviewed-release script and its encrypted backup gate. Evidence: `/data/akuru/release-evidence/deployed-5860681734667942092bd619cc5ce90e71f36639-20261101T011959Z.txt`. No new migration was required; production remains at `0017_official_question_analyses`, with no schema drift.

Local verification: 107 frontend tests, 19 focused backend question-review/confidence/provenance tests, TypeScript and targeted lint passed. Seven existing backend dependency deprecation warnings remain. Production HTTPS/security-header, service-health, timer, route-fallback and loopback-binding acceptance passed.

Read-only production browser verification passed for both 1C (10 questions / 49 subparts) and 2C (6 / 38): dedicated route, question/subpart scope filters, model filtering, current confidence values, detailed source/provenance/history, responsive scrolling at 1440px and 390px, and links opening the exact review subpart without enabling Save. The compact question navigation contains no confidence percentages. Authenticated read-back confirmed all 2C content, revisions and approvals unchanged by assessment or browser checks, with every assessment current. An unauthenticated Admin API request returned 401. No browser errors occurred. Unrelated local navigation/style edits from another chat were excluded from this release.

### Follow-up: missing model-answer candidates

On 2026-11-01, the owner requested the three missing worked models. Source-bound AI-generated drafts for Q2(c), Q2(e) and Q3(c) were created and made available for independent Admin review. See [2C worked-answer draft evidence](../../../../source-code/backend/docs/ai-generated-worked-answers-2c-drafts.md). M03 remains a pending approval gate until those candidates are independently approved; draft creation did not change any question content or accuracy assessment.
