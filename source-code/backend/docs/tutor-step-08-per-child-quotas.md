# Tutor Step 8: per-child AI quotas

AKURU applies tutoring allowances to individual student accounts. These limits are independent of family assessment limits and OpenAI provider-account budgets.

## Data model

`student_ai_quotas` stores one current policy per child: accounting-period length and anchor, request allowance, text-token allowance, voice-second allowance, enabled state, and the last administrator who changed it. Existing students receive the initial 30-day allowance during migration; newly created students receive it with their account.

`student_ai_usage` is an append-only accounting ledger. Each row identifies the student, logical operation, dimension, event type and signed quantity. Its uniqueness constraint makes reserve, settle and release operations idempotent for retries.

## Accounting

Before a Tutor Agent provider call, the service takes a PostgreSQL transaction advisory lock scoped to the student. It checks the active period and atomically reserves one request plus estimated text tokens. A successful call settles the estimate to the provider's actual token count. A failed provider operation releases both reservations. OpenAI account failover occurs inside this one logical operation, so changing accounts cannot create another student charge.

Voice uses the same reservation pattern in seconds and is available for the voice implementation. If voice time is exhausted while text remains, the API directs the student to continue by text.

## API and authorization

- `GET /api/v1/tutoring/quota` gives a student only their own understandable remaining allowance.
- `GET /api/v1/tutoring/admin/quotas` gives Admin a per-child overview.
- `POST /api/v1/tutoring/admin/quotas/{student_ref}` changes a policy and requires a reason plus CSRF protection.
- `GET /api/v1/tutoring/admin/quotas/{student_ref}/audit` returns the policy-change history.

The API uses opaque student references for quota administration. Responses contain no provider aliases, credentials, provider budgets, or internal UUID fields.

States are `available`, `warning` at 20% remaining, `exhausted`, and `disabled`. Period boundaries are calculated from the configured anchor and duration, so usage renews automatically without deleting historical ledger rows.
