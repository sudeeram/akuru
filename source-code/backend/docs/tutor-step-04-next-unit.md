# Tutor Step 4 — Deterministic next-unit recommendations

`POST /api/v1/tutoring/sessions/{sessionRef}/next-unit` answers “What should I improve next?” inside the Student's active tutor subject. The endpoint requires the active subject and a request key. A cross-subject value is rejected, and cumulative Grade and Term coverage is recalculated before ranking.

## Ranking

Algorithm `next-unit-v1` assigns deterministic priority points to every eligible unit:

| Factor | Points |
| --- | ---: |
| Mastery gap | `(10 - mastery score) × 8` |
| Missing mastery with other learner evidence | `12` |
| Low-confidence, provisional, sparse or old evidence | `12` |
| Declining trend | `14` |
| Improving trend | `-4` |
| Assessed mistakes in the last seven days | `4 each`, capped at `24` |
| Additional assessed mistakes in the last thirty days | `2 each`, capped at `8` |
| Approved reviewed recommendations | `8 each`, capped at `16` |
| Planned current study-plan activities | `10 each`, capped at `20` |
| Published current-term assessment blueprint | `5` |

Units sort by descending score, then curriculum sequence, unit code and unit identifier. Every factor returns its points, plain-language explanation and evidence references. The chosen activity prefers a current planned item, followed by a reviewed recommendation, recurring-mistake practice, an evidence-gathering unit check, or a review.

The service returns `no_evidence` when eligible units exist but none has learner evidence. It returns `no_eligible_units` when progression or curriculum coverage does not provide any units.

## Tutor and session boundary

The service calls the Step 3 grounded context operation and returns its context version and operation reference. Tutor turns, profile properties and conversational requests are never ranking inputs. `tutorBrief` allows a later language model to explain the fixed unit and reason, while explicitly forbidding changes to its unit, counts, reason or evidence.

Receiving a recommendation does not modify the session or study plan. The response supplies the existing authenticated unit-switch endpoint as a proposed action, and the Student must explicitly choose that action with a fresh idempotency key.
